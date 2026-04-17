"""Orquestador de tool calling entre Ollama e IFCTools.

ToolRunner:
  - mantiene el contexto del archivo IFC y del elemento seleccionado
  - construye el system prompt completo en cada consulta
  - ejecuta el bucle de tool calling (Ollama → IFCTools → Ollama…)
  - entrega los tokens finales vía callback
"""

import ollama as _ollama

_SYSTEM_BASE = (
    "Eres un asistente experto en BIM e IFC. "
    "Responde de forma concisa y en el mismo idioma en que te hagan la pregunta."
)

_MAX_ITERACIONES = 5   # rondas máximas de tool calling por consulta
_BUFFER_TOKENS   = 8   # tokens agrupados antes de entregar al callback


class ToolRunner:
    def __init__(self, ollama_client, ifc_tools=None):
        """
        ollama_client — instancia de OllamaClient (para leer el modelo activo)
        ifc_tools     — instancia de IFCTools, o None si no hay modelo cargado
        """
        self._client    = ollama_client
        self._ifc_tools = ifc_tools
        self.contexto_archivo   = ""
        self.contexto_seleccion = ""

    # ------------------------------------------------------------------
    # API de contexto
    # ------------------------------------------------------------------
    def set_archivo(self, nombre: str, total: int):
        """Actualiza el contexto con el archivo IFC activo."""
        self.contexto_archivo = (
            f"Archivo IFC abierto: {nombre} ({total} elementos cargados)."
        )

    def set_seleccion(self, elementos: list, props: list):
        """Actualiza el contexto con el/los elemento/s seleccionado/s en la UI.

        elementos — lista de objetos IFC seleccionados.
        props     — grupos de propiedades (estructura de IFCLoader.get_properties).
        """
        if not elementos:
            self.contexto_seleccion = ""
            return

        if len(elementos) == 1:
            info  = elementos[0].get_info()
            nombre = info.get("Name") or elementos[0].is_a()
            tipo   = elementos[0].is_a()
            lineas = [f"Elemento actualmente seleccionado: {nombre} ({tipo})"]
            for grupo in props:
                lineas.append(f"\n{grupo['pset']}:")
                for p in grupo["props"]:
                    unidad = f" {p['unidad']}" if p["unidad"] else ""
                    lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}")
            self.contexto_seleccion = "\n".join(lineas)
        else:
            lineas = [f"Elementos seleccionados ({len(elementos)}):"]
            for e in elementos:
                info  = e.get_info()
                nombre = info.get("Name") or e.is_a()
                lineas.append(f"  - {nombre} ({e.is_a()})")
            self.contexto_seleccion = "\n".join(lineas)

    # ------------------------------------------------------------------
    # Chat principal
    # ------------------------------------------------------------------
    def chat(self, prompt: str, on_token, on_tool_call=None, should_stop=None):
        """Ejecuta una consulta completa con soporte de tool calling.

        prompt       — texto del usuario
        on_token     — callable(str) llamado con cada fragmento de texto
        on_tool_call — callable(nombre, args) llamado al invocar una herramienta
        should_stop  — callable() que devuelve True para cancelar
        """
        tools    = self._ifc_tools.definiciones() if self._ifc_tools else []
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
                    # Respuesta de texto directa — la emitimos y terminamos
                    content = (response.message.content or "").strip()
                    if content:
                        on_token(content)
                    return

                # Añadir respuesta del asistente al historial
                messages.append(response.message)

                # Ejecutar cada herramienta y añadir resultado al historial
                for tc in tool_calls:
                    if should_stop and should_stop():
                        return
                    nombre    = tc.function.name
                    args      = tc.function.arguments
                    if on_tool_call:
                        on_tool_call(nombre, args)
                    resultado = self._ifc_tools.ejecutar(nombre, args)
                    messages.append({"role": "tool", "content": resultado})

            # Límite de iteraciones alcanzado → dejamos que el bloque
            # de streaming de abajo genere la respuesta final sin tools.

        # ---- Respuesta final en streaming ----
        # (sin tools para no disparar más tool calls)
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
    # Helpers
    # ------------------------------------------------------------------
    def _build_system(self, has_tools: bool) -> str:
        parts = [_SYSTEM_BASE]
        if self.contexto_archivo:
            parts.append(self.contexto_archivo)
        if self.contexto_seleccion:
            parts.append(self.contexto_seleccion)
        if has_tools:
            parts.append(
                "Tienes herramientas disponibles para consultar el modelo IFC completo."
            )
        return "\n\n".join(parts)
