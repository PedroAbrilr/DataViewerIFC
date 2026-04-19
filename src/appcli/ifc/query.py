"""Funciones de consulta puras sobre un modelo IFC cargado.

Todas reciben `modelo` (ifcopenshell.file) y devuelven datos serializables
(listas, dicts, strings, números). No dependen de la UI ni de IFCLoader.
"""


def _elem_dict(e) -> dict:
    """Convierte un elemento IFC en un dict básico (id, nombre, tipo)."""
    info = e.get_info()
    return {
        "id":     info.get("GlobalId", ""),
        "nombre": info.get("Name") or e.is_a(),
        "tipo":   e.is_a(),
    }


def _normalizar_tipo(tipo: str) -> str:
    return tipo if tipo.startswith("Ifc") else f"Ifc{tipo}"


def buscar_por_tipo(modelo, tipo: str) -> list:
    """Devuelve todos los elementos del tipo IFC dado (incluye subtipos).

    El tipo puede llevar o no el prefijo 'Ifc' (p.ej. 'Wall' o 'IfcWall').
    """
    try:
        elementos = modelo.by_type(_normalizar_tipo(tipo))
    except Exception:
        return []
    return [_elem_dict(e) for e in elementos]


def contar_por_tipo(modelo, tipo: str) -> int:
    """Cuenta los elementos del tipo IFC dado."""
    try:
        return len(modelo.by_type(_normalizar_tipo(tipo)))
    except Exception:
        return 0


def listar_plantas(modelo) -> list:
    """Devuelve los IfcBuildingStorey del modelo."""
    return [_elem_dict(e) for e in modelo.by_type("IfcBuildingStorey")]


def elementos_de_planta(modelo, nombre_planta: str) -> list:
    """Devuelve los elementos contenidos en la planta cuyo nombre coincide.

    La comparación es case-insensitive y por subcadena.
    Si hay varias coincidencias se usa la primera.
    """
    plantas = modelo.by_type("IfcBuildingStorey")
    coincidencias = [
        p for p in plantas
        if nombre_planta.lower() in (p.Name or "").lower()
    ]
    if not coincidencias:
        return []
    planta = coincidencias[0]
    resultado = []
    for rel in getattr(planta, "ContainsElements", []):
        for e in rel.RelatedElements:
            resultado.append(_elem_dict(e))
    return resultado


def calcular_area_total(modelo, tipo: str) -> float:
    """Suma los valores de AreaValue en IfcElementQuantity para el tipo dado.

    Devuelve 0.0 si no hay datos de área. Solo cuenta una vez por elemento
    aunque tenga el dato en varios quantity sets.
    """
    try:
        ifc_elementos = modelo.by_type(_normalizar_tipo(tipo))
    except Exception:
        return 0.0

    total = 0.0
    for e in ifc_elementos:
        for rel in getattr(e, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pset = rel.RelatingPropertyDefinition
            if not pset.is_a("IfcElementQuantity"):
                continue
            area_encontrada = False
            for cantidad in pset.Quantities:
                area = getattr(cantidad, "AreaValue", None)
                if area is not None:
                    total += area
                    area_encontrada = True
                    break
            if area_encontrada:
                break  # no acumular de varios quantity sets

    return round(total, 4)


def buscar_por_nombre(modelo, texto: str) -> list:
    """Devuelve los IfcProduct cuyo Name contiene el texto (case-insensitive)."""
    texto_lower = texto.lower()
    resultado = []
    for e in modelo.by_type("IfcProduct"):
        nombre = getattr(e, "Name", None) or ""
        if texto_lower in nombre.lower():
            resultado.append(_elem_dict(e))
    return resultado


def filtrar_por_propiedad(elementos: list, propiedad: str, valor: str) -> list:
    """Filtra elementos que tienen una propiedad cuyo valor contiene el texto dado.

    La comparación es case-insensitive y por subcadena.
    Busca en IfcPropertySet e IfcElementQuantity.
    """
    propiedad_lower = propiedad.lower()
    valor_lower     = valor.lower()
    resultado       = []

    for e in elementos:
        for rel in getattr(e, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pset = rel.RelatingPropertyDefinition

            if pset.is_a("IfcPropertySet"):
                for prop in getattr(pset, "HasProperties", []):
                    if prop.Name.lower() != propiedad_lower:
                        continue
                    if prop.is_a("IfcPropertySingleValue") and prop.NominalValue:
                        if valor_lower in str(prop.NominalValue.wrappedValue).lower():
                            resultado.append(_elem_dict(e))
                            break
                else:
                    continue
                break

            elif pset.is_a("IfcElementQuantity"):
                for cantidad in getattr(pset, "Quantities", []):
                    if cantidad.Name.lower() != propiedad_lower:
                        continue
                    for attr in ("LengthValue", "AreaValue", "VolumeValue",
                                 "WeightValue", "CountValue", "TimeValue"):
                        val = getattr(cantidad, attr, None)
                        if val is not None and valor_lower in str(val).lower():
                            resultado.append(_elem_dict(e))
                            break
                    break

    return resultado


def obtener_propiedades(modelo, global_id: str) -> dict:
    """Devuelve las propiedades de un elemento dado su GlobalId.

    Retorna {'encontrado': False} si no existe el elemento, o bien
    {'encontrado': True, 'nombre': ..., 'tipo': ..., 'grupos': [...]}
    con la misma estructura de grupos que IFCLoader.get_properties.
    """
    try:
        elemento = modelo.by_guid(global_id)
    except Exception:
        elemento = None

    if elemento is None:
        return {"encontrado": False}

    info = elemento.get_info()

    # Atributos básicos
    attrs = []
    for clave in ("GlobalId", "Name", "Description", "ObjectType"):
        if info.get(clave):
            attrs.append({"nombre": clave, "valor": str(info[clave]), "unidad": ""})
    attrs.append({"nombre": "Tipo IFC", "valor": elemento.is_a(), "unidad": ""})
    grupos = [{"pset": "Atributos", "props": attrs}]

    _unidades_cantidad = {
        "LengthValue": "m",
        "AreaValue":   "m²",
        "VolumeValue": "m³",
        "WeightValue": "kg",
        "CountValue":  "",
        "TimeValue":   "s",
    }

    for rel in getattr(elemento, "IsDefinedBy", []):
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pset = rel.RelatingPropertyDefinition

        if pset.is_a("IfcPropertySet"):
            props = []
            for prop in pset.HasProperties:
                if prop.is_a("IfcPropertySingleValue") and prop.NominalValue:
                    props.append({
                        "nombre": prop.Name,
                        "valor":  str(prop.NominalValue.wrappedValue),
                        "unidad": "",
                    })
            if props:
                grupos.append({"pset": pset.Name, "props": props})

        elif pset.is_a("IfcElementQuantity"):
            props = []
            for cantidad in pset.Quantities:
                for attr, unidad in _unidades_cantidad.items():
                    valor = getattr(cantidad, attr, None)
                    if valor is not None:
                        props.append({
                            "nombre": cantidad.Name,
                            "valor":  str(round(valor, 4)),
                            "unidad": unidad,
                        })
                        break
            if props:
                grupos.append({"pset": pset.Name, "props": props})

    return {
        "encontrado": True,
        "nombre": info.get("Name") or elemento.is_a(),
        "tipo":   elemento.is_a(),
        "grupos": grupos,
    }
