"""Carga y parseo de archivos IFC mediante ifcopenshell."""


class IFCLoader:
    def __init__(self):
        self.model = None

    def open(self, path: str):
        """Abre un archivo IFC y devuelve el modelo."""
        pass

    def get_tree(self):
        """Devuelve la jerarquía de elementos del modelo."""
        pass

    def get_properties(self, element):
        """Devuelve las propiedades de un elemento IFC."""
        pass
