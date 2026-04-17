"""Orquestador de tool calling entre Ollama e IFCTools.

ToolRunner:
  - mantiene el contexto del archivo IFC y del elemento seleccionado
  - construye el system prompt (versión compacta: una línea por selección)
  - añade 'obtener_seleccion' a las herramientas cuando hay selección activa
  - ejecuta el bucle de tool calling (Ollama → herramientas → Ollama…)
  - entrega los tokens finales vía callback
"""

from collections import defaultdict

import ollama as _ollama

_SYSTEM_BASE = (
    "Eres un asistente experto en BIM e IFC. "
    "Responde de forma concisa y en el mismo idioma en que te hagan la pregunta."
)

_MAX_ITERACIONES = 5   # rondas máximas de tool calling por consulta
_BUFFER_TOKENS   = 8   # tokens agrupados antes de entregar al callback


class ToolRunner:
    def __init__(self, ollama_client, ifc_tools=None):
        self._client    = ollama_client
        self._ifc_tools = ifc_tools
        self.contexto_archivo   = ""
        self.contexto_seleccion = ""   # una línea: "Elemento seleccionado: X (IfcY)"
        self._elementos = []           # objetos IFC seleccionados (raw)
        self._props     = []           # grupos de propiedades (merged)

    # ------------------------------------------------------------------
    # API de contexto
    # ------------------------------------------------------------------
    def set_archivo(self, nombre: str, total: int):
        self.contexto_archivo = (
            f"Archivo IFC abierto: {nombre} ({total} elementos cargados)."
        )

    def set_seleccion(self, elementos: list, props: list):
        """Guarda la selección actual y actualiza el contexto pasivo (una línea)."""
        self._elementos = elementos
        self._props     = props

        if not elementos:
            self.contexto_seleccion = ""
            return

        if len(elementos) == 1:
            info   = elementos[0].get_info()
            nombre = info.get("Name") or elementos[0].is_a()
            tipo   = elementos[0].is_a()
            self.contexto_seleccion = f"Elemento seleccionado: {nombre} ({tipo})"
        else:
            self.contexto_seleccion = f"Elementos seleccionados: {len(elementos)}"

    # ------------------------------------------------------------------
    # Chat principal
    # ------------------------------------------------------------------
    def chat(self, prompt: str, on_token, on_tool_call=None, should_stop=None):
        """Ejecuta una consulta completa con soporte de tool calling.

        prompt       — texto del usuario
        on_token     — callable(str) llamado con cada fragmento de texto
        on_tool_call — callable(nombre, args) al invocar una herramienta
        should_stop  — callable() que devuelve True para cancelar
        """
        tools = self._tools_disponibles()
        messages = [
            {"role": "system", "content": self._build_system(bool(tools))},
            {"role": "user",   "content": prompt},
        ]

        # ---- Bucle de tool calling (llamadas no-streaming) ----
        if tools:
            for _ in range(_MAX_ITERACIONES):
                if should_stop and should_stop():
                    return

                response = _ollama.chat(
                    model=self._client.model,
                    messages=messages,
                    tools=tools,
                )

                tool_calls = getattr(response.message, "tool_calls", None) or []

                if not tool_calls:
                    content = (response.message.content or "").strip()
                    if content:
                        on_token(content)
                    return

                messages.append(response.message)

                for tc in tool_calls:
                    if should_stop and should_stop():
                        return
                    nombre    = tc.function.name
                    args      = tc.function.arguments
                    if on_tool_call:
                        on_tool_call(nombre, args)
                    resultado = self._ejecutar(nombre, args)
                    messages.append({"role": "tool", "content": resultado})

        # ---- Respuesta final en streaming ----
        if should_stop and should_stop():
            return

        buffer = []
        for chunk in _ollama.chat(
            model=self._client.model,
            messages=messages,
            stream=True,
        ):
            if should_stop and should_stop():
                return
            content = chunk.message.content
            if content:
                buffer.append(content)
                if len(buffer) >= _BUFFER_TOKENS:
                    on_token("".join(buffer))
                    buffer.clear()

        if buffer and not (should_stop and should_stop()):
            on_token("".join(buffer))

    # ------------------------------------------------------------------
    # Herramientas
    # ------------------------------------------------------------------
    def _tools_disponibles(self) -> list:
        """Combina las herramientas IFC con obtener_seleccion si hay selección."""
        tools = self._ifc_tools.definiciones() if self._ifc_tools else []
        if self._elementos:
            tools = tools + [self._schema_seleccion()]
        return tools

    def _ejecutar(self, nombre: str, args: dict) -> str:
        """Ejecuta una herramienta: intercepta obtener_seleccion, delega el resto."""
        if nombre == "obtener_seleccion":
            modo = args.get("modo", "reducido")
            return self._fmt_seleccion(modo)
        if self._ifc_tools:
            return self._ifc_tools.ejecutar(nombre, args)
        return "No hay modelo IFC cargado."

    def _schema_seleccion(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "obtener_seleccion",
                "description": (
                    "Devuelve información sobre el/los elemento/s actualmente "
                    "seleccionado/s en la interfaz. "
                    "Úsala SIEMPRE que el usuario pregunte sobre 'este elemento', "
                    "'el elemento seleccionado', 'sus propiedades', 'sus características' "
                    "o cualquier detalle del elemento activo. "
                    "No necesita ningún identificador: accede directamente a la selección actual."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "modo": {
                            "type": "string",
                            "enum": ["reducido", "agrupado", "estadistico"],
                            "description": (
                                "reducido: nombre, tipo y nombres de PSets disponibles "
                                "(sin valores; útil para saber qué información existe). "
                                "agrupado: todas las propiedades con sus valores — "
                                "USA ESTE MODO cuando el usuario pida las propiedades, "
                                "características, dimensiones o detalles del elemento. "
                                "estadistico: resumen numérico mín/máx/media/suma "
                                "(recomendado cuando hay varios elementos seleccionados)."
                            ),
                        }
                    },
                    "required": [],
                },
            },
        }

    # ------------------------------------------------------------------
    # Formateadores de selección
    # ------------------------------------------------------------------
    def _fmt_seleccion(self, modo: str) -> str:
        if not self._elementos:
            return "No hay ningún elemento seleccionado en la aplicación."
        if modo == "agrupado":
            return self._fmt_agrupado()
        if modo == "estadistico":
            return self._fmt_estadistico()
        return self._fmt_reducido()

    def _fmt_reducido(self) -> str:
        """Solo nombres de PSets, sin propiedades."""
        psets = ", ".join(g["pset"] for g in self._props) or "ninguno"

        if len(self._elementos) == 1:
            e      = self._elementos[0]
            info   = e.get_info()
            nombre = info.get("Name") or e.is_a()
            tipo   = e.is_a()
            return (
                f"Elemento seleccionado: {nombre} ({tipo})\n"
                f"PSets disponibles: {psets}"
            )

        lineas = [f"{len(self._elementos)} elementos seleccionados:"]
        for e in self._elementos[:20]:
            info   = e.get_info()
            nombre = info.get("Name") or e.is_a()
            lineas.append(f"  - {nombre} ({e.is_a()})")
        if len(self._elementos) > 20:
            lineas.append(f"  ... y {len(self._elementos) - 20} más")
        e_activo = self._elementos[-1]
        nombre_activo = e_activo.get_info().get("Name") or e_activo.is_a()
        lineas.append(f"\nPSets disponibles en elemento activo ({nombre_activo}): {psets}")
        return "\n".join(lineas)

    def _fmt_agrupado(self) -> str:
        """Nombre, tipo, GlobalId y todas las propiedades por PSet."""
        if len(self._elementos) == 1:
            e      = self._elementos[0]
            info   = e.get_info()
            nombre = info.get("Name") or e.is_a()
            tipo   = e.is_a()
            gid    = info.get("GlobalId", "")
            lineas = [
                f"Elemento seleccionado: {nombre} ({tipo})",
                f"GlobalId: {gid}",
            ]
            for grupo in self._props:
                lineas.append(f"\n{grupo['pset']}:")
                for p in grupo["props"]:
                    unidad = f" {p['unidad']}" if p["unidad"] else ""
                    lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}")
            return "\n".join(lineas)

        # Multiselección: propiedades fusionadas (merged)
        lineas = [f"{len(self._elementos)} elementos seleccionados — propiedades combinadas:"]
        for grupo in self._props:
            lineas.append(f"\n{grupo['pset']}:")
            for p in grupo["props"]:
                unidad = f" {p['unidad']}" if p["unidad"] else ""
                nota   = " (valores distintos)" if p.get("varios") else ""
                lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}{nota}")
        return "\n".join(lineas)

    def _fmt_estadistico(self) -> str:
        """Resumen numérico mín/máx/media/suma por propiedad compartida."""
        if len(self._elementos) <= 1:
            return self._fmt_agrupado()
        if not self._ifc_tools:
            return "No hay modelo IFC cargado para calcular estadísticas."

        loader = self._ifc_tools._loader
        # {(pset, nombre, unidad): [valores float]}
        acum = defaultdict(list)

        for e in self._elementos:
            for grupo in loader.get_properties(e):
                for p in grupo["props"]:
                    try:
                        acum[(grupo["pset"], p["nombre"], p["unidad"])].append(
                            float(p["valor"])
                        )
                    except (ValueError, TypeError):
                        pass

        n = len(self._elementos)
        lineas = [f"Resumen estadístico — {n} elementos seleccionados:"]
        encontrado = False

        for (pset, nombre, unidad), vals in acum.items():
            if len(vals) < 2:
                continue
            encontrado = True
            u     = f" {unidad}" if unidad else ""
            media = sum(vals) / len(vals)
            lineas.append(
                f"  {pset} / {nombre}: "
                f"mín={min(vals):.4g}{u}  máx={max(vals):.4g}{u}  "
                f"media={media:.4g}{u}  suma={sum(vals):.4g}{u}  "
                f"({len(vals)}/{n} elementos)"
            )

        if not encontrado:
            lineas.append("  No se encontraron propiedades numéricas en varios elementos.")
        return "\n".join(lineas)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_system(self, has_tools: bool) -> str:
        parts = [_SYSTEM_BASE]
        if self.contexto_archivo:
            parts.append(self.contexto_archivo)
        if self.contexto_seleccion:
            parts.append(self.contexto_seleccion)
        if has_tools:
            if self._elementos:
                parts.append(
                    "Tienes herramientas disponibles. Para cualquier pregunta sobre el "
                    "elemento seleccionado usa obtener_seleccion — nunca pidas un "
                    "identificador al usuario para consultar el elemento activo."
                )
            else:
                parts.append(
                    "Tienes herramientas disponibles para consultar el modelo IFC completo."
                )
        return "\n\n".join(parts)
