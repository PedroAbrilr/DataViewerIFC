"""Plugins de interacción con la aplicación: EstadoApp y CargarIfc."""

import os
from pathlib import Path

from appcli import config as _config


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
        nombre = args.get("nombre", "").strip()
        if not nombre:
            return "Indica el nombre del archivo a cargar."

        # Normalizar: extraer solo el nombre de archivo (ignorar ruta indicada por el modelo)
        nombre_archivo = Path(nombre).name.lower()
        if not nombre_archivo.endswith(".ifc"):
            nombre_archivo += ".ifc"

        # Buscar en el directorio de trabajo y en el de proyecto recursivamente
        directorios = [Path(os.getcwd()).resolve()]
        proj_dir = _config.load().get("proyecto_dir", "")
        if proj_dir:
            proj_path = Path(proj_dir)
            if proj_path.exists() and proj_path not in directorios:
                directorios.append(proj_path)

        candidatos = []
        for base in directorios:
            try:
                candidatos += [p for p in base.rglob("*.ifc") if p.name.lower() == nombre_archivo]
            except PermissionError:
                pass

        if not candidatos:
            return (
                f"No se encontró ningún archivo llamado '{nombre}'. "
                "Usa 'buscar_archivos_ifc' para ver los disponibles."
            )

        if len(candidatos) > 1:
            lista = "\n".join(f"- {p}" for p in candidatos[:5])
            return f"Hay varios archivos con ese nombre:\n{lista}\nEspecifica la ruta completa."

        self._cargar(str(candidatos[0]))
        return f"Cargando '{candidatos[0].name}'..."
