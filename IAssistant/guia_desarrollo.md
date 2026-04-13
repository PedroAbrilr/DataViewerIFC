# Guía de desarrollo

## Activar el entorno y arrancar la app

```bash
source .venv/bin/activate
python -m appcli          # usando el punto de entrada del paquete
# o bien:
python src/appcli/main.py
```

## Instalar dependencias

Las dependencias están declaradas en `pyproject.toml`. El paquete está instalado en modo editable:

```bash
.venv/bin/pip install -e .
```

Dependencias principales:
- `ifcopenshell` — lectura y navegación de archivos IFC
- `ollama` — cliente Python para Ollama corriendo en local (`http://localhost:11434`)

## Requisito externo: Ollama

La consola de IA requiere que **Ollama esté corriendo en local** con al menos un modelo descargado. El modelo por defecto en `OllamaClient` es `llama3.2`.

```bash
ollama serve          # iniciar el servidor
ollama pull llama3.2  # descargar el modelo si no está disponible
```

## Próximos pasos de implementación (orden sugerido)

1. **`IFCLoader.open()`** — cargar archivo con `ifcopenshell.open(path)`.
2. **`IFCLoader.get_tree()`** — recorrer la jerarquía espacial IFC (`IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey → elementos`).
3. **`TreePanel.load()`** — poblar el `ttk.Treeview` con la jerarquía.
4. **Evento de selección en `TreePanel`** — binding `<<TreeviewSelect>>` + callback hacia `App`.
5. **`IFCLoader.get_properties()`** — extraer propiedades con `element.get_info()` y `IfcPropertySet`.
6. **`PropsPanel.show()`** — ya implementado, conectar con el evento de selección.
7. **`OllamaClient.stream()`** — llamada a `ollama.chat()` con `stream=True`.
8. **`AIConsole._on_send()`** — lanzar la consulta en un hilo y hacer streaming hacia `append()`.
9. **Diálogo de apertura de archivo** — `tkinter.filedialog.askopenfilename()` en `App`.

## Consideraciones para threading

Las operaciones lentas (carga de IFC, consultas a Ollama) deben ejecutarse fuera del hilo principal de Tkinter. Patrón recomendado:

```python
import threading

def _cargar_ifc_en_hilo(path):
    # en hilo secundario
    modelo = loader.open(path)
    root.after(0, lambda: tree_panel.load(modelo))

threading.Thread(target=_cargar_ifc_en_hilo, args=(path,), daemon=True).start()
```
