"""Panel izquierdo: árbol jerárquico de elementos IFC."""

import tkinter as tk
from tkinter import ttk


class TreePanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        self.tree = ttk.Treeview(self.frame)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def load(self, ifc_model):
        """Carga el modelo IFC y puebla el árbol."""
        pass
