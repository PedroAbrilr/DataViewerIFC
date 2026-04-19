"""Herramientas de interacción con la aplicación para tool calling."""

import os
from pathlib import Path


class AppTools:
    def __init__(self, get_archivo_activo, on_cargar_archivo):
        """
        get_archivo_activo — callable() → str|None  (nombre del archivo abierto o None)
        on_cargar_archivo  — callable(path: str)    (carga el archivo en la app)
        """
        self._get_archivo = get_archivo_activo
        self._cargar      = on_cargar_archivo

    # ------------------------------------------------------------------
    # Schemas
    # ------------------------------------------------------------------
    def definiciones(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "estado_app",
                    "description": (
                        "Devuelve el estado actual de la aplicación: si hay un archivo IFC "
                        "abierto y cuál es. Úsala antes de responder preguntas sobre el "
                        "modelo cuando no tengas esa información en el contexto."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "cargar_ifc",
                    "description": (
                        "Carga un archivo IFC en la aplicación. Busca el archivo por nombre "
                        "en el directorio de trabajo. Úsala cuando el usuario pida abrir o "
                        "cargar un archivo IFC concreto."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre": {
                                "type": "string",
                                "description": (
                                    "Nombre del archivo a cargar, con o sin extensión .ifc. "
                                    "Ejemplo: 'edificio' o 'edificio.ifc'."
                                ),
                            }
                        },
                        "required": ["nombre"],
                    },
                },
            },
        ]

    # ------------------------------------------------------------------
    # Ejecutor
    # ------------------------------------------------------------------
    def ejecutar(self, nombre: str, args: dict) -> str:
        if nombre == "estado_app":
            return self._estado()
        if nombre == "cargar_ifc":
            return self._cargar_ifc(args.get("nombre", ""))
        return f"Herramienta de app desconocida: {nombre}"

    # ------------------------------------------------------------------
    # Implementaciones
    # ------------------------------------------------------------------
    def _estado(self) -> str:
        archivo = self._get_archivo()
        if archivo:
            return f"Hay un archivo IFC abierto: {archivo}"
        return "No hay ningún archivo IFC abierto en la aplicación."

    def _cargar_ifc(self, nombre: str) -> str:
        if not nombre:
            return "Indica el nombre del archivo a cargar."

        cwd = Path(os.getcwd()).resolve()

        # Normalizar nombre: añadir extensión si falta
        nombre_lower = nombre.lower()
        if not nombre_lower.endswith(".ifc"):
            nombre_lower += ".ifc"

        # Rechazar cualquier intento de salir del directorio activo
        if os.sep in nombre or "/" in nombre or "\\" in nombre:
            return "Solo se pueden cargar archivos del directorio de trabajo."

        # Buscar coincidencia case-insensitive
        try:
            candidatos = [
                p for p in cwd.iterdir()
                if p.is_file() and p.suffix.lower() == ".ifc"
                and p.name.lower() == nombre_lower
            ]
        except PermissionError:
            return "No se puede acceder al directorio de trabajo."

        if not candidatos:
            # Listar los .ifc disponibles para orientar al usuario
            disponibles = [p.name for p in cwd.iterdir() if p.suffix.lower() == ".ifc"]
            if disponibles:
                lista = ", ".join(disponibles)
                return f"No se encontró '{nombre}'. Archivos disponibles: {lista}"
            return f"No se encontró '{nombre}' y no hay archivos .ifc en el directorio de trabajo."

        path = str(candidatos[0])
        self._cargar(path)
        return f"Cargando '{candidatos[0].name}'..."
