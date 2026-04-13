"""Panel inferior: consola de IA conectada a Ollama local."""

import threading
import tkinter as tk
from tkinter import ttk

from appcli.ui import theme

SYSTEM_BASE = (
    "Eres un asistente experto en BIM e IFC. "
    "Responde de forma concisa y en el mismo idioma en que te hagan la pregunta."
)


class AIConsole:
    def __init__(self, parent, ollama_client=None):
        self.frame = tk.Frame(parent, bg=theme.BG_DARK, height=220)
        self.frame.pack_propagate(False)
        self._client = ollama_client
        self._context_archivo = ""   # archivo IFC abierto
        self._context_elemento = ""  # elemento seleccionado
        self._procesando = False
        self._build()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------
    def _build(self):
        # Cabecera
        header = tk.Frame(self.frame, bg=theme.BG_DARK, height=32)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(
            header, text="CONSOLA IA", bg=theme.BG_DARK,
            fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
        ).pack(side=tk.LEFT, padx=10, pady=6)

        self.lbl_modelo = tk.Label(
            header, text="", bg=theme.BG_DARK,
            fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
        )
        self.lbl_modelo.pack(side=tk.RIGHT, padx=10)

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
        self.output.tag_configure("usuario",
            foreground=theme.ACCENT, font=theme.FONT_BOLD)
        self.output.tag_configure("ia",
            foreground=theme.FG_PRIMARY)
        self.output.tag_configure("error",
            foreground="#e06c75")
        self.output.tag_configure("info",
            foreground=theme.FG_SECONDARY)
        # Barra de entrada (se empaqueta ANTES que output para que pack
        # reserve su espacio antes de expandir el área de texto)
        input_bar = tk.Frame(self.frame, bg=theme.BG_DARK, height=46)
        input_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.output.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
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
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True,
                        padx=(10, 6), pady=8, ipady=6)
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

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def set_client(self, client):
        """Asigna el cliente Ollama y muestra el modelo activo."""
        self._client = client
        self.lbl_modelo.config(text=client.model)

    def set_archivo(self, nombre: str, total: int):
        """Actualiza el contexto con el archivo IFC activo."""
        self._context_archivo = f"Archivo IFC abierto: {nombre} ({total} elementos cargados)."
        self._append(f"[Archivo: {nombre}  —  {total} elementos]\n", "info")

    def set_context(self, elemento, props: list):
        """Actualiza el contexto IFC con el elemento seleccionado."""
        if not elemento:
            self._context_elemento = ""
            return
        info = elemento.get_info()
        nombre = info.get("Name") or elemento.is_a()
        tipo = elemento.is_a()
        lineas = [f"Elemento seleccionado en la aplicación: {nombre} ({tipo})"]
        for grupo in props:
            lineas.append(f"\n{grupo['pset']}:")
            for p in grupo["props"]:
                unidad = f" {p['unidad']}" if p["unidad"] else ""
                lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}")
        self._context_elemento = "\n".join(lineas)
        self._append(f"[Elemento: {nombre}  {tipo}]\n", "info")

    # ------------------------------------------------------------------
    # Envío y streaming
    # ------------------------------------------------------------------
    def _on_send(self, event=None):
        if self._procesando:
            return
        texto = self.input.get().strip()
        if not texto:
            return
        if self._client is None:
            self._append("Ollama no está configurado.\n", "error")
            return

        self.input.delete(0, tk.END)
        self._append(f"▶ {texto}\n", "usuario")
        self._set_procesando(True)

        system = SYSTEM_BASE
        if self._context_archivo:
            system += f"\n\n{self._context_archivo}"
        if self._context_elemento:
            system += f"\n\n{self._context_elemento}"

        threading.Thread(
            target=self._stream_respuesta,
            args=(texto, system),
            daemon=True,
        ).start()

    def _stream_respuesta(self, prompt: str, system: str):
        root = self.frame.winfo_toplevel()
        try:
            primer_token = True
            for fragmento in self._client.stream(prompt, system=system):
                if primer_token:
                    root.after(0, lambda: self._append("", "ia"))
                    primer_token = False
                root.after(0, lambda f=fragmento: self._append_token(f))
            root.after(0, lambda: self._append("\n", "ia"))
        except Exception as e:
            root.after(0, lambda: self._append(f"Error: {e}\n", "error"))
        finally:
            root.after(0, lambda: self._set_procesando(False))

    # ------------------------------------------------------------------
    # Helpers de UI
    # ------------------------------------------------------------------
    def _append(self, text: str, tag: str = "ia"):
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text, tag)
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)

    def _append_token(self, token: str):
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, token, "ia")
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)

    def _set_procesando(self, valor: bool):
        self._procesando = valor
        estado = tk.DISABLED if valor else tk.NORMAL
        self.send_btn.config(state=estado)
        self.input.config(state=estado)

    def append(self, text: str):
        """API de compatibilidad para añadir texto externo."""
        self._append(text + "\n", "ia")
