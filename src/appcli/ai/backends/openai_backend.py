"""Backend OpenAI / ChatGPT. Requiere OPENAI_API_KEY en el entorno."""

import json
import os

from .base import AIBackend, ChatResponse, ToolCall, prepend_system


def _get_client():
    import openai
    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _prepare_messages(system: str, messages: list) -> list:
    msgs = prepend_system(system, [])
    for msg in messages:
        if isinstance(msg, dict):
            msgs.append(msg)
        else:
            msgs.append({"role": msg.role, "content": msg.content or ""})
    return msgs


class OpenAIBackend(AIBackend):
    def __init__(self, model: str = "gpt-4o-mini"):
        self._model = model

    def chat_turn(self, system: str, messages: list, tools: list) -> ChatResponse:
        client = _get_client()
        msgs = _prepare_messages(system, messages)
        kwargs: dict = {"model": self._model, "messages": msgs}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        return ChatResponse(
            tool_calls=tool_calls,
            content=(msg.content or "").strip(),
            _raw=msg,
        )

    def chat_stream(self, system: str, messages: list):
        client = _get_client()
        msgs = _prepare_messages(system, messages)
        for chunk in client.chat.completions.create(
            model=self._model, messages=msgs, stream=True
        ):
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def make_assistant_message(self, response: ChatResponse) -> dict:
        raw = response._raw
        if raw is not None:
            msg: dict = {"role": "assistant", "content": raw.content}
            if raw.tool_calls:
                msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in raw.tool_calls
                ]
            return msg
        return {"role": "assistant", "content": response.content}

    def make_tool_message(self, tool_call_id: str, tool_name: str, result: str) -> dict:
        return {"role": "tool", "tool_call_id": tool_call_id, "name": tool_name, "content": result}

    @property
    def display_name(self) -> str:
        return f"ChatGPT · {self._model}"

    @property
    def current_model(self) -> str:
        return self._model

    def is_available(self) -> tuple[bool, str]:
        if not os.environ.get("OPENAI_API_KEY"):
            return False, "Variable de entorno OPENAI_API_KEY no definida"
        try:
            import openai  # noqa: F401
            return True, ""
        except ImportError:
            return False, "Paquete 'openai' no instalado. Ejecuta: pip install openai"
