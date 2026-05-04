"""Carga y parseo de archivos IFC mediante ifcopenshell."""

import ifcopenshell
import ifcopenshell.util.element

from dataviewerifc.ifc.query import _grupos_pset


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

        info = elemento.get_info()
        attrs = []
        for clave in ("GlobalId", "Name", "Description", "ObjectType"):
            if info.get(clave):
                attrs.append({"nombre": clave, "valor": str(info[clave]), "unidad": ""})
        attrs.append({"nombre": "Tipo IFC", "valor": elemento.is_a(), "unidad": ""})

        grupos = [{"pset": "Atributos", "props": attrs}]
        grupos.extend(_grupos_pset(elemento))
        return grupos
