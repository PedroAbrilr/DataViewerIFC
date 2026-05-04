"""Backend Claude (Anthropic API). Requiere ANTHROPIC_API_KEY en el entorno."""

import os

from .base import AIBackend, ChatResponse, ToolCall

_MAX_TOKENS = 8096


def _get_client():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _to_claude_tools(tools: list) -> list:
    result = []
    for t in tools:
        fn = t["function"]
        result.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return result


def _to_claude_messages(messages: list) -> list:
    """Convierte mensajes OpenAI/Ollama a formato Claude."""
    result = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", "user")

        if role == "tool":
            # Agrupa resultados de herramientas consecutivos en un único mensaje de usuario
            tool_results = []
            while i < len(messages):
                m = messages[i]
                r = m.get("role") if isinstance(m, dict) else getattr(m, "role", "")
                if r != "tool":
                    break
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": (m.get("tool_call_id") or "") if isinstance(m, dict) else "",
                    "content": (m.get("content") or "") if isinstance(m, dict) else (getattr(m, "content", "") or ""),
                })
                i += 1
            result.append({"role": "user", "content": tool_results})

        elif role == "assistant":
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
            if isinstance(content, list):
                result.append({"role": "assistant", "content": content})
            else:
                result.append({"role": "assistant", "content": content or ""})
            i += 1

        elif role == "user":
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
            if isinstance(content, list):
                result.append({"role": "user", "content": content})
            else:
                result.append({"role": "user", "content": str(content or "")})
            i += 1

        else:
            i += 1

    return result


class ClaudeBackend(AIBackend):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self._model = model

    def chat_turn(self, system: str, messages: list, tools: list) -> ChatResponse:
        client = _get_client()
        claude_messages = _to_claude_messages(messages)
        kwargs: dict = {
            "model": self._model,
            "max_tokens": _MAX_TOKENS,
            "system": system,
            "messages": claude_messages,
        }
        if tools:
            kwargs["tools"] = _to_claude_tools(tools)

        response = client.messages.create(**kwargs)

        tool_calls = []
        content_text = ""
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))
            elif block.type == "text":
                content_text += block.text

        return ChatResponse(tool_calls=tool_calls, content=content_text.strip())

    def chat_stream(self, system: str, messages: list):
        client = _get_client()
        with client.messages.stream(
            model=self._model,
            max_tokens=_MAX_TOKENS,
            system=system,
            messages=_to_claude_messages(messages),
        ) as stream:
            for text in stream.text_stream:
                yield text

    def make_assistant_message(self, response: ChatResponse) -> dict:
        content = []
        if response.content:
            content.append({"type": "text", "text": response.content})
        for tc in response.tool_calls:
            content.append({
                "type": "tool_use",
                "id": tc.id,
                "name": tc.name,
                "input": tc.arguments,
            })
        return {"role": "assistant", "content": content}

    def make_tool_message(self, tool_call_id: str, tool_name: str, result: str) -> dict:
        return {"role": "tool", "tool_call_id": tool_call_id, "content": result}

    @property
    def display_name(self) -> str:
        return f"Claude · {self._model}"

    @property
    def current_model(self) -> str:
        return self._model

    def is_available(self) -> tuple[bool, str]:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return False, "Variable de entorno ANTHROPIC_API_KEY no definida"
        try:
            import anthropic  # noqa: F401
            return True, ""
        except ImportError:
            return False, "Paquete 'anthropic' no instalado. Ejecuta: pip install anthropic"
