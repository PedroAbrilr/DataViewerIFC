"""Panel derecho: tabla de propiedades agrupadas por PSet."""

import tkinter as tk
from tkinter import ttk

from appcli.ui import theme


class PropsPanel:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self._build()

    def _build(self):
        # Cabecera
        header = tk.Frame(self.frame, bg=theme.BG_DARK, height=32)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(
            header, text="PROPIEDADES", bg=theme.BG_DARK,
            fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
        ).pack(side=tk.LEFT, padx=10, pady=6)

        # Tabla
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.BOTH, expand=True)

        columns = ("valor", "unidad")
        self.table = ttk.Treeview(container, columns=columns, show="tree headings")
        self.table.heading("#0",      text="Propiedad")
        self.table.heading("valor",   text="Valor")
        self.table.heading("unidad",  text="Unidad")
        self.table.column("#0",     width=220, stretch=True,  minwidth=140)
        self.table.column("valor",  width=200, stretch=True,  minwidth=100)
        self.table.column("unidad", width=70,  stretch=False, minwidth=50)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        # Tag visual para nodos PSet
        self.table.tag_configure(
            "pset",
            background=theme.BG_HEADER,
            foreground=theme.FG_HEADING,
            font=theme.FONT_BOLD,
        )

    def show(self, grupos: list):
        self.table.delete(*self.table.get_children())
        for grupo in grupos:
            nodo_pset = self.table.insert(
                "", tk.END, text=f"  {grupo['pset']}",
                values=("", ""), open=True, tags=("pset",),
            )
            for prop in grupo["props"]:
                self.table.insert(
                    nodo_pset, tk.END,
                    text=f"    {prop['nombre']}",
                    values=(prop["valor"], prop["unidad"]),
                )
