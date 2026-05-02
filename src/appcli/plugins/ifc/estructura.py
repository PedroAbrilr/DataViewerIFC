"""Herramientas IFC de estructura edilicia: plantas y áreas."""

from appcli.ifc import query as _q
from appcli.plugins.ifc._utils import _extract_ids, _fmt_lista


class ListarPlantas:
    name = "listar_plantas"
    schema = {
        "type": "function",
        "function": {
            "name": "listar_plantas",
            "description": "Lista todas las plantas (IfcBuildingStorey) del modelo.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
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
            plantas = _q.listar_plantas(modelo)
            if not plantas:
                return "No se encontraron plantas en el modelo."
            lineas = [f"- {p['nombre']} (id: {p['id']})" for p in plantas]
            return "Plantas del modelo:\n" + "\n".join(lineas)
        except Exception as e:
            return f"Error al ejecutar 'listar_plantas': {e}"


class ElementosDePlanta:
    name = "elementos_de_planta"
    schema = {
        "type": "function",
        "function": {
            "name": "elementos_de_planta",
            "description": (
                "Devuelve y selecciona en el árbol los elementos contenidos en una "
                "planta concreta. Usa el nombre de la planta tal como aparece en listar_plantas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "planta": {
                        "type": "string",
                        "description": "Nombre (o parte del nombre) de la planta.",
                    }
                },
                "required": ["planta"],
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
            elementos = _q.elementos_de_planta(modelo, args["planta"])
            self.last_ids = _extract_ids(elementos)
            return _fmt_lista(elementos, f"planta '{args['planta']}'")
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar 'elementos_de_planta': {e}"


class CalcularAreaTotal:
    name = "calcular_area_total"
    schema = {
        "type": "function",
        "function": {
            "name": "calcular_area_total",
            "description": (
                "Calcula la suma de áreas de todos los elementos de un tipo IFC. "
                "Devuelve el total en m²."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "description": "Tipo IFC cuyas áreas se suman. Ejemplo: 'IfcSlab'.",
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
            area = _q.calcular_area_total(modelo, args["tipo"])
            return f"Área total de {args['tipo']}: {area} m²."
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar 'calcular_area_total': {e}"
