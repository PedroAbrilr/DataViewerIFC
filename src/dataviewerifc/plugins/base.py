"""Protocolo Tool: contrato estructural para todas las herramientas de IA."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    """Contrato estructural para herramientas invocables por el modelo de IA.

    Atributos requeridos:
      name   — nombre único, coincide con function.name dentro del schema.
      schema — dict completo en formato OpenAI:
               {"type": "function", "function": {"name": ..., "description": ...,
                                                  "parameters": {...}}}

    Atributo opcional last_ids: las herramientas que producen listas de elementos
    seleccionables en la UI pueden exponer `last_ids: list[str]`. El runner lo lee
    con getattr(tool, "last_ids", []) tras cada execute(). No se declara aquí para
    no romper isinstance() en Python 3.13+, donde solo se comprueban métodos.
    """

    name: str
    schema: dict

    def execute(self, args: dict) -> str: ...
