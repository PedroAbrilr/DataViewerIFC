"""Carga y parseo de archivos IFC mediante ifcopenshell."""

import ifcopenshell
import ifcopenshell.util.element


class IFCLoader:
    def __init__(self):
        self.model = None

    def open(self, path: str):
        """Abre un archivo IFC y almacena el modelo."""
        self.model = ifcopenshell.open(path)
        return self.model

    def get_tree(self) -> list:
        """Devuelve la jerarquía espacial del modelo como lista de nodos.

        Cada nodo es un dict con:
            id     — GlobalId del elemento
            tipo   — clase IFC (IfcWall, IfcSlab…)
            nombre — Name del elemento
            hijos  — lista de nodos hijo
        """
        if self.model is None:
            return []
        proyectos = self.model.by_type("IfcProject")
        return [self._nodo(p) for p in proyectos]

    def _nodo(self, elemento) -> dict:
        info = elemento.get_info()
        hijos = []
        for rel in getattr(elemento, "IsDecomposedBy", []):
            for hijo in rel.RelatedObjects:
                hijos.append(self._nodo(hijo))
        for rel in getattr(elemento, "ContainsElements", []):
            for hijo in rel.RelatedElements:
                hijos.append(self._nodo(hijo))
        return {
            "id": info.get("GlobalId", ""),
            "tipo": elemento.is_a(),
            "nombre": info.get("Name") or elemento.is_a(),
            "hijos": hijos,
            "elemento": elemento,
        }

    def get_properties(self, elemento) -> list:
        """Devuelve las propiedades agrupadas por PSet.

        Retorna una lista de grupos:
            [
                {
                    "pset": "Atributos",
                    "props": [
                        {"nombre": "Name", "valor": "Muro exterior", "unidad": ""},
                        ...
                    ]
                },
                ...
            ]
        """
        if elemento is None:
            return []

        grupos = []

        # --- Atributos básicos ---
        info = elemento.get_info()
        attrs = []
        for clave in ("GlobalId", "Name", "Description", "ObjectType"):
            if info.get(clave):
                attrs.append({"nombre": clave, "valor": str(info[clave]), "unidad": ""})
        attrs.append({"nombre": "Tipo IFC", "valor": elemento.is_a(), "unidad": ""})
        grupos.append({"pset": "Atributos", "props": attrs})

        # --- Property sets ---
        for rel in getattr(elemento, "IsDefinedBy", []):
            if not rel.is_a("IfcRelDefinesByProperties"):
                continue
            pset = rel.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet"):
                props = []
                for prop in pset.HasProperties:
                    if prop.is_a("IfcPropertySingleValue") and prop.NominalValue:
                        unidad = self._unidad(prop)
                        props.append({
                            "nombre": prop.Name,
                            "valor": str(prop.NominalValue.wrappedValue),
                            "unidad": unidad,
                        })
                if props:
                    grupos.append({"pset": pset.Name, "props": props})

            elif pset.is_a("IfcElementQuantity"):
                props = []
                for cantidad in pset.Quantities:
                    valor, unidad = self._cantidad(cantidad)
                    if valor is not None:
                        props.append({
                            "nombre": cantidad.Name,
                            "valor": valor,
                            "unidad": unidad,
                        })
                if props:
                    grupos.append({"pset": pset.Name, "props": props})

        return grupos

    def _unidad(self, prop) -> str:
        """Extrae la unidad de una IfcPropertySingleValue si la tiene."""
        unit = getattr(prop, "Unit", None)
        if unit is None:
            return ""
        if hasattr(unit, "Name"):
            return str(unit.Name)
        if hasattr(unit, "Prefix") and hasattr(unit, "UnitType"):
            prefix = unit.Prefix or ""
            return f"{prefix}{unit.UnitType}".lower()
        return ""

    def _cantidad(self, cantidad) -> tuple:
        """Extrae valor y unidad de una IfcPhysicalQuantity."""
        for attr in ("LengthValue", "AreaValue", "VolumeValue",
                     "WeightValue", "CountValue", "TimeValue"):
            valor = getattr(cantidad, attr, None)
            if valor is not None:
                unidades = {
                    "LengthValue": "m",
                    "AreaValue": "m²",
                    "VolumeValue": "m³",
                    "WeightValue": "kg",
                    "CountValue": "",
                    "TimeValue": "s",
                }
                return str(round(valor, 4)), unidades.get(attr, "")
        return None, ""
