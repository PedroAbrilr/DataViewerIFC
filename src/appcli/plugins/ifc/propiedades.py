"""Herramientas IFC de acceso a propiedades de elementos."""

from appcli.ifc import query as _q
from appcli.plugins.ifc._utils import _fmt_propiedades


class ObtenerPropiedades:
    name = "obtener_propiedades"
    schema = {
        "type": "function",
        "function": {
            "name": "obtener_propiedades",
            "description": (
                "Devuelve todas las propiedades de un elemento dado su GlobalId. "
                "Útil cuando se necesita información detallada de un elemento concreto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "global_id": {
                        "type": "string",
                        "description": "GlobalId del elemento IFC (cadena de 22 caracteres).",
                    }
                },
                "required": ["global_id"],
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
            return _fmt_propiedades(_q.obtener_propiedades(modelo, args["global_id"]))
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar 'obtener_propiedades': {e}"
