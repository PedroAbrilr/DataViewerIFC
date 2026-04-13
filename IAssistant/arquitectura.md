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
3. Al terminar, `root.after(0, ...)` llama a `TreePanel.load(nodos)` y actualiza la statusbar con el total de elementos.

### Selección de un elemento en el árbol
1. `TreePanel` captura `<<TreeviewSelect>>` y llama a `on_select(elemento)`.
2. `App._on_elemento_seleccionado()` llama a `IFCLoader.get_properties(elemento)`.
3. El resultado (lista de grupos PSet) se pasa a `PropsPanel.show(grupos)`.
4. La statusbar muestra nombre y tipo del elemento seleccionado.

### Consulta a la IA (pendiente)
1. `AIConsole._on_send()` recoge el texto del usuario.
2. Lanza hilo → `OllamaClient.stream(prompt, system=contexto_ifc)`.
3. Cada token llega a la UI con `root.after(0, append)`.

---

## Módulos clave

### `appcli.ui.theme`
- Define la paleta completa de colores (BG_DARK, BG_PANEL, ACCENT, etc.) y fuentes.
- Función `apply(root)` configura `ttk.Style` sobre el tema base `equilux` de `ttkthemes`.
- Todos los módulos UI importan `theme` para colores y fuentes — no hay valores hardcoded en los paneles.

### `appcli.ui.app.App`
- Usa `ThemedTk(theme="equilux")` como ventana raíz.
- Ensambla toolbar, layout principal (con márgenes) y statusbar.
- Única clase que coordina UI ↔ IFC ↔ IA.
- Gestiona threading para operaciones bloqueantes con `root.after()`.
- Statusbar muestra: elementos cargados · elemento activo · versión.

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
- Cabecera `CONSOLA IA` + área `tk.Text` (solo lectura) + barra de entrada.
- `append(text)` para añadir respuestas progresivas.
- `_on_send()` pendiente de conectar con `OllamaClient`.

### `appcli.ifc.loader.IFCLoader`
- `open(path)` → carga con `ifcopenshell.open()`.
- `get_tree()` → jerarquía espacial recursiva (`IsDecomposedBy` + `ContainsElements`).
- `get_properties(elemento)` → lista de grupos `{"pset", "props": [{"nombre","valor","unidad"}]}`.
  - Cubre `IfcPropertySet` y `IfcElementQuantity` (con unidades m, m², m³, kg).

### `appcli.ai.ollama_client.OllamaClient`
- `query(prompt)` → respuesta completa.
- `stream(prompt, system="")` → generador de fragmentos para streaming en UI.
- Modelo configurable en el constructor (por defecto `"llama3.2"`).

---

## Decisiones de diseño

- **Threading**: operaciones lentas en hilo secundario; resultados a la UI con `root.after(0, callback)`.
- **Coordinación en `App`**: los paneles no se conocen entre sí.
- **`theme.py` como única fuente de verdad visual**: colores y fuentes centralizados, sin valores hardcoded en los paneles.
- **`get_properties()` devuelve lista de grupos**, no dict plano, para la agrupación por PSet en la UI.
