"""Panel inferior: consola de IA conectada a Ollama local."""

import threading
import tkinter as tk

from appcli.ui import theme


class AIConsole:
    def __init__(self, parent, tool_runner=None):
        self.frame = tk.Frame(parent, bg=theme.BG_DARK, height=220)
        self.frame.pack_propagate(False)
        self._runner = tool_runner
        self._procesando = False
        self._cancelado = False
        self._build()
        if tool_runner:
            self.lbl_modelo.config(text=tool_runner._client.model)

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

        self.stop_btn = tk.Button(
            input_bar,
            text="Detener",
            command=self._on_stop,
            bg="#c0392b",
            fg="#ffffff",
            activebackground="#a93226",
            activeforeground="#ffffff",
            font=theme.FONT_BOLD,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=16,
        )
        # oculto por defecto; se muestra al procesar

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def set_runner(self, runner):
        """Asigna el ToolRunner y muestra el modelo activo."""
        self._runner = runner
        self.lbl_modelo.config(text=runner._client.model)

    def set_archivo(self, nombre: str, total: int):
        """Notifica al runner y muestra el mensaje en consola."""
        if self._runner:
            self._runner.set_archivo(nombre, total)
        self._append(f"[Archivo: {nombre}  —  {total} elementos]\n", "info")

    def set_context(self, elementos: list, props: list):
        """Notifica al runner y muestra el elemento activo en consola."""
        if self._runner:
            self._runner.set_seleccion(elementos, props)
        if not elementos:
            return
        if len(elementos) == 1:
            info   = elementos[0].get_info()
            nombre = info.get("Name") or elementos[0].is_a()
            tipo   = elementos[0].is_a()
            self._append(f"[Elemento: {nombre}  {tipo}]\n", "info")
        else:
            nombres = ", ".join(
                (e.get_info().get("Name") or e.is_a()) for e in elementos[:3]
            )
            sufijo = f" y {len(elementos) - 3} más" if len(elementos) > 3 else ""
            self._append(f"[{len(elementos)} elementos: {nombres}{sufijo}]\n", "info")

    # ------------------------------------------------------------------
    # Envío y respuesta
    # ------------------------------------------------------------------
    def _on_stop(self):
        """Cancela la respuesta en curso y desbloquea la UI."""
        self._cancelado = True
        self._set_procesando(False)
        self._append("[Respuesta cancelada]\n", "info")

    def _on_send(self, event=None):
        if self._procesando:
            return
        texto = self.input.get().strip()
        if not texto:
            return
        if self._runner is None:
            self._append("Ollama no está configurado.\n", "error")
            return

        self.input.delete(0, tk.END)
        self._append(f"▶ {texto}\n", "usuario")
        self._set_procesando(True)
        self._cancelado = False
        threading.Thread(
            target=self._stream_respuesta,
            args=(texto,),
            daemon=True,
        ).start()

    def _stream_respuesta(self, prompt: str):
        root = self.frame.winfo_toplevel()
        primer_token = True

        def on_token(texto):
            nonlocal primer_token
            if self._cancelado:
                return
            if primer_token:
                root.after(0, lambda: self._append("", "ia"))
                primer_token = False
            root.after(0, lambda t=texto: self._append_token(t))

        def on_tool_call(nombre, _args):
            root.after(0, lambda n=nombre: self._append(f"[llamando a {n}...]\n", "info"))

        try:
            self._runner.chat(prompt, on_token, on_tool_call, lambda: self._cancelado)
        except Exception as e:
            root.after(0, lambda: self._append(f"Error: {e}\n", "error"))
        finally:
            if not self._cancelado:
                root.after(0, lambda: self._append("\n", "ia"))
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
        if valor:
            self.send_btn.pack_forget()
            self.stop_btn.pack(side=tk.RIGHT, padx=(0, 10), pady=8)
            self.input.config(state=tk.DISABLED)
        else:
            self.stop_btn.pack_forget()
            self.send_btn.pack(side=tk.RIGHT, padx=(0, 10), pady=8)
            self.input.config(state=tk.NORMAL)

    def append(self, text: str):
        """API de compatibilidad para añadir texto externo."""
        self._append(text + "\n", "ia")
