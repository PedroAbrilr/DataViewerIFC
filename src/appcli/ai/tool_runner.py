"""Orquestador de tool calling entre el backend de IA e IFCTools.

ToolRunner:
  - mantiene el contexto del archivo IFC y del elemento seleccionado
  - construye el system prompt
  - ejecuta el bucle de tool calling (backend → herramientas → backend…)
  - entrega los tokens finales vía callback
"""

from collections import defaultdict

from appcli.ai.backends.base import AIBackend

_SYSTEM_BASE = (
    "Eres un asistente experto en BIM e IFC. "
    "Responde de forma concisa y en el mismo idioma en que te hagan la pregunta."
)

_MAX_ITERACIONES = 5
_BUFFER_TOKENS   = 8


class ToolRunner:
    def __init__(self, backend: AIBackend, ifc_tools=None):
        self._backend   = backend
        self._ifc_tools = ifc_tools
        self._app_tools    = None
        self.on_seleccionar = None  # callable(global_ids: list[str])
        self.contexto_archivo   = ""
        self.contexto_seleccion = ""
        self._elementos = []
        self._props     = []

    def set_app_tools(self, app_tools) -> None:
        self._app_tools = app_tools

    # ------------------------------------------------------------------
    # API de contexto
    # ------------------------------------------------------------------
    def set_archivo(self, nombre: str, total: int):
        self.contexto_archivo = (
            f"Archivo IFC abierto: {nombre} ({total} elementos cargados)."
        )

    def set_seleccion(self, elementos: list, props: list):
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
        tools   = self._tools_disponibles()
        system  = self._build_system(bool(tools))
        messages = [{"role": "user", "content": prompt}]

        try:
            # ---- Bucle de tool calling ----
            if tools:
                for _ in range(_MAX_ITERACIONES):
                    if should_stop and should_stop():
                        return

                    response = self._backend.chat_turn(system, messages, tools)

                    if not response.tool_calls:
                        if response.content:
                            on_token(response.content)
                        return

                    messages.append(self._backend.make_assistant_message(response))

                    for tc in response.tool_calls:
                        if should_stop and should_stop():
                            return
                        if on_tool_call:
                            on_tool_call(tc.name, tc.arguments)
                        resultado = self._ejecutar(tc.name, tc.arguments)
                        messages.append(
                            self._backend.make_tool_message(tc.id, tc.name, resultado)
                        )

            # ---- Respuesta final en streaming ----
            if should_stop and should_stop():
                return

            buffer = []
            for text in self._backend.chat_stream(system, messages):
                if should_stop and should_stop():
                    return
                buffer.append(text)
                if len(buffer) >= _BUFFER_TOKENS:
                    on_token("".join(buffer))
                    buffer.clear()

            if buffer and not (should_stop and should_stop()):
                on_token("".join(buffer))

        except Exception as exc:
            on_token(f"\n[Error del asistente: {exc}]")

    # ------------------------------------------------------------------
    # Herramientas
    # ------------------------------------------------------------------
    def _tools_disponibles(self) -> list:
        tools = self._ifc_tools.definiciones() if self._ifc_tools else []
        if self._elementos:
            tools = tools + [self._schema_seleccion()]
        if self._app_tools:
            tools = tools + self._app_tools.definiciones()
        return tools

    def _ejecutar(self, nombre: str, args: dict) -> str:
        if nombre == "obtener_seleccion":
            modo = args.get("modo", "reducido")
            return self._fmt_seleccion(modo)
        if self._ifc_tools:
            resultado = self._ifc_tools.ejecutar(nombre, args)
            if resultado == "_DELEGAR_SELECCION_":
                return self._filtrar_seleccion(args)
            if not resultado.startswith("Herramienta desconocida"):
                if self.on_seleccionar and self._ifc_tools._last_ids:
                    self.on_seleccionar(self._ifc_tools._last_ids)
                return resultado
        if self._app_tools:
            return self._app_tools.ejecutar(nombre, args)
        return "No hay modelo IFC cargado."

    def _filtrar_seleccion(self, args: dict) -> str:
        from appcli.ifc import query as _q
        from appcli.ai.ifc_tools import IFCTools
        if not self._elementos:
            return "No hay ningún elemento seleccionado."
        resultado = _q.filtrar_por_propiedad(
            self._elementos, args["propiedad"], args["valor"]
        )
        return self._ifc_tools._fmt_lista(
            resultado,
            f"propiedad '{args['propiedad']}' = '{args['valor']}' en la selección",
        )

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
                                "reducido: nombre, tipo y nombres de PSets disponibles. "
                                "agrupado: todas las propiedades con sus valores — "
                                "USA ESTE MODO cuando el usuario pida propiedades, "
                                "características, dimensiones o detalles del elemento. "
                                "estadistico: resumen numérico mín/máx/media/suma "
                                "(recomendado con varios elementos seleccionados)."
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

        lineas = [f"{len(self._elementos)} elementos seleccionados — propiedades combinadas:"]
        for grupo in self._props:
            lineas.append(f"\n{grupo['pset']}:")
            for p in grupo["props"]:
                unidad = f" {p['unidad']}" if p["unidad"] else ""
                nota   = " (valores distintos)" if p.get("varios") else ""
                lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}{nota}")
        return "\n".join(lineas)

    def _fmt_estadistico(self) -> str:
        if len(self._elementos) <= 1:
            return self._fmt_agrupado()
        if not self._ifc_tools:
            return "No hay modelo IFC cargado para calcular estadísticas."

        loader = self._ifc_tools._loader
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
