"""Herramientas IFC para tool calling con Ollama.

IFCTools expone:
  - definiciones() → lista de schemas JSON (formato OpenAI/Ollama)
  - ejecutar(nombre, args) → resultado como str listo para enviar al modelo
"""

from appcli.ifc import query as _q

_MAX_RESULTADOS = 50  # límite de elementos en respuestas de lista


class IFCTools:
    def __init__(self, loader):
        """loader — instancia de IFCLoader ya con un modelo abierto."""
        self._loader = loader

    # ------------------------------------------------------------------
    # Schemas JSON (formato OpenAI / Ollama)
    # ------------------------------------------------------------------
    def definiciones(self) -> list:
        """Devuelve la lista de schemas de herramientas disponibles."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "buscar_elementos",
                    "description": (
                        "Busca todos los elementos IFC de un tipo dado en el modelo. "
                        "Devuelve nombre, tipo IFC y GlobalId de cada elemento."
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
            },
            {
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
            },
            {
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
            },
            {
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
            },
            {
                "type": "function",
                "function": {
                    "name": "elementos_de_planta",
                    "description": (
                        "Devuelve los elementos contenidos en una planta concreta. "
                        "Usa el nombre de la planta tal como aparece en listar_plantas."
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
            },
            {
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
            },
            {
                "type": "function",
                "function": {
                    "name": "buscar_por_nombre",
                    "description": (
                        "Busca elementos cuyo Name contiene el texto indicado "
                        "(búsqueda parcial, sin distinguir mayúsculas)."
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
            },
        ]

    # ------------------------------------------------------------------
    # Ejecutor
    # ------------------------------------------------------------------
    def ejecutar(self, nombre: str, args: dict) -> str:
        """Ejecuta la herramienta indicada y devuelve el resultado como texto."""
        modelo = self._loader.model
        if modelo is None:
            return "No hay ningún archivo IFC abierto."

        try:
            if nombre == "buscar_elementos":
                return self._fmt_lista(
                    _q.buscar_por_tipo(modelo, args["tipo"]),
                    args["tipo"],
                )
            if nombre == "contar_elementos":
                n = _q.contar_por_tipo(modelo, args["tipo"])
                return f"Hay {n} elemento(s) de tipo {args['tipo']}."
            if nombre == "obtener_propiedades":
                return self._fmt_propiedades(
                    _q.obtener_propiedades(modelo, args["global_id"])
                )
            if nombre == "listar_plantas":
                plantas = _q.listar_plantas(modelo)
                if not plantas:
                    return "No se encontraron plantas en el modelo."
                lineas = [f"- {p['nombre']} (id: {p['id']})" for p in plantas]
                return "Plantas del modelo:\n" + "\n".join(lineas)
            if nombre == "elementos_de_planta":
                return self._fmt_lista(
                    _q.elementos_de_planta(modelo, args["planta"]),
                    f"planta '{args['planta']}'",
                )
            if nombre == "calcular_area_total":
                area = _q.calcular_area_total(modelo, args["tipo"])
                return f"Área total de {args['tipo']}: {area} m²."
            if nombre == "buscar_por_nombre":
                return self._fmt_lista(
                    _q.buscar_por_nombre(modelo, args["texto"]),
                    f"nombre '{args['texto']}'",
                )
            return f"Herramienta desconocida: {nombre}"
        except KeyError as e:
            return f"Argumento requerido no proporcionado: {e}"
        except Exception as e:
            return f"Error al ejecutar '{nombre}': {e}"

    # ------------------------------------------------------------------
    # Helpers de formato
    # ------------------------------------------------------------------
    def _fmt_lista(self, elementos: list, contexto: str) -> str:
        if not elementos:
            return f"No se encontraron elementos para: {contexto}."
        total = len(elementos)
        muestra = elementos[:_MAX_RESULTADOS]
        lineas = [f"- {e['nombre']} ({e['tipo']}) [id: {e['id']}]" for e in muestra]
        cabecera = f"{total} elemento(s) encontrado(s) para: {contexto}."
        if total > _MAX_RESULTADOS:
            cabecera += f" Mostrando los primeros {_MAX_RESULTADOS}."
        return cabecera + "\n" + "\n".join(lineas)

    def _fmt_propiedades(self, resultado: dict) -> str:
        if not resultado.get("encontrado"):
            return "Elemento no encontrado."
        lineas = [f"{resultado['nombre']} ({resultado['tipo']})"]
        for grupo in resultado.get("grupos", []):
            lineas.append(f"\n{grupo['pset']}:")
            for p in grupo["props"]:
                unidad = f" {p['unidad']}" if p["unidad"] else ""
                lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}")
        return "\n".join(lineas)
