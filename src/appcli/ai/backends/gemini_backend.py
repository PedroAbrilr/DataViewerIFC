"""Backend Google Gemini. Requiere GOOGLE_API_KEY en el entorno."""

import os

from .base import AIBackend, ChatResponse, ToolCall


def _get_client():
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    return genai


def _clean_api_error(exc: Exception) -> str:
    msg = str(exc)
    if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
        return (
            "Cuota de la API de Gemini agotada. "
            "Comprueba el límite diario en aistudio.google.com o activa la facturación."
        )
    if "401" in msg or "403" in msg or "API_KEY" in msg or "api key" in msg.lower():
        return "Clave de API de Gemini inválida o sin permisos. Compruébala en ⚙ Configuración."
    if "404" in msg or "not found" in msg.lower():
        return f"Modelo '{msg.split('models/')[-1].split(' ')[0]}' no disponible. Cambia el modelo en ⚙ Configuración."
    return f"Error de Gemini: {msg.splitlines()[0]}"


def _to_gemini_tools(tools: list) -> list:
    """Convierte schemas OpenAI a function_declarations de Gemini."""
    declarations = []
    for t in tools:
        fn = t["function"]
        params = fn.get("parameters", {"type": "object", "properties": {}})
        declarations.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "parameters": params,
        })
    return [{"function_declarations": declarations}]


def _to_gemini_history(messages: list) -> list:
    """Convierte historial OpenAI/Ollama a formato Gemini."""
    history = []
    for msg in messages:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "user")
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")

        if role == "user":
            if isinstance(content, str):
                history.append({"role": "user", "parts": [{"text": content}]})
        elif role in ("assistant", "model"):
            if isinstance(content, str):
                history.append({"role": "model", "parts": [{"text": content or ""}]})
            elif isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append({"text": block.get("text", "")})
                        elif block.get("type") == "function_call":
                            parts.append({"function_call": {
                                "name": block["name"],
                                "args": block.get("args", {}),
                            }})
                history.append({"role": "model", "parts": parts})
        elif role == "tool":
            name = msg.get("name", "") if isinstance(msg, dict) else ""
            result = content or ""
            history.append({"role": "user", "parts": [{"function_response": {
                "name": name,
                "response": {"result": result},
            }}]})

    return history


class GeminiBackend(AIBackend):
    def __init__(self, model: str = "gemini-2.0-flash"):
        self._model = model

    def chat_turn(self, system: str, messages: list, tools: list) -> ChatResponse:
        genai = _get_client()
        model = genai.GenerativeModel(
            model_name=self._model,
            system_instruction=system,
            tools=_to_gemini_tools(tools) if tools else None,
        )
        history = _to_gemini_history(messages[:-1]) if len(messages) > 1 else []
        last = messages[-1]
        last_text = last.get("content", "") if isinstance(last, dict) else getattr(last, "content", "")

        chat = model.start_chat(history=history)
        try:
            response = chat.send_message(last_text)
        except Exception as exc:
            raise RuntimeError(_clean_api_error(exc)) from exc

        tool_calls = []
        content_text = ""
        for part in response.parts:
            if hasattr(part, "function_call") and part.function_call.name:
                fc = part.function_call
                tool_calls.append(ToolCall(
                    id=fc.name,
                    name=fc.name,
                    arguments=dict(fc.args),
                ))
            elif hasattr(part, "text") and part.text:
                content_text += part.text

        return ChatResponse(
            tool_calls=tool_calls,
            content=content_text.strip(),
            _raw=response,
        )

    def chat_stream(self, system: str, messages: list):
        genai = _get_client()
        model = genai.GenerativeModel(
            model_name=self._model,
            system_instruction=system,
        )
        history = _to_gemini_history(messages[:-1]) if len(messages) > 1 else []
        last = messages[-1]
        last_text = last.get("content", "") if isinstance(last, dict) else getattr(last, "content", "")

        chat = model.start_chat(history=history)
        try:
            for chunk in chat.send_message(last_text, stream=True):
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            raise RuntimeError(_clean_api_error(exc)) from exc

    def make_assistant_message(self, response: ChatResponse) -> dict:
        parts = []
        if response.content:
            parts.append({"type": "text", "text": response.content})
        for tc in response.tool_calls:
            parts.append({"type": "function_call", "name": tc.name, "args": tc.arguments})
        return {"role": "model", "content": parts}

    def make_tool_message(self, tool_call_id: str, tool_name: str, result: str) -> dict:
        return {"role": "tool", "name": tool_name, "content": result}

    @property
    def display_name(self) -> str:
        return f"Gemini · {self._model}"

    @property
    def current_model(self) -> str:
        return self._model

    def is_available(self) -> tuple[bool, str]:
        if not os.environ.get("GOOGLE_API_KEY"):
            return False, "Variable de entorno GOOGLE_API_KEY no definida"
        try:
            import google.generativeai  # noqa: F401
            return True, ""
        except ImportError:
            return False, "Paquete 'google-generativeai' no instalado. Ejecuta: pip install google-generativeai"
