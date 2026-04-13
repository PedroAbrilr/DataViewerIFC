# Arquitectura del proyecto

## Capas y responsabilidades

El proyecto sigue una separación en tres capas:

```
┌─────────────────────────────────────┐
│           UI  (appcli.ui)           │  Presentación y eventos de usuario
├─────────────────────────────────────┤
│    IFC (appcli.ifc)                 │  Acceso y transformación del modelo IFC
│    AI  (appcli.ai)                  │  Comunicación con Ollama
└─────────────────────────────────────┘
```

La capa UI **no importa directamente** `ifcopenshell` ni `ollama`. Todo acceso a esas librerías pasa por `IFCLoader` y `OllamaClient` respectivamente.

---

## Flujo de datos esperado

### Apertura de un archivo IFC

1. El usuario selecciona un `.ifc` (mediante diálogo de archivo, a implementar en `app.py`).
2. `App` llama a `IFCLoader.open(path)` → devuelve el modelo.
3. `App` llama a `IFCLoader.get_tree()` → estructura jerárquica de elementos.
4. `App` pasa el resultado a `TreePanel.load(ifc_model)` → puebla el `ttk.Treeview`.

### Selección de un elemento en el árbol

1. El usuario hace clic en un nodo del árbol (`TreePanel`).
2. `TreePanel` emite un evento (callback o binding Tkinter) con el elemento seleccionado.
3. `App` recibe el evento, llama a `IFCLoader.get_properties(element)` → dict de propiedades.
4. `App` llama a `PropsPanel.show(properties)` → actualiza la tabla.

### Consulta a la IA

1. El usuario escribe en el campo de entrada de `AIConsole` y pulsa Enter o "Enviar".
2. `AIConsole._on_send()` recopila el texto y lo pasa a `OllamaClient.stream(prompt)`.
3. Los tokens se van añadiendo al área de texto mediante `AIConsole.append()`.

---

## Módulos clave

### `appcli.ui.app.App`
- Clase central que ensambla la UI.
- Posee referencias a `TreePanel`, `PropsPanel` y `AIConsole`.
- Es la única clase que coordina las tres capas.
- Layout: `PanedWindow` horizontal (árbol + propiedades) encima, consola debajo.

### `appcli.ui.tree_panel.TreePanel`
- Envuelve un `ttk.Treeview`.
- Método `load(ifc_model)` → construye la jerarquía desde el modelo IFC.
- Debe emitir eventos al seleccionar un nodo (pendiente de implementar).

### `appcli.ui.props_panel.PropsPanel`
- Envuelve un `ttk.Treeview` en modo tabla (dos columnas: propiedad / valor).
- Método `show(properties: dict)` → limpia y recarga las filas.

### `appcli.ui.ai_console.AIConsole`
- `tk.Text` (solo lectura) para mostrar el historial.
- `ttk.Entry` para la entrada del usuario.
- Método `append(text)` para añadir respuestas progresivas (streaming).
- `_on_send()` es el punto de extensión para conectar con `OllamaClient`.

### `appcli.ifc.loader.IFCLoader`
- Abstrae `ifcopenshell`.
- `open(path)` → carga el archivo `.ifc`.
- `get_tree()` → devuelve la jerarquía (a definir: lista anidada, dict, o nodos propios).
- `get_properties(element)` → devuelve `dict[str, Any]`.

### `appcli.ai.ollama_client.OllamaClient`
- Abstrae la librería `ollama`.
- `query(prompt)` → respuesta completa como `str`.
- `stream(prompt)` → generador de tokens `str` para actualización progresiva de la UI.
- Modelo configurable en el constructor (por defecto `"llama3.2"`).

---

## Decisiones de diseño a tener en cuenta

- **Tkinter es single-thread**: las llamadas bloqueantes (Ollama, lectura de IFC grandes) deben ejecutarse en hilos separados (`threading.Thread`) y comunicar resultados a la UI mediante `root.after()` o una cola (`queue.Queue`).
- **Coordinación en `App`**: los paneles no se conocen entre sí; toda comunicación pasa por `App`. Esto facilita el mantenimiento y evita acoplamiento.
- **ifcopenshell**: los objetos IFC son instancias de clases generadas dinámicamente por la librería. Las propiedades se obtienen mediante `element.get_info()` o recorriendo `IfcPropertySet`.
