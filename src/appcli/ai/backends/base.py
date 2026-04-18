"""Interfaz común para todos los backends de IA."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ChatResponse:
    tool_calls: list[ToolCall] = field(default_factory=list)
    content: str = ""
    _raw: Any = field(default=None, repr=False)


class AIBackend(ABC):
    @abstractmethod
    def chat_turn(self, system: str, messages: list, tools: list) -> ChatResponse:
        """Turno no-streaming con soporte de tool calling."""

    @abstractmethod
    def chat_stream(self, system: str, messages: list) -> Iterator[str]:
        """Respuesta final en streaming (sin herramientas)."""

    @abstractmethod
    def make_assistant_message(self, response: ChatResponse) -> Any:
        """Mensaje de asistente en formato nativo para añadir al historial."""

    @abstractmethod
    def make_tool_message(self, tool_call_id: str, tool_name: str, result: str) -> Any:
        """Mensaje de resultado de herramienta para añadir al historial."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nombre legible: 'Ollama · ifc-assistant', 'Claude · claude-sonnet-4-6'…"""

    @property
    @abstractmethod
    def current_model(self) -> str:
        """Identificador del modelo activo."""

    def is_available(self) -> tuple[bool, str]:
        """Devuelve (disponible, mensaje_de_error)."""
        return True, ""
