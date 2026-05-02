"""Panel izquierdo: árbol jerárquico de elementos IFC."""

import tkinter as tk
from tkinter import ttk

from appcli.ui import theme


class TreePanel:
    def __init__(self, parent, on_select=None):
        self.frame = ttk.Frame(parent)
        self.on_select = on_select
        self._elementos = {}
        self._gid_to_iid = {}
        self._build()

    def _build(self):
        # Cabecera
        header = tk.Frame(self.frame, bg=theme.BG_DARK, height=32)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(
            header, text="ESTRUCTURA", bg=theme.BG_DARK,
            fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
        ).pack(side=tk.LEFT, padx=10, pady=6)

        # Árbol
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(container, show="tree", selectmode="extended")
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def load(self, nodos: list):
        self.tree.delete(*self.tree.get_children())
        self._elementos.clear()
        self._gid_to_iid = {}
        for nodo in nodos:
            self._insertar(nodo, "")

    def _insertar(self, nodo: dict, padre: str):
        etiqueta = f"{nodo['nombre']}  [{nodo['tipo']}]"
        iid = self.tree.insert(padre, tk.END, text=etiqueta, open=True)
        self._elementos[iid] = nodo["elemento"]
        if nodo.get("id"):
            self._gid_to_iid[nodo["id"]] = iid
        for hijo in nodo["hijos"]:
            self._insertar(hijo, iid)

    def select_by_ids(self, global_ids: list[str]) -> None:
        """Selecciona en el árbol los elementos cuyos GlobalId se indican."""
        iids = [self._gid_to_iid[gid] for gid in global_ids if gid in self._gid_to_iid]
        if not iids:
            return
        self.tree.selection_set(iids)
        self.tree.see(iids[0])

    def _on_select(self, event):
        if self.on_select is None:
            return
        seleccion = self.tree.selection()
        if seleccion:
            elementos = [self._elementos[iid] for iid in seleccion if iid in self._elementos]
            if elementos:
                self.on_select(elementos)
