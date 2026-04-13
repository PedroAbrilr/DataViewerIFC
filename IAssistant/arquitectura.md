# Arquitectura del proyecto

## Capas y responsabilidades

```
┌─────────────────────────────────────┐
│           UI  (appcli.ui)           │  Presentación y eventos de usuario
├─────────────────────────────────────┤
│    IFC (appcli.ifc)                 │  Acceso y transformación del modelo IFC
│    AI  (appcli.ai)                  │  Comunicación con Ollama
└─────────────────────────────────────┘
```

La capa UI no importa directamente `ifcopenshell` ni `ollama`. Todo acceso pasa por `IFCLoader` y `OllamaClient`.

---

## Flujo de datos

### Apertura de un archivo IFC
1. Botón `Abrir IFC` (toolbar) lanza `filedialog.askopenfilename()` en `App`.
2. `App` abre un hilo secundario → `IFCLoader.open(path)` + `get_tree()`.
3. Al terminar, `root.after(0, ...)` llama a `TreePanel.load(nodos)`, actualiza la statusbar y llama a `AIConsole.set_archivo(nombre, total)`.

### Selección de un elemento en el árbol
1. `TreePanel` captura `<<TreeviewSelect>>` y llama a `on_select(elemento)`.
2. `App._on_elemento_seleccionado()` llama a `IFCLoader.get_properties(elemento)`.
3. El resultado (lista de grupos PSet) se pasa a `PropsPanel.show(grupos)`.
4. Se llama a `AIConsole.set_context(elemento, props)` para actualizar el contexto de la IA.
5. La statusbar muestra nombre y tipo del elemento seleccionado.

### Consulta a la IA
1. `AIConsole._on_send()` recoge el texto del usuario.
2. Construye el system prompt: instrucciones base + contexto del archivo + contexto del elemento seleccionado.
3. Lanza hilo → `OllamaClient.stream(prompt, system=system_prompt)`.
4. Cada token llega a la UI con `root.after(0, append_token)`.

### Arranque de Ollama (al iniciar la app)
1. `App._iniciar_ollama()` lanza un hilo con `OllamaClient.ensure_running()`.
2. `ensure_running()` comprueba si Ollama responde (`ping`), lo arranca si no.
3. Descarga `qwen2.5:1.5b` si no está disponible.
4. Crea el modelo `ifc-assistant` si no existe: lee `appcli/data/Modelfile`, sustituye `{{MANUAL_USUARIO}}` con `appcli/data/manual_usuario.md`, escribe un temporal y ejecuta `ollama create`.

---

## Módulos clave

### `appcli.ui.theme`
- Define la paleta completa de colores (BG_DARK, BG_PANEL, ACCENT, etc.) y fuentes.
- Función `apply(root)` configura `ttk.Style` sobre el tema base `equilux` de `ttkthemes`.
- Todos los módulos UI importan `theme` — no hay valores hardcoded en los paneles.

### `appcli.ui.app.App`
- Usa `ThemedTk(theme="equilux")` como ventana raíz.
- Ensambla toolbar, layout principal (con márgenes) y statusbar.
- Única clase que coordina UI ↔ IFC ↔ IA.
- Gestiona threading para operaciones bloqueantes con `root.after()`.

### `appcli.ui.tree_panel.TreePanel(parent, on_select=None)`
- Cabecera fija `ESTRUCTURA` + `ttk.Treeview` con scrollbar.
- `load(nodos)` puebla el árbol desde la lista devuelta por `get_tree()`.
- Mantiene `_elementos: dict[iid → elemento IFC]` para recuperar el objeto al seleccionar.

### `appcli.ui.props_panel.PropsPanel`
- Cabecera fija `PROPIEDADES` + `ttk.Treeview` en modo árbol+columnas.
- `show(grupos)` acepta la lista de grupos de `get_properties()`.
- PSets como nodos padre con tag `"pset"` (fondo y fuente diferenciados).
- Columnas: Propiedad · Valor · Unidad.

### `appcli.ui.ai_console.AIConsole`
- Cabecera `CONSOLA IA` + modelo activo + área `tk.Text` (solo lectura) + barra de entrada.
- `set_archivo(nombre, total)` — actualiza el contexto del archivo IFC abierto.
- `set_context(elemento, props)` — actualiza el contexto del elemento seleccionado.
- El system prompt se construye dinámicamente en `_on_send()` concatenando las dos variables de contexto.
- Streaming: tokens llegan desde el hilo a la UI con `root.after(0, lambda f=fragmento: _append_token(f))`.
- Orden de empaquetado Tkinter: `input_bar` se empaqueta con `side=BOTTOM` **antes** que `output` con `expand=True` para evitar que quede cubierto.

### `appcli.ifc.loader.IFCLoader`
- `open(path)` → carga con `ifcopenshell.open()`.
- `get_tree()` → jerarquía espacial recursiva (`IsDecomposedBy` + `ContainsElements`).
- `get_properties(elemento)` → lista de grupos `{"pset", "props": [{"nombre","valor","unidad"}]}`.
  - Cubre `IfcPropertySet` y `IfcElementQuantity` (con unidades m, m², m³, kg).

### `appcli.ai.ollama_client.OllamaClient`
- Rutas portables: `_PKG_DIR = Path(__file__).parent.parent` (apunta a `src/appcli/`).
  - Binario: `_PKG_DIR / "bin" / "ollama"` (usa sistema si no existe).
  - Modelos: `_PKG_DIR.parents[1] / "models"` (directorio junto al paquete instalado).
  - Modelfile y manual: `_PKG_DIR / "data" / *`.
- `ensure_running()`: arranca Ollama → descarga modelo base → crea `ifc-assistant` con sustitución del manual.
- `query(prompt, system)` → respuesta completa.
- `stream(prompt, system)` → generador de fragmentos para streaming en UI.
- Modelo activo: `ifc-assistant` (creado sobre `qwen2.5:1.5b`).

---

## Modelo de IA: `ifc-assistant`

El modelo personalizado se crea dinámicamente al arrancar la app si no existe:

```
Modelfile (plantilla)
  FROM qwen2.5:1.5b
  PARAMETER temperature 0.3 / top_p 0.9 / num_ctx 8192
  SYSTEM """
    Eres el asistente de AppCLI...
    ## Manual de la aplicación
    {{MANUAL_USUARIO}}   ← sustituido con docs/manual_usuario.md
    ## Conocimientos especializados
    ...IFC, BIM, PSets...
  """
```

El system prompt dinámico de cada consulta añade encima:
```
[instrucciones del Modelfile — fijas]
Archivo IFC abierto: nombre.ifc (N elementos)
Elemento seleccionado: ...nombre, tipo, propiedades...
```

---

## Decisiones de diseño

- **Threading**: operaciones lentas en hilo secundario; resultados a la UI con `root.after(0, callback)`.
- **Coordinación en `App`**: los paneles no se conocen entre sí.
- **`theme.py` como única fuente de verdad visual**: colores y fuentes centralizados.
- **`get_properties()` devuelve lista de grupos**, no dict plano, para la agrupación por PSet en la UI.
- **Ollama portable**: el binario y los modelos viven dentro del proyecto; `OLLAMA_MODELS` se sobreescribe con `env_portable()` solo cuando se usa el binario local.
- **Modelfile como plantilla**: el placeholder `{{MANUAL_USUARIO}}` se resuelve en tiempo de creación del modelo, no en cada consulta. Para actualizar el manual basta con borrar `ifc-assistant` y relanzar la app.
