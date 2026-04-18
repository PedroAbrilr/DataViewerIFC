"""Backend Ollama (modelo local)."""

import ollama as _ollama

from .base import AIBackend, ChatResponse, ToolCall


class OllamaBackend(AIBackend):
    def __init__(self, model: str = "ifc-assistant"):
        self._model = model

    def chat_turn(self, system: str, messages: list, tools: list) -> ChatResponse:
        msgs = [{"role": "system", "content": system}] + list(messages)
        response = _ollama.chat(
            model=self._model,
            messages=msgs,
            tools=tools if tools else None,
        )
        raw_calls = getattr(response.message, "tool_calls", None) or []
        tool_calls = [
            ToolCall(
                id=str(i),
                name=tc.function.name,
                arguments=tc.function.arguments if isinstance(tc.function.arguments, dict) else {},
            )
            for i, tc in enumerate(raw_calls)
        ]
        return ChatResponse(
            tool_calls=tool_calls,
            content=(response.message.content or "").strip(),
            _raw=response.message,
        )

    def chat_stream(self, system: str, messages: list):
        msgs = [{"role": "system", "content": system}] + list(messages)
        for chunk in _ollama.chat(model=self._model, messages=msgs, stream=True):
            content = chunk.message.content
            if content:
                yield content

    def make_assistant_message(self, response: ChatResponse):
        # El objeto Message nativo de Ollama es aceptado directamente en el historial
        if response._raw is not None:
            return response._raw
        return {"role": "assistant", "content": response.content}

    def make_tool_message(self, tool_call_id: str, tool_name: str, result: str) -> dict:
        return {"role": "tool", "content": result}

    @property
    def display_name(self) -> str:
        return f"Ollama · {self._model}"

    @property
    def current_model(self) -> str:
        return self._model
