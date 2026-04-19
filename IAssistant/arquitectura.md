# Arquitectura del proyecto

## Capas y responsabilidades

```
┌─────────────────────────────────────┐
│           UI  (appcli.ui)           │  Presentación y eventos de usuario
├─────────────────────────────────────┤
│    IFC (appcli.ifc)                 │  Acceso y transformación del modelo IFC
│    AI  (appcli.ai)                  │  Backends IA y tool calling
└─────────────────────────────────────┘
```

La capa UI no importa directamente `ifcopenshell` ni `ollama`. Todo acceso pasa por `IFCLoader`, `OllamaClient` y los backends.

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

### Consulta a la IA (con tool calling)
```
Usuario escribe → AIConsole → ToolRunner.chat()
    │
    ├─ System prompt: base + archivo IFC + elemento seleccionado
    ├─ Tools: 8 herramientas IFC + obtener_seleccion (si hay selección)
    │          + 2 herramientas de app (AppTools)
    │
    └─ Bucle (no-streaming):
         Backend → tool_calls? → IFCTools.ejecutar() o AppTools.ejecutar()
                               → si _last_ids → on_seleccionar(ids) → tree_panel.select_by_ids()
                               → añadir resultado → Backend → …
         Sin tool_calls → respuesta final en streaming → on_token()
```

### Sincronización de selección árbol ↔ IA
Cuando `IFCTools.ejecutar()` devuelve una lista de elementos, `_fmt_lista()` guarda los GlobalIds en `_last_ids`. Tras la ejecución, `ToolRunner._ejecutar()` comprueba `_last_ids` y llama a `on_seleccionar(ids)`, que ha sido asignado en `App._actualizar_arbol()` como:
```
lambda ids: root.after(0, lambda i=ids: tree_panel.select_by_ids(i))
```
`TreePanel.select_by_ids()` usa el diccionario `_gid_to_iid` (construido en la carga del árbol) para traducir GlobalIds a items del Treeview.

### Arranque de Ollama
1. `App._iniciar_ollama()` lanza un hilo con `OllamaClient.ensure_running()`.
2. `ensure_running()` fija `OLLAMA_MODELS` al directorio `ollama/models/` junto al binario.
3. Comprueba si Ollama responde (`ping`), lo arranca si no.
4. Descarga el modelo base si no está disponible.
5. Crea `ifc-assistant` si no existe: lee `appcli/data/Modelfile`, sustituye `{{MANUAL_USUARIO}}`, escribe temporal y ejecuta `ollama create`.

### Cambio de backend IA
1. Usuario abre **⚙ Configuración** → selecciona backend y modelo.
2. Si el backend requiere API key y no está guardada, aparece diálogo emergente.
3. La clave se guarda en `config.json` y se inyecta en `os.environ`.
4. `App` recibe el nuevo backend, actualiza `tool_runner` y el label de la consola.

---

## Módulos clave

### `appcli.ui.app.App`
- Usa `ThemedTk(theme="equilux")` como ventana raíz.
- Ensambla toolbar (Abrir IFC + ⚙ Configuración), layout principal y statusbar.
- Única clase que coordina UI ↔ IFC ↔ IA.
- Gestiona threading para operaciones bloqueantes con `root.after()`.
- Al arrancar: llama a `config.inject_env()` para inyectar API keys en el entorno.

### `appcli.ui.config_dialog.ConfigDialog`
- Ventana modal con tres secciones: **Asistente IA**, **Directorios del sistema**.
- Selector de backend (radio) + combobox de modelo.
- Llama a `pedir_api_key()` si el backend elegido no tiene clave guardada.
- Al aplicar: guarda en `config.json`, inyecta en `os.environ`, actualiza `App.backend` y el label de la consola.

### `appcli.ui.ai_console.AIConsole`
- Cabecera `CONSOLA IA` + backend activo (`lbl_modelo`) + área `tk.Text` + barra de entrada.
- `set_runner(runner)` — actualiza el runner y el label del backend.
- `set_archivo(nombre, total)` — actualiza el contexto del archivo IFC abierto.
- `set_context(elemento, props)` — actualiza el contexto del elemento seleccionado.

### `appcli.ai.ollama_client.OllamaClient`
- `_ollama_bin()`: busca en `APPCLI_OLLAMA_BIN` → `~/.local/share/appcli/ollama/ollama` → sistema.
- `_prepare_models_dir()`: deriva `models/` junto al binario y fija `OLLAMA_MODELS`.
- `ensure_running()`: arranca Ollama → descarga modelo base → crea `ifc-assistant`.

### `appcli.config`
- `load()` / `save()` — lee y escribe `~/.config/appcli/config.json`.
- `inject_env()` — inyecta `anthropic_api_key` y `openai_api_key` en `os.environ`.

### `appcli.ui.theme`
- Paleta completa de colores y fuentes. Función `apply(root)` configura `ttk.Style`.
- Todos los módulos UI importan `theme` — no hay valores hardcoded en los paneles.

### `appcli.ifc.loader.IFCLoader`
- `open(path)` → carga con `ifcopenshell.open()`.
- `get_tree()` → jerarquía espacial recursiva (`IsDecomposedBy` + `ContainsElements`).
- `get_properties(elemento)` → lista de grupos `{"pset", "props": [{"nombre","valor","unidad"}]}`.

---

## Herramientas disponibles en la consola IA

### Herramientas IFC (`IFCTools`)

| Herramienta | Cuándo la usa el modelo | Actualiza selección |
|---|---|---|
| `obtener_seleccion(modo)` | Preguntas sobre el elemento activo | No |
| `buscar_elementos` | Listar elementos de un tipo IFC | Sí |
| `contar_elementos` | Contar elementos de un tipo | No |
| `obtener_propiedades` | Propiedades por GlobalId | No |
| `listar_plantas` | Plantas del edificio | No |
| `elementos_de_planta` | Elementos de una planta concreta | Sí |
| `calcular_area_total` | Suma de áreas por tipo | No |
| `buscar_por_nombre` | Búsqueda por nombre parcial | Sí |
| `filtrar_por_propiedad` | Filtrar por valor de propiedad (modelo o selección) | Sí |

### Herramientas de aplicación (`AppTools`)

| Herramienta | Cuándo la usa el modelo |
|---|---|
| `estado_app` | Consultar qué archivo está abierto |
| `cargar_ifc` | Abrir un archivo IFC por nombre |

---

## Decisiones de diseño

- **Threading**: operaciones lentas en hilo secundario; resultados a la UI con `root.after(0, callback)`.
- **Coordinación en `App`**: los paneles no se conocen entre sí.
- **`theme.py` como única fuente de verdad visual**: colores y fuentes centralizados.
- **Credenciales en config.json**: las API keys se guardan localmente y se inyectan en `os.environ` al arrancar; nunca se distribuyen en el wheel.
- **Rutas de Ollama por entorno**: `APPCLI_OLLAMA_BIN` separa desarrollo (binario portable del proyecto) de producción (instalado por `appcli-install`). `OLLAMA_MODELS` se deriva automáticamente del binario activo.
- **Modelfile como plantilla**: el placeholder `{{MANUAL_USUARIO}}` se resuelve al crear el modelo, no en cada consulta. Para actualizar el manual basta con borrar `ifc-assistant` y relanzar la app.
- **`dev_bootstrap.py` fuera del paquete**: configura el entorno de desarrollo sin contaminar el código de producción.
