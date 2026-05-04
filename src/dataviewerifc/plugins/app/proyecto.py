"""Plugins para gestión del directorio de proyecto y búsqueda de archivos IFC."""

from pathlib import Path

from dataviewerifc import config as _config


class ObtenerDirectorioProyecto:
    name = "obtener_directorio_proyecto"
    schema = {
        "type": "function",
        "function": {
            "name": "obtener_directorio_proyecto",
            "description": (
                "Devuelve el directorio de proyecto configurado actualmente. "
                "Úsala para saber en qué carpeta buscará la herramienta buscar_archivos_ifc."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }

    def execute(self, args: dict) -> str:
        directorio = _config.load().get("proyecto_dir", "")
        if directorio:
            return f"Directorio de proyecto: {directorio}"
        return "No hay ningún directorio de proyecto configurado."


class EstablecerDirectorioProyecto:
    name = "establecer_directorio_proyecto"
    schema = {
        "type": "function",
        "function": {
            "name": "establecer_directorio_proyecto",
            "description": (
                "Establece el directorio de proyecto. La búsqueda de archivos IFC "
                "se realizará dentro de esa carpeta. Úsala cuando el usuario indique "
                "cuál es su carpeta de proyectos o quiera cambiarla."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "description": "Ruta absoluta al directorio de proyecto.",
                    }
                },
                "required": ["ruta"],
            },
        },
    }

    def execute(self, args: dict) -> str:
        ruta = args.get("ruta", "").strip()
        if not ruta:
            return "Indica una ruta válida."
        path = Path(ruta).expanduser().resolve()
        if not path.exists():
            return f"La ruta '{path}' no existe."
        if not path.is_dir():
            return f"'{path}' no es un directorio."
        _config.save({"proyecto_dir": str(path)})
        return f"Directorio de proyecto establecido: {path}"


class BuscarArchivosIfc:
    name = "buscar_archivos_ifc"
    schema = {
        "type": "function",
        "function": {
            "name": "buscar_archivos_ifc",
            "description": (
                "Busca recursivamente archivos .ifc en el directorio de proyecto "
                "configurado. Devuelve la lista de archivos encontrados con su ruta "
                "relativa al directorio de proyecto. Úsala cuando el usuario pregunte "
                "qué archivos IFC hay disponibles o quiera abrir uno por nombre."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }

    def execute(self, args: dict) -> str:
        directorio = _config.load().get("proyecto_dir", "")
        if not directorio:
            return (
                "No hay ningún directorio de proyecto configurado. "
                "Usa establecer_directorio_proyecto para indicar uno."
            )
        base = Path(directorio)
        if not base.exists():
            return f"El directorio de proyecto '{base}' no existe."
        try:
            archivos = sorted(base.rglob("*.ifc"))
        except PermissionError:
            return f"Sin permiso para leer '{base}'."
        if not archivos:
            return f"No se encontraron archivos .ifc en '{base}'."
        lineas = [f"- {p.relative_to(base)}" for p in archivos]
        return f"Archivos IFC en '{base}':\n" + "\n".join(lineas)
