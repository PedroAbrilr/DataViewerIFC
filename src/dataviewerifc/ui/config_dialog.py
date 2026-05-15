"""Ventana de configuración: backend IA y directorios del sistema."""

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import ollama as _ollama

from dataviewerifc import config as _config
from dataviewerifc.platform_support import get_platform
from dataviewerifc.ui import theme

MARGIN = 20

_MODELOS = {
    "ollama":  [],
    "claude":  ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5-20251001"],
    "openai":  ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    "gemini":  ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
}

_LABELS = {
    "ollama": "Ollama (local)",
    "claude": "Claude (Anthropic)",
    "openai": "ChatGPT (OpenAI)",
    "gemini": "Gemini (Google)",
}

_ENV_KEY = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

_CFG_KEY = {
    "claude": "anthropic_api_key",
    "openai": "openai_api_key",
    "gemini": "google_api_key",
}


def _dir_size(path: Path) -> str:
    if not path.exists():
        return ""
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    if total == 0:
        return "0 MB"
    mb = total / (1024 * 1024)
    return f"{mb:.1f} MB" if mb < 1024 else f"{mb / 1024:.1f} GB"


def _directorios() -> list[dict]:
    plat = get_platform()
    entradas = [
        {"label": "Configuración",  "path": plat.config_dir},
    ]
    if plat.shortcut_path:
        entradas.append({"label": "Acceso directo", "path": plat.shortcut_path})

    for e in entradas:
        p = e["path"]
        e["existe"] = p.exists()
        e["size"] = _dir_size(p) if p.is_dir() else ""
        e["path_str"] = str(p)

    return entradas


def pedir_api_key(parent, backend_id: str) -> str | None:
    """Muestra un diálogo modal que pide la API key. Devuelve la clave o None si cancela."""
    env_var = _ENV_KEY.get(backend_id, "API_KEY")
    nombre = _LABELS.get(backend_id, backend_id)

    resultado = {"key": None}

    dlg = tk.Toplevel(parent)
    dlg.title("Credencial requerida")
    dlg.geometry("440x200")
    dlg.resizable(False, False)
    dlg.configure(bg=theme.BG_PANEL)
    dlg.transient(parent)
    dlg.grab_set()

    tk.Label(
        dlg,
        text=f"Se necesita la clave de API para {nombre}.",
        bg=theme.BG_PANEL, fg=theme.FG_PRIMARY, font=theme.FONT_BOLD,
        wraplength=400,
    ).pack(anchor="w", padx=MARGIN, pady=(20, 4))

    tk.Label(
        dlg,
        text=f"Se guardará en {get_platform().config_dir_display}/config.json\ny no se incluirá en la distribución.",
        bg=theme.BG_PANEL, fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
        wraplength=400, justify="left",
    ).pack(anchor="w", padx=MARGIN)

    frame_entry = tk.Frame(dlg, bg=theme.BG_PANEL)
    frame_entry.pack(fill=tk.X, padx=MARGIN, pady=(12, 0))

    tk.Label(
        frame_entry, text=f"{env_var}:",
        bg=theme.BG_PANEL, fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
    ).pack(anchor="w")

    var_key = tk.StringVar()
    entry = tk.Entry(
        frame_entry, textvariable=var_key, show="•", width=48,
        bg=theme.BG_SURFACE, fg=theme.FG_PRIMARY, insertbackground=theme.FG_PRIMARY,
        font=theme.FONT_MONO, relief="flat", bd=4,
    )
    entry.pack(fill=tk.X, pady=(4, 0))
    entry.focus_set()

    frame_btn = tk.Frame(dlg, bg=theme.BG_PANEL)
    frame_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=MARGIN, pady=14)

    def _aceptar():
        clave = var_key.get().strip()
        if clave:
            resultado["key"] = clave
            dlg.destroy()

    def _cancelar():
        dlg.destroy()

    entry.bind("<Return>", lambda _: _aceptar())

    theme.make_button(frame_btn, "Aceptar", _aceptar).pack(side=tk.RIGHT)
    theme.make_button(
        frame_btn, "Cancelar", _cancelar, variant="surface",
    ).pack(side=tk.RIGHT, padx=(0, 8))

    dlg.wait_window()
    return resultado["key"]


class ConfigDialog:
    def __init__(self, parent, app):
        self._app = app
        self._dlg = tk.Toplevel(parent)
        self._dlg.title("Configuración")
        self._dlg.geometry("540x560")
        self._dlg.resizable(False, False)
        self._dlg.configure(bg=theme.BG_PANEL)
        self._dlg.transient(parent)
        self._dlg.grab_set()
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        dlg = self._dlg
        cfg = _config.load()

        # ---- Sección IA ----
        tk.Label(
            dlg, text="Asistente IA",
            bg=theme.BG_PANEL, fg=theme.FG_HEADING, font=theme.FONT_BOLD,
        ).pack(anchor="w", padx=MARGIN, pady=(18, 6))

        frame_ia = tk.Frame(dlg, bg=theme.BG_SURFACE, padx=14, pady=12)
        frame_ia.pack(fill=tk.X, padx=MARGIN)

        var_backend = tk.StringVar(value=self._app._backend_id)
        var_modelo = tk.StringVar()

        frame_radios = tk.Frame(frame_ia, bg=theme.BG_SURFACE)
        frame_radios.pack(fill=tk.X)

        for bid, label in _LABELS.items():
            tk.Radiobutton(
                frame_radios, text=label,
                variable=var_backend, value=bid,
                bg=theme.BG_SURFACE, fg=theme.FG_PRIMARY,
                selectcolor=theme.BG_PANEL, activebackground=theme.BG_SURFACE,
                font=theme.FONT_UI,
            ).pack(anchor="w", pady=1)

        tk.Label(
            frame_ia, text="Modelo:",
            bg=theme.BG_SURFACE, fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
        ).pack(anchor="w", pady=(10, 2))

        combo_modelo = ttk.Combobox(frame_ia, textvariable=var_modelo, state="readonly", width=40)
        combo_modelo.pack(anchor="w")

        lbl_aviso = tk.Label(
            frame_ia, text="",
            bg=theme.BG_SURFACE, fg="#e06c75", font=theme.FONT_SMALL, wraplength=460,
        )
        lbl_aviso.pack(anchor="w", pady=(4, 0))

        # --- Subsección Ollama: recrear modelo ---
        frame_ollama = tk.Frame(frame_ia, bg=theme.BG_SURFACE)
        frame_ollama.pack(fill=tk.X, pady=(10, 0))

        btn_recrear = theme.make_button(
            frame_ollama, "Recrear modelo ifc-assistant", None, variant="surface",
        )
        btn_recrear.pack(anchor="w")

        lbl_progreso = tk.Label(
            frame_ollama, text="",
            bg=theme.BG_SURFACE, fg=theme.FG_SECONDARY,
            font=theme.FONT_SMALL, wraplength=460, justify="left",
        )
        lbl_progreso.pack(anchor="w", pady=(4, 0))

        barra = ttk.Progressbar(
            frame_ollama, orient="horizontal", mode="determinate", maximum=100,
        )
        barra.pack(fill=tk.X, pady=(4, 0))
        barra.pack_forget()  # oculta hasta que se inicia la recreación

        # Mapa mensaje → porcentaje de progreso
        _PASOS = [
            ("iniciando ollama",            5),
            ("ollama iniciado",            15),
            ("eliminando modelo anterior", 20),
            ("aviso:",                     25),
            ("creando modelo",             75),
            ("gathering model",            77),
            ("using existing layer",       82),
            ("creating new layer",         82),
            ("copying",                    84),
            ("transferring",               86),
            ("writing manifest",           92),
            ("success",                    98),
        ]

        def _progreso_para(msg: str) -> int | None:
            m = msg.lower()
            for clave, valor in _PASOS:
                if clave in m:
                    return valor
            return None

        def _recrear_modelo():
            base = var_modelo.get()
            if not base:
                _actualizar_combo()
                base = var_modelo.get()
            if not base:
                lbl_progreso.config(
                    text="Selecciona un modelo base antes de recrear.", fg="#e06c75",
                )
                return

            btn_recrear.config(state=tk.DISABLED)
            barra["value"] = 0
            barra.pack(fill=tk.X, pady=(4, 0))
            lbl_progreso.config(text="Iniciando...", fg=theme.FG_SECONDARY)

            def on_status(msg):
                color = "#e06c75" if msg.lower().startswith("error") else theme.FG_SECONDARY
                pct = _progreso_para(msg)
                def _update(m=msg, c=color, p=pct):
                    lbl_progreso.config(text=m, fg=c)
                    if p is not None:
                        barra["value"] = p
                self._dlg.after(0, _update)

            def _run():
                ok = self._app.ollama.recrear_modelo(on_status=on_status, base_model=base)
                def _done():
                    btn_recrear.config(state=tk.NORMAL)
                    if ok:
                        barra["value"] = 100
                        lbl_progreso.config(text="Modelo listo.", fg=theme.ACCENT)
                    else:
                        barra.pack_forget()
                self._dlg.after(0, _done)

            threading.Thread(target=_run, daemon=True).start()

        btn_recrear.config(command=_recrear_modelo)

        def _mostrar_ocultar_ollama(*_):
            if var_backend.get() == "ollama":
                frame_ollama.pack(fill=tk.X, pady=(10, 0))
            else:
                frame_ollama.pack_forget()

        _arrancando_ollama = {"activo": False}

        def _arrancar_y_refrescar():
            _arrancando_ollama["activo"] = True
            ok = self._app.ollama.iniciar_servidor()
            def _done():
                _arrancando_ollama["activo"] = False
                if ok:
                    _actualizar_combo()
                else:
                    lbl_aviso.config(text="Ollama no disponible. Asegúrate de que está instalado y corriendo.")
            self._dlg.after(0, _done)

        def _actualizar_combo(*_):
            bid = var_backend.get()
            modelos = list(_MODELOS.get(bid, []))
            if bid == "ollama":
                try:
                    modelos = [m.model for m in _ollama.list().models]
                    lbl_aviso.config(text="")
                except Exception:
                    modelos = []
                    if not _arrancando_ollama["activo"]:
                        lbl_aviso.config(text="Iniciando Ollama...")
                        threading.Thread(target=_arrancar_y_refrescar, daemon=True).start()
                    else:
                        lbl_aviso.config(text="Iniciando Ollama...")
            combo_modelo["values"] = modelos
            modelo_actual = {
                "ollama":  cfg.get("ollama_base_model", ""),
                "claude":  cfg.get("claude_model",  "claude-sonnet-4-6"),
                "openai":  cfg.get("openai_model",  "gpt-4o-mini"),
                "gemini":  cfg.get("gemini_model",  "gemini-2.0-flash"),
            }.get(bid, modelos[0] if modelos else "")
            var_modelo.set(modelo_actual if modelo_actual in modelos else (modelos[0] if modelos else ""))

            if bid != "ollama":
                backend_tmp = self._app._crear_backend(bid, {
                    "claude_model": var_modelo.get(),
                    "openai_model": var_modelo.get(),
                    "gemini_model": var_modelo.get(),
                })
                ok, msg = backend_tmp.is_available()
                lbl_aviso.config(text=msg if not ok else "")

        for child in frame_radios.winfo_children():
            child.config(command=lambda: (_actualizar_combo(), _mostrar_ocultar_ollama()))

        _actualizar_combo()
        _mostrar_ocultar_ollama()

        # ---- Sección directorios ----
        tk.Label(
            dlg, text="Directorios del sistema",
            bg=theme.BG_PANEL, fg=theme.FG_HEADING, font=theme.FONT_BOLD,
        ).pack(anchor="w", padx=MARGIN, pady=(20, 6))

        frame_dirs = tk.Frame(dlg, bg=theme.BG_SURFACE, padx=14, pady=12)
        frame_dirs.pack(fill=tk.X, padx=MARGIN)
        frame_dirs.columnconfigure(1, weight=1)

        for row_i, entry in enumerate(_directorios()):
            color_estado = theme.FG_PRIMARY if entry["existe"] else "#e06c75"
            estado_txt = "✓" if entry["existe"] else "✗"

            tk.Label(
                frame_dirs, text=entry["label"],
                bg=theme.BG_SURFACE, fg=theme.FG_SECONDARY, font=theme.FONT_SMALL,
                anchor="w", width=16,
            ).grid(row=row_i, column=0, sticky="w", pady=3)

            tk.Label(
                frame_dirs, text=entry["path_str"],
                bg=theme.BG_SURFACE, fg=theme.FG_PRIMARY, font=theme.FONT_MONO,
                anchor="w",
            ).grid(row=row_i, column=1, sticky="w", padx=(6, 0))

            info = estado_txt
            if entry["size"]:
                info += f"  {entry['size']}"
            tk.Label(
                frame_dirs, text=info,
                bg=theme.BG_SURFACE, fg=color_estado, font=theme.FONT_SMALL,
                anchor="e", width=10,
            ).grid(row=row_i, column=2, sticky="e", padx=(6, 0))

        # ---- Botones ----
        frame_btn = tk.Frame(dlg, bg=theme.BG_PANEL)
        frame_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=MARGIN, pady=16)

        def _aplicar():
            bid = var_backend.get()
            modelo = var_modelo.get()
            cfg_actual = _config.load()

            # Si el backend necesita API key y no la tiene, pedirla ahora
            if bid in _ENV_KEY and not os.environ.get(_ENV_KEY[bid]) and not cfg_actual.get(_CFG_KEY[bid]):
                clave = pedir_api_key(self._dlg, bid)
                if not clave:
                    return  # el usuario canceló
                os.environ[_ENV_KEY[bid]] = clave
                cfg_actual[_CFG_KEY[bid]] = clave

            cfg_actual["active_backend"] = bid
            if bid == "ollama":
                cfg_actual["ollama_base_model"] = modelo
            else:
                cfg_actual[f"{bid}_model"] = modelo
            _config.save(cfg_actual)
            nuevo_backend = self._app._crear_backend(bid, cfg_actual)

            self._app._backend_id = bid
            self._app.backend = nuevo_backend
            self._app.tool_runner.backend = nuevo_backend
            self._app.ai_console.set_runner(self._app.tool_runner)

            if bid == "ollama":
                self._app._iniciar_ollama()

            self._dlg.destroy()

        theme.make_button(frame_btn, "Aplicar", _aplicar).pack(side=tk.RIGHT)
        theme.make_button(
            frame_btn, "Cancelar", self._dlg.destroy, variant="surface",
        ).pack(side=tk.RIGHT, padx=(0, 8))
