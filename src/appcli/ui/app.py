"""Ventana principal: organiza los tres paneles de la interfaz."""

import tkinter as tk
from tkinter import ttk

from appcli.ui.tree_panel import TreePanel
from appcli.ui.props_panel import PropsPanel
from appcli.ui.ai_console import AIConsole


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AppCLI — IFC Viewer")
        self.root.geometry("1200x800")
        self._build_layout()

    def _build_layout(self):
        # Panel superior: árbol + propiedades
        top_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        top_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self.tree_panel = TreePanel(top_frame)
        self.props_panel = PropsPanel(top_frame)
        top_frame.add(self.tree_panel.frame, weight=1)
        top_frame.add(self.props_panel.frame, weight=2)

        # Panel inferior: consola IA
        self.ai_console = AIConsole(self.root)
        self.ai_console.frame.pack(fill=tk.BOTH, expand=False, side=tk.BOTTOM)

    def run(self):
        self.root.mainloop()
