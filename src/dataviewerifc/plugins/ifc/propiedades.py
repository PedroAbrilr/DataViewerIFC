"""Herramientas IFC de acceso a propiedades de elementos."""

from dataviewerifc.ifc import query as _q
from dataviewerifc.plugins.ifc._utils import _extract_ids, _fmt_lista, _fmt_propiedades


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


class FiltrarPorPropiedad:
    name = "filtrar_por_propiedad"
    schema = {
        "type": "function",
        "function": {
            "name": "filtrar_por_propiedad",
            "description": (
                "Filtra y selecciona en el árbol los elementos que tienen una propiedad "
                "con un valor concreto. Puede buscar en el modelo completo o en la selección actual."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "propiedad": {
                        "type": "string",
                        "description": "Nombre de la propiedad a filtrar (p.ej. 'IsExternal', 'Área').",
                    },
                    "valor": {
                        "type": "string",
                        "description": "Valor a buscar (comparación parcial, sin distinguir mayúsculas).",
                    },
                    "fuente": {
                        "type": "string",
                        "enum": ["modelo", "seleccion"],
                        "description": (
                            "modelo: busca en todo el IFC (restringible por tipo). "
                            "seleccion: busca solo entre los elementos seleccionados."
                        ),
                    },
                    "tipo": {
                        "type": "string",
                        "description": (
                            "Tipo IFC opcional para restringir la búsqueda en el modelo. "
                            "Ignorado cuando fuente=seleccion. Ejemplo: 'IfcWall'."
                        ),
                    },
                },
                "required": ["propiedad", "valor"],
            },
        },
    }

    def __init__(self, loader, get_context=None):
        self._loader = loader
        self._get_context = get_context
        self.last_ids: list[str] = []

    def execute(self, args: dict) -> str:
        self.last_ids = []
        modelo = self._loader.model
        if modelo is None:
            return "No hay ningún archivo IFC abierto."
        try:
            propiedad = args["propiedad"]
            valor = args["valor"]
            fuente = args.get("fuente", "modelo")

            if fuente == "seleccion":
                if not self._get_context:
                    return "No hay contexto de selección disponible."
                elementos_ifc, _ = self._get_context()
                if not elementos_ifc:
                    return "No hay ningún elemento seleccionado."
                resultado = _q.filtrar_por_propiedad(elementos_ifc, propiedad, valor)
                self.last_ids = _extract_ids(resultado)
                return _fmt_lista(resultado, f"propiedad '{propiedad}' = '{valor}' en la selección")

            tipo = args.get("tipo", "")
            elementos_modelo = (
                modelo.by_type(_q._normalizar_tipo(tipo)) if tipo
                else modelo.by_type("IfcProduct")
            )
            resultado = _q.filtrar_por_propiedad(elementos_modelo, propiedad, valor)
            self.last_ids = _extract_ids(resultado)
            return _fmt_lista(resultado, f"propiedad '{propiedad}' = '{valor}'")
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar 'filtrar_por_propiedad': {e}"
