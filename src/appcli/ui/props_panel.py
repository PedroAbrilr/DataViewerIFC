"""Panel derecho: tabla de propiedades del elemento seleccionado."""

import tkinter as tk
from tkinter import ttk


class PropsPanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        columns = ("propiedad", "valor")
        self.table = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.table.heading("propiedad", text="Propiedad")
        self.table.heading("valor", text="Valor")
        self.table.pack(fill=tk.BOTH, expand=True)

    def show(self, properties: dict):
        """Muestra las propiedades de un elemento IFC."""
        for row in self.table.get_children():
            self.table.delete(row)
        for key, value in properties.items():
            self.table.insert("", tk.END, values=(key, value))
