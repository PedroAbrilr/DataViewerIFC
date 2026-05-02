"""Orquestador de tool calling entre el backend de IA y el ToolRegistry.

ToolRunner:
  - mantiene el contexto del archivo IFC y del elemento seleccionado
  - construye el system prompt
  - ejecuta el bucle de tool calling (backend → herramientas → backend…)
  - entrega los tokens finales vía callback
"""

from appcli.ai.backends.base import AIBackend

_SYSTEM_BASE = (
    "Eres un asistente experto en BIM e IFC. "
    "Responde de forma concisa y en el mismo idioma en que te hagan la pregunta."
)

_MAX_ITERACIONES = 5


class ToolRunner:
    def __init__(self, backend: AIBackend, registry_base=None, registry_seleccion=None):
        self.backend = backend
        self._registry_base      = registry_base
        self._registry_seleccion = registry_seleccion
        self.on_seleccionar      = None  # callable(global_ids: list[str])
        self.contexto_archivo    = ""
        self.contexto_seleccion  = ""
        self._elementos          = []
        self._props              = []

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
            if tools:
                for _ in range(_MAX_ITERACIONES):
                    if should_stop and should_stop():
                        return

                    response = self.backend.chat_turn(system, messages, tools)

                    if not response.tool_calls:
                        if response.content:
                            on_token(response.content)
                            return
                        break  # respuesta vacía sin tool calls → fallback a streaming

                    messages.append(self.backend.make_assistant_message(response))

                    for tc in response.tool_calls:
                        if should_stop and should_stop():
                            return
                        if on_tool_call:
                            on_tool_call(tc.name, tc.arguments)
                        resultado = self._ejecutar(tc.name, tc.arguments)
                        messages.append(
                            self.backend.make_tool_message(tc.id, tc.name, resultado)
                        )

            if should_stop and should_stop():
                return

            for text in self.backend.chat_stream(system, messages):
                if should_stop and should_stop():
                    return
                on_token(text)

        except Exception as exc:
            on_token(f"\n[Error del asistente: {exc}]")

    # ------------------------------------------------------------------
    # Herramientas
    # ------------------------------------------------------------------
    def _tools_disponibles(self) -> list:
        tools = self._registry_base.schemas() if self._registry_base else []
        if self._elementos and self._registry_seleccion:
            tools = tools + self._registry_seleccion.schemas()
        return tools

    def _ejecutar(self, nombre: str, args: dict) -> str:
        if self._registry_seleccion and nombre in self._registry_seleccion:
            return self._registry_seleccion.execute(nombre, args)
        if self._registry_base and nombre in self._registry_base:
            resultado = self._registry_base.execute(nombre, args)
            tool = self._registry_base.get_tool(nombre)
            if self.on_seleccionar and tool and getattr(tool, "last_ids", []):
                self.on_seleccionar(tool.last_ids)
            return resultado
        return "Herramienta no disponible."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_system(self, has_tools: bool) -> str:
        parts = [_SYSTEM_BASE]
        if self.contexto_archivo:
            parts.append(self.contexto_archivo)
        else:
            parts.append("No hay ningún archivo IFC cargado actualmente.")
        if self.contexto_seleccion:
            parts.append(self.contexto_seleccion)
        if has_tools:
            if self._elementos:
                parts.append(
                    "Tienes herramientas disponibles. Responde desde el contexto cuando "
                    "tengas la información; para el elemento seleccionado usa "
                    "obtener_seleccion — nunca pidas un identificador al usuario."
                )
            else:
                parts.append(
                    "Tienes herramientas disponibles. Las herramientas de búsqueda "
                    "(buscar_elementos, buscar_por_nombre, elementos_de_planta, "
                    "filtrar_por_propiedad) seleccionan automáticamente los elementos "
                    "encontrados en el árbol de la aplicación. Úsalas cuando el usuario "
                    "pida buscar, mostrar o seleccionar elementos. Responde desde el "
                    "contexto cuando ya tengas la información."
                )
        return "\n\n".join(parts)
