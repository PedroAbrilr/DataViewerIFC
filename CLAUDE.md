# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos habituales

```bash
# Activar entorno
source .venv/bin/activate

# Lanzar la aplicación (para probar o mostrar)
.venv/bin/python src/appcli/main.py

# Instalar dependencias
.venv/bin/pip install -e ".[dev]"

# Ejecutar tests
.venv/bin/pytest

# Generar wheel de distribución (solo cuando se pida explícitamente)
python -m build --wheel
```

## Lanzar la aplicación

Cuando el usuario pida mostrar, probar o lanzar la aplicación, usar siempre **Python directamente** (`src/appcli/main.py`). El wheel solo se genera cuando se pide explícitamente.

## Arquitectura

Tres capas: `appcli.ui` (Tkinter) → `appcli.ifc` (ifcopenshell) y `appcli.ai` (ollama). La UI no importa directamente `ifcopenshell` ni `ollama`; todo acceso pasa por `IFCLoader` y `OllamaClient`.

`App` es la única clase que coordina los tres paneles y las dos capas de datos. Los paneles no se conocen entre sí.

Las operaciones bloqueantes (carga IFC, consultas Ollama) se ejecutan en hilos secundarios y devuelven resultados a la UI con `root.after(0, callback)`.

## Módulos principales

- `ui/theme.py` — paleta de colores y fuentes, única fuente de verdad visual. Todos los módulos UI importan de aquí.
- `ui/app.py` — ventana principal (`ThemedTk` + tema `equilux`), toolbar, statusbar y coordinación.
- `ui/tree_panel.py` — árbol jerárquico IFC (`ttk.Treeview`), emite `on_select(elemento)`.
- `ui/props_panel.py` — tabla de propiedades agrupadas por PSet, tres columnas: Propiedad · Valor · Unidad.
- `ui/ai_console.py` — consola IA con área de texto y barra de entrada.
- `ifc/loader.py` — `IFCLoader`: `open()`, `get_tree()`, `get_properties()`.
- `ai/ollama_client.py` — `OllamaClient`: `query()` y `stream()`.

## Distribución

El wheel se genera con `python -m build --wheel` y queda en `dist/`. Incluye el binario portable de Ollama (`appcli/bin/ollama`), el `Modelfile` y el manual de usuario (`appcli/data/`). El tag de plataforma es `linux_x86_64` (configurado en `setup.cfg`). Los modelos de Ollama (`models/`) no se incluyen.

## Control de versiones

Los mensajes de commit comienzan con la fecha en formato `aammdd` al inicio de la primera línea: `260413 Descripción del cambio`.
