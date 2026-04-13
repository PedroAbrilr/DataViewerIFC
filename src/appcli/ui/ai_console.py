"""Panel inferior: consola de IA conectada a Ollama local."""

import tkinter as tk
from tkinter import ttk

from appcli.ui import theme


class AIConsole:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=theme.BG_DARK, height=220)
        self.frame.pack_propagate(False)
        self._build()

    def _build(self):
        # Cabecera
        header = tk.Frame(self.frame, bg=theme.BG_DARK, height=32)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(
            header, text="CONSOLA IA", bg=theme.BG_DARK,
            fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
        ).pack(side=tk.LEFT, padx=10, pady=6)

        # Área de salida
        self.output = tk.Text(
            self.frame,
            state=tk.DISABLED,
            bg=theme.BG_PANEL,
            fg=theme.FG_PRIMARY,
            insertbackground=theme.FG_PRIMARY,
            font=theme.FONT_MONO,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            wrap=tk.WORD,
            cursor="arrow",
        )
        self.output.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # Barra de entrada
        input_bar = tk.Frame(self.frame, bg=theme.BG_DARK, height=46)
        input_bar.pack(fill=tk.X, side=tk.BOTTOM)
        input_bar.pack_propagate(False)

        self.input = tk.Entry(
            input_bar,
            bg=theme.BG_SURFACE,
            fg=theme.FG_PRIMARY,
            insertbackground=theme.FG_PRIMARY,
            relief="flat",
            bd=0,
            font=theme.FONT_UI,
        )
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 6), pady=8, ipady=6)
        self.input.bind("<Return>", self._on_send)

        self.send_btn = tk.Button(
            input_bar,
            text="Enviar",
            command=self._on_send,
            bg=theme.ACCENT,
            fg="#ffffff",
            activebackground="#3a82d6",
            activeforeground="#ffffff",
            font=theme.FONT_BOLD,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=16,
        )
        self.send_btn.pack(side=tk.RIGHT, padx=(0, 10), pady=8)

    def _on_send(self, event=None):
        """Recoge el texto del usuario y lanza la consulta a Ollama."""
        pass

    def append(self, text: str):
        """Añade texto al área de salida."""
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)
