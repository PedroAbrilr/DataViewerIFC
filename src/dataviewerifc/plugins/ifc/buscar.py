"""Herramientas IFC de búsqueda por tipo y nombre."""

from dataviewerifc.ifc import query as _q
from dataviewerifc.plugins.ifc._utils import _extract_ids, _fmt_lista


class BuscarElementos:
    name = "buscar_elementos"
    schema = {
        "type": "function",
        "function": {
            "name": "buscar_elementos",
            "description": (
                "Busca y selecciona en el árbol todos los elementos IFC de un tipo dado. "
                "Devuelve nombre, tipo IFC y GlobalId de cada elemento encontrado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "description": (
                            "Tipo IFC a buscar, con o sin prefijo 'Ifc'. "
                            "Ejemplos: 'IfcWall', 'IfcSlab', 'Window'."
                        ),
                    }
                },
                "required": ["tipo"],
            },
        },
    }

    def __init__(self, loader):
        self._loader = loader
        self.last_ids: list[str] = []

    def execute(self, args: dict) -> str:
        modelo = self._loader.model
        if modelo is None:
            return "No hay ningún archivo IFC abierto."
        try:
            elementos = _q.buscar_por_tipo(modelo, args["tipo"])
            self.last_ids = _extract_ids(elementos)
            return _fmt_lista(elementos, args["tipo"])
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar 'buscar_elementos': {e}"


class ContarElementos:
    name = "contar_elementos"
    schema = {
        "type": "function",
        "function": {
            "name": "contar_elementos",
            "description": "Cuenta cuántos elementos hay de un tipo IFC dado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "description": "Tipo IFC a contar. Ejemplos: 'IfcDoor', 'IfcColumn'.",
                    }
                },
                "required": ["tipo"],
            },
        },
    }

    def __init__(self, loader):
        self._loader = loader

    def execute(self, args: dict) -> str:
        modelo = self._loader.model
        if modelo is None:
            return "No hay ningún archivo IFC abierto."
        try:
            n = _q.contar_por_tipo(modelo, args["tipo"])
            return f"Hay {n} elemento(s) de tipo {args['tipo']}."
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar 'contar_elementos': {e}"


class BuscarPorNombre:
    name = "buscar_por_nombre"
    schema = {
        "type": "function",
        "function": {
            "name": "buscar_por_nombre",
            "description": (
                "Busca y selecciona en el árbol los elementos cuyo Name contiene "
                "el texto indicado (búsqueda parcial, sin distinguir mayúsculas)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "Texto a buscar dentro del nombre del elemento.",
                    }
                },
                "required": ["texto"],
            },
        },
    }

    def __init__(self, loader):
        self._loader = loader
        self.last_ids: list[str] = []

    def execute(self, args: dict) -> str:
        modelo = self._loader.model
        if modelo is None:
            return "No hay ningún archivo IFC abierto."
        try:
            elementos = _q.buscar_por_nombre(modelo, args["texto"])
            self.last_ids = _extract_ids(elementos)
            return _fmt_lista(elementos, f"nombre '{args['texto']}'")
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar 'buscar_por_nombre': {e}"
