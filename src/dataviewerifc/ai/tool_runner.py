"""Orquestador de tool calling entre el backend de IA y el ToolRegistry.

ToolRunner:
  - mantiene el contexto del archivo IFC y del elemento seleccionado
  - construye el system prompt
  - ejecuta el bucle de tool calling (backend → herramientas → backend…)
  - entrega los tokens finales vía callback
"""

import json
import logging
import time
from pathlib import Path

_log = logging.getLogger(__name__)

from dataviewerifc.ai.backends.base import AIBackend, ToolCall

_SYSTEM_PROMPT_FILE = Path(__file__).parent.parent / "data" / "system_prompt.txt"

def _load_system_base() -> str:
    try:
        return _SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return (
            "Eres un asistente experto en BIM e IFC. "
            "Responde de forma concisa y en el mismo idioma en que te hagan la pregunta."
        )

_SYSTEM_BASE = _load_system_base()

_MAX_ITERACIONES = 5
_MAX_EXCHANGES   = 5  # exchanges antes de compactar el historial


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
        self._historial: list[dict] = []   # últimos N exchanges (user + assistant)
        self._memoria_compactada = ""      # resumen IA de exchanges anteriores

    # ------------------------------------------------------------------
    # API de contexto
    # ------------------------------------------------------------------
    def set_archivo(self, nombre: str, total: int):
        self.contexto_archivo = (
            f"Archivo IFC abierto: {nombre} ({total} elementos cargados)."
        )
        self.limpiar_historial()

    def limpiar_historial(self):
        """Resetea la memoria conversacional (al cargar nuevo archivo)."""
        self._historial = []
        self._memoria_compactada = ""

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
        system   = _SYSTEM_BASE  # siempre estático para aprovechar la KV-cache
        messages = self._build_messages(prompt)

        _log.debug("chat() — backend=%s prompt=%r", type(self.backend).__name__, prompt[:60])

        tokens_acumulados: list[str] = []
        def _on_token(text):
            tokens_acumulados.append(text)
            on_token(text)

        try:
            if getattr(self.backend, "supports_native_tools", True):
                self._chat_native_tools(system, messages, _on_token, on_tool_call, should_stop)
            else:
                self._chat_stream_tools(system, messages, _on_token, on_tool_call, should_stop)
        except Exception as exc:
            on_token(f"\n[Error del asistente: {exc}]")
            return

        if tokens_acumulados and not (should_stop and should_stop()):
            self._actualizar_historial(prompt, "".join(tokens_acumulados))

    # ------------------------------------------------------------------
    # Memoria conversacional
    # ------------------------------------------------------------------
    def _build_messages(self, prompt: str) -> list[dict]:
        """Construye la lista de mensajes: [resumen?] + historial + mensaje actual."""
        messages: list[dict] = []
        if self._memoria_compactada:
            messages.append({"role": "user", "content": f"[Resumen de la conversación anterior: {self._memoria_compactada}]"})
            messages.append({"role": "assistant", "content": "Entendido."})
        messages.extend(self._historial)
        messages.append({"role": "user", "content": self._build_context_prefix() + prompt})
        return messages

    def _actualizar_historial(self, prompt: str, respuesta: str):
        self._historial.append({"role": "user", "content": prompt})
        self._historial.append({"role": "assistant", "content": respuesta})
        if len(self._historial) // 2 >= _MAX_EXCHANGES:
            self._compactar_historial()

    def _compactar_historial(self):
        """Resume el historial actual con la IA y rota el buffer."""
        if not self._historial:
            return
        partes = []
        for msg in self._historial:
            rol = "Usuario" if msg["role"] == "user" else "Asistente"
            partes.append(f"{rol}: {msg['content']}")
        previo = f"Resumen previo:\n{self._memoria_compactada}\n\n" if self._memoria_compactada else ""
        prompt_resumen = (
            f"{previo}Resume en pocas frases los puntos clave de esta conversación sobre un "
            f"archivo IFC. Sé breve y concreto:\n\n" + "\n".join(partes)
        )
        try:
            tokens: list[str] = []
            for chunk in self.backend.chat_stream(
                "Resume conversaciones de forma concisa.",
                [{"role": "user", "content": prompt_resumen}],
            ):
                tokens.append(chunk)
            self._memoria_compactada = "".join(tokens).strip()
            _log.debug("historial compactado (%d exchanges)", _MAX_EXCHANGES)
        except Exception as e:
            _log.warning("compactación de historial falló: %s", e)
        self._historial = []

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
    def _tool_existe(self, nombre: str) -> bool:
        if self._registry_base and nombre in self._registry_base:
            return True
        if self._registry_seleccion and nombre in self._registry_seleccion:
            return True
        return False

    def _parse_json_tool_call(self, content: str):
        """Intenta parsear JSON de texto como tool call (fallback para modelos pequeños)."""
        stripped = content.strip()
        if not stripped.startswith("{"):
            return None
        try:
            data = json.loads(stripped)
            name = data.get("name") or data.get("function")
            args = data.get("parameters") or data.get("arguments") or data.get("args") or {}
            if name and isinstance(args, dict):
                return ToolCall(id="0", name=name, arguments=args)
        except Exception:
            pass
        return None

    def _chat_native_tools(self, system, messages, on_token, on_tool_call, should_stop):
        """Bucle tool calling con schemas nativos (Claude, OpenAI, Gemini)."""
        tools = self._tools_disponibles()
        if tools:
            for _ in range(_MAX_ITERACIONES):
                if should_stop and should_stop():
                    return
                response = self.backend.chat_turn(system, messages, tools)
                if not response.tool_calls:
                    if response.content:
                        tc = self._parse_json_tool_call(response.content)
                        if tc and self._tool_existe(tc.name):
                            messages.append(self.backend.make_assistant_message(response))
                            if on_tool_call:
                                on_tool_call(tc.name, tc.arguments)
                            resultado = self._ejecutar(tc.name, tc.arguments)
                            messages.append(self.backend.make_tool_message(tc.id, tc.name, resultado))
                            continue
                        if not response.content.strip().startswith("{"):
                            on_token(response.content)
                            return
                    break
                messages.append(self.backend.make_assistant_message(response))
                for tc in response.tool_calls:
                    if should_stop and should_stop():
                        return
                    if on_tool_call:
                        on_tool_call(tc.name, tc.arguments)
                    resultado = self._ejecutar(tc.name, tc.arguments)
                    messages.append(self.backend.make_tool_message(tc.id, tc.name, resultado))

        if should_stop and should_stop():
            return
        for text in self.backend.chat_stream(system, messages):
            if should_stop and should_stop():
                return
            on_token(text)

    def _chat_stream_tools(self, system, messages, on_token, on_tool_call, should_stop):
        """Stream-first con detección de JSON tool call (Ollama y modelos sin tool calling nativo).

        Los tokens de texto se emiten en tiempo real. Si la respuesta empieza por '{',
        se acumula en silencio para detectar una tool call; si es válida se ejecuta y
        se itera; si no, se emite el buffer como texto.
        """
        for i in range(_MAX_ITERACIONES):
            if should_stop and should_stop():
                return

            _log.debug("_chat_stream_tools() iteración %d — enviando a backend", i + 1)
            t0 = time.perf_counter()
            first_token = True
            buffer: list[str] = []
            is_tool_call: bool | None = None  # None = aún desconocido

            for text in self.backend.chat_stream(system, messages):
                if first_token:
                    _log.debug("primer token en %.3fs", time.perf_counter() - t0)
                    first_token = False
                if should_stop and should_stop():
                    return
                buffer.append(text)
                if is_tool_call is None:
                    stripped = "".join(buffer).lstrip()
                    if stripped.startswith("{"):
                        is_tool_call = True   # podría ser JSON → acumular
                    elif stripped:
                        is_tool_call = False  # texto claro → emitir
                        on_token(text)
                elif not is_tool_call:
                    on_token(text)

            full = "".join(buffer).strip()
            _log.debug("stream completo en %.3fs — is_tool_call=%s", time.perf_counter() - t0, is_tool_call)
            if is_tool_call:
                tc = self._parse_json_tool_call(full)
                if tc and self._tool_existe(tc.name):
                    _log.debug("tool call: %s(%s)", tc.name, tc.arguments)
                    if on_tool_call:
                        on_tool_call(tc.name, tc.arguments)
                    resultado = self._ejecutar(tc.name, tc.arguments)
                    messages.append({"role": "assistant", "content": full})
                    messages.append(self.backend.make_tool_message(tc.id, tc.name, resultado))
                    continue  # siguiente iteración para la respuesta final
                on_token(full)  # JSON inválido → emitir como texto
            return  # respuesta de texto → done

    def _build_context_prefix(self) -> str:
        parts = []
        if self.contexto_archivo:
            parts.append(self.contexto_archivo)
        else:
            parts.append("No hay ningún archivo IFC cargado.")
        if self.contexto_seleccion:
            parts.append(self.contexto_seleccion)
        return "[" + " · ".join(parts) + "]\n"
