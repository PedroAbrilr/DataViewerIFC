"""Backend Ollama (modelo local)."""

import logging
import time

import ollama as _ollama

from .base import AIBackend, ChatResponse, ToolCall, prepend_system

_log = logging.getLogger(__name__)


class OllamaBackend(AIBackend):
    supports_native_tools = False  # usa JSON en texto; los schemas se pasan por el system prompt

    def __init__(self, model: str = "ifc-assistant"):
        self._model = model

    def chat_turn(self, system: str, messages: list, tools: list) -> ChatResponse:
        msgs = prepend_system(system, messages)
        response = _ollama.chat(
            model=self._model,
            messages=msgs,
            keep_alive="30m",
        )
        return ChatResponse(
            tool_calls=[],
            content=(response.message.content or "").strip(),
            _raw=response.message,
        )

    def chat_stream(self, system: str, messages: list):
        msgs = prepend_system(system, messages)
        _log.debug("ollama.chat() — model=%s, %d mensajes", self._model, len(msgs))
        t0 = time.perf_counter()
        first = True
        for chunk in _ollama.chat(model=self._model, messages=msgs, stream=True, keep_alive="30m"):
            content = chunk.message.content
            if content:
                if first:
                    _log.debug("primer chunk Ollama en %.3fs", time.perf_counter() - t0)
                    first = False
                yield content

    def make_assistant_message(self, response: ChatResponse):
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
