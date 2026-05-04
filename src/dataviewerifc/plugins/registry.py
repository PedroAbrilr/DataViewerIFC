"""ToolRegistry: registro y despacho centralizado de herramientas de IA."""

from __future__ import annotations

from dataviewerifc.plugins.base import Tool


class ToolRegistry:
    """Registro ordenado de herramientas Tool.

    El orden de inserción se preserva en schemas() y names().
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Registra una herramienta. Lanza ValueError si el nombre ya existe."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' ya está registrado")
        self._tools[tool.name] = tool

    def schemas(self) -> list[dict]:
        """Lista de schemas en formato OpenAI, en orden de registro."""
        return [tool.schema for tool in self._tools.values()]

    def execute(self, name: str, args: dict) -> str:
        """Despacha la llamada al tool indicado. Lanza KeyError si no existe."""
        if name not in self._tools:
            raise KeyError(name)
        return self._tools[name].execute(args)

    def get_tool(self, name: str) -> Tool | None:
        """Devuelve la instancia del tool o None si no está registrado."""
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def names(self) -> list[str]:
        """Lista de nombres en orden de registro."""
        return list(self._tools.keys())
