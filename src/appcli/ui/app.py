"""Ventana principal: organiza los tres paneles de la interfaz."""

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ttkthemes import ThemedTk

from appcli import config as _config
from appcli.ui import theme
from appcli.ui.tree_panel import TreePanel
from appcli.ui.props_panel import PropsPanel
from appcli.ui.ai_console import AIConsole
from appcli.ifc.loader import IFCLoader
from appcli.ai.ollama_client import OllamaClient
from appcli.ai.ifc_tools import IFCTools
from appcli.ai.tool_runner import ToolRunner
from appcli.ai.backends import OllamaBackend, ClaudeBackend, OpenAIBackend
from appcli.ui.config_dialog import ConfigDialog

MARGIN = 10


class App:
    def __init__(self):
        self.root = ThemedTk(theme="equilux")
        self.root.title("AppCLI — IFC Viewer")
        self.root.geometry("1280x860")
        self.loader = IFCLoader()
        self.ollama = OllamaClient()

        cfg = _config.load()
        _config.inject_env(cfg)
        self._backend_id = cfg.get("active_backend", "ollama")
        self.backend = self._crear_backend(self._backend_id, cfg)
        self.tool_runner = ToolRunner(self.backend)

        theme.apply(self.root)
        self._build_toolbar()
        self._build_statusbar()
        self._build_layout()
        self._iniciar_ia()

    # ------------------------------------------------------------------
    # Creación de backend
    # ------------------------------------------------------------------
    def _crear_backend(self, backend_id: str, cfg: dict):
        if backend_id == "claude":
            return ClaudeBackend(model=cfg.get("claude_model", "claude-sonnet-4-6"))
        if backend_id == "openai":
            return OpenAIBackend(model=cfg.get("openai_model", "gpt-4o-mini"))
        return OllamaBackend(model=cfg.get("ollama_model", "ifc-assistant"))

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=theme.BG_DARK, height=44)
        bar.pack(fill=tk.X, side=tk.TOP, padx=0, pady=0)
        bar.pack_propagate(False)

        btn_open = tk.Button(
            bar,
            text="  Abrir IFC",
            command=self._abrir_ifc,
            bg=theme.ACCENT,
            fg="#ffffff",
            activebackground="#3a82d6",
            activeforeground="#ffffff",
            font=theme.FONT_BOLD,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=6,
        )
        btn_open.pack(side=tk.LEFT, padx=(MARGIN, 0), pady=7)

        self.lbl_archivo = tk.Label(
            bar,
            text="Sin archivo cargado",
            bg=theme.BG_DARK,
            fg=theme.FG_SECONDARY,
            font=theme.FONT_SMALL,
        )
        self.lbl_archivo.pack(side=tk.LEFT, padx=14)

        self.root.bind("<Control-o>", lambda e: self._abrir_ifc())

        # Botón de configuración (lado derecho)
        btn_cfg = tk.Button(
            bar,
            text="⚙  Configuración",
            command=self._abrir_configuracion,
            bg=theme.BG_SURFACE,
            fg=theme.FG_PRIMARY,
            activebackground=theme.BG_HEADER,
            activeforeground=theme.FG_PRIMARY,
            font=theme.FONT_SMALL,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=6,
        )
        btn_cfg.pack(side=tk.RIGHT, padx=(0, MARGIN), pady=7)

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X)

    # ------------------------------------------------------------------
    # Ventana de configuración
    # ------------------------------------------------------------------
    def _abrir_configuracion(self):
        ConfigDialog(self.root, self)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------
    def _build_statusbar(self):
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, side=tk.BOTTOM)

        bar = tk.Frame(self.root, bg=theme.BG_DARK, height=26)
        bar.pack(fill=tk.X, side=tk.BOTTOM, padx=0)
        bar.pack_propagate(False)

        self.status_elementos = tk.Label(
            bar, text="",
            bg=theme.BG_DARK, fg=theme.FG_SECONDARY,
            font=theme.FONT_SMALL, anchor="w",
        )
        self.status_elementos.pack(side=tk.LEFT, padx=(MARGIN, 20))

        self.status_elemento_activo = tk.Label(
            bar, text="",
            bg=theme.BG_DARK, fg=theme.FG_SECONDARY,
            font=theme.FONT_SMALL, anchor="w",
        )
        self.status_elemento_activo.pack(side=tk.LEFT)

        self.status_modelo = tk.Label(
            bar, text="IFC Viewer  v0.1",
            bg=theme.BG_DARK, fg=theme.FG_SECONDARY,
            font=theme.FONT_SMALL, anchor="e",
        )
        self.status_modelo.pack(side=tk.RIGHT, padx=(0, MARGIN))

    # ------------------------------------------------------------------
    # Layout principal
    # ------------------------------------------------------------------
    def _build_layout(self):
        outer = tk.Frame(self.root, bg=theme.BG_DARK)
        outer.pack(fill=tk.BOTH, expand=True,
                   padx=MARGIN, pady=(MARGIN, MARGIN))

        top_paned = ttk.PanedWindow(outer, orient=tk.HORIZONTAL)
        top_paned.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self.tree_panel  = TreePanel(top_paned, on_select=self._on_elemento_seleccionado)
        self.props_panel = PropsPanel(top_paned)
        top_paned.add(self.tree_panel.frame,  weight=1)
        top_paned.add(self.props_panel.frame, weight=2)

        tk.Frame(outer, bg=theme.BORDER, height=1).pack(fill=tk.X, pady=(MARGIN, 0))

        self.ai_console = AIConsole(outer, tool_runner=self.tool_runner)
        self.ai_console.frame.pack(fill=tk.BOTH, expand=False,
                                   side=tk.BOTTOM, pady=(0, 0))

    # ------------------------------------------------------------------
    # Lógica de IA
    # ------------------------------------------------------------------
    def _iniciar_ia(self):
        if self._backend_id == "ollama":
            self._iniciar_ollama()

    def _iniciar_ollama(self):
        def _run():
            self.ollama.ensure_running(
                on_status=lambda msg: self.root.after(
                    0, lambda m=msg: self.ai_console.append(m)
                )
            )
        threading.Thread(target=_run, daemon=True).start()

    # ------------------------------------------------------------------
    # Carga de archivos IFC
    # ------------------------------------------------------------------
    def _abrir_ifc(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo IFC",
            filetypes=[("Archivos IFC", "*.ifc"), ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        self.lbl_archivo.config(text="Cargando…", fg=theme.FG_SECONDARY)
        self.status_elementos.config(text="")
        self.status_elemento_activo.config(text="")
        threading.Thread(target=self._cargar_ifc, args=(path,), daemon=True).start()

    def _cargar_ifc(self, path: str):
        try:
            self.loader.open(path)
            nodos = self.loader.get_tree()
            total = self._contar_elementos(nodos)
            self.root.after(0, lambda: self._actualizar_arbol(nodos, path, total))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error al cargar", str(e)))
            self.root.after(0, lambda: self.lbl_archivo.config(
                text="Error al cargar el archivo", fg="#e06c75"
            ))

    def _actualizar_arbol(self, nodos: list, path: str, total: int):
        self.tree_panel.load(nodos)
        nombre = path.split("/")[-1]
        self.root.title(f"AppCLI — {nombre}")
        self.lbl_archivo.config(text=nombre, fg=theme.FG_PRIMARY)
        self.status_elementos.config(text=f"{total} elementos cargados")
        self.tool_runner._ifc_tools = IFCTools(self.loader)
        self.ai_console.set_archivo(nombre, total)

    def _contar_elementos(self, nodos: list) -> int:
        total = 0
        for nodo in nodos:
            total += 1 + self._contar_elementos(nodo["hijos"])
        return total

    def _on_elemento_seleccionado(self, elementos):
        threading.Thread(
            target=self._cargar_propiedades,
            args=(elementos,),
            daemon=True,
        ).start()

    def _cargar_propiedades(self, elementos):
        elemento = elementos[-1]
        props_activo = self.loader.get_properties(elemento)
        if len(elementos) == 1:
            props = props_activo
        else:
            todos_props = [self.loader.get_properties(e) for e in elementos]
            props = self._merge_props(todos_props)
        self.root.after(0, lambda: self._actualizar_seleccion(elementos, elemento, props))

    def _actualizar_seleccion(self, elementos, elemento, props):
        self.props_panel.show(props)
        self.ai_console.set_context(elementos, props)
        nombre = elemento.get_info().get("Name") or elemento.is_a()
        tipo   = elemento.is_a()
        if len(elementos) > 1:
            self.status_elemento_activo.config(
                text=f"  ·  {len(elementos)} elementos seleccionados  (activo: {nombre}  [{tipo}])",
                fg=theme.FG_PRIMARY,
            )
        else:
            self.status_elemento_activo.config(
                text=f"  ·  {nombre}  [{tipo}]",
                fg=theme.FG_PRIMARY,
            )

    def _merge_props(self, todos_props: list) -> list:
        merged: dict = {}
        orden_psets: list = []
        for grupos in todos_props:
            for grupo in grupos:
                pset = grupo["pset"]
                if pset not in merged:
                    merged[pset] = {}
                    orden_psets.append(pset)
                for prop in grupo["props"]:
                    nombre = prop["nombre"]
                    if nombre not in merged[pset]:
                        merged[pset][nombre] = {"valores": set(), "unidades": set()}
                    merged[pset][nombre]["valores"].add(str(prop["valor"]))
                    merged[pset][nombre]["unidades"].add(str(prop["unidad"]))

        result = []
        for pset in orden_psets:
            props_list = []
            for nombre, data in merged[pset].items():
                varios  = len(data["valores"]) > 1
                valor   = list(data["valores"])[0] if not varios else "varios..."
                unidad  = list(data["unidades"])[0] if len(data["unidades"]) == 1 else ""
                props_list.append({
                    "nombre": nombre,
                    "valor":  valor,
                    "unidad": unidad,
                    "varios": varios,
                })
            result.append({"pset": pset, "props": props_list})
        return result

    def run(self):
        self.root.mainloop()
