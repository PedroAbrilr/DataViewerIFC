"""Panel inferior: consola de IA conectada a Ollama local."""

import tkinter as tk
from tkinter import ttk


class AIConsole:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent, height=200)
        self._build()

    def _build(self):
        self.output = tk.Text(self.frame, state=tk.DISABLED, height=8)
        self.output.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        input_frame = ttk.Frame(self.frame)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.input = ttk.Entry(input_frame)
        self.input.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.input.bind("<Return>", self._on_send)

        self.send_btn = ttk.Button(input_frame, text="Enviar", command=self._on_send)
        self.send_btn.pack(side=tk.RIGHT)

    def _on_send(self, event=None):
        """Recoge el texto del usuario y lanza la consulta a Ollama."""
        pass

    def append(self, text: str):
        """Añade texto al área de salida."""
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)
