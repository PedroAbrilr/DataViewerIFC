"""Plugins de interacción con la aplicación: EstadoApp y CargarIfc."""

import os
from pathlib import Path


class EstadoApp:
    name = "estado_app"
    schema = {
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
    }

    def __init__(self, get_archivo_activo):
        self._get_archivo = get_archivo_activo
        self.last_ids: list[str] = []

    def execute(self, args: dict) -> str:
        archivo = self._get_archivo()
        if archivo:
            return f"Hay un archivo IFC abierto: {archivo}"
        return "No hay ningún archivo IFC abierto en la aplicación."


class CargarIfc:
    name = "cargar_ifc"
    schema = {
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
    }

    def __init__(self, on_cargar_archivo):
        self._cargar = on_cargar_archivo
        self.last_ids: list[str] = []

    def execute(self, args: dict) -> str:
        nombre = args.get("nombre", "")
        if not nombre:
            return "Indica el nombre del archivo a cargar."

        cwd = Path(os.getcwd()).resolve()

        nombre_lower = nombre.lower()
        if not nombre_lower.endswith(".ifc"):
            nombre_lower += ".ifc"

        if os.sep in nombre or "/" in nombre or "\\" in nombre:
            return "Solo se pueden cargar archivos del directorio de trabajo."

        try:
            candidatos = [
                p for p in cwd.iterdir()
                if p.is_file() and p.suffix.lower() == ".ifc"
                and p.name.lower() == nombre_lower
            ]
        except PermissionError:
            return "No se puede acceder al directorio de trabajo."

        if not candidatos:
            disponibles = [p.name for p in cwd.iterdir() if p.suffix.lower() == ".ifc"]
            if disponibles:
                lista = ", ".join(disponibles)
                return f"No se encontró '{nombre}'. Archivos disponibles: {lista}"
            return f"No se encontró '{nombre}' y no hay archivos .ifc en el directorio de trabajo."

        path = str(candidatos[0])
        self._cargar(path)
        return f"Cargando '{candidatos[0].name}'..."
