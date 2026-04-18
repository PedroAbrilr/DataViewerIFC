# Contexto del proyecto: AppCLI — IFC Viewer con IA local y en la nube

## Qué es este proyecto

Aplicación de escritorio en Python para **explorar archivos IFC** (Industry Foundation Classes, el formato estándar de intercambio en BIM). El usuario abre un archivo `.ifc`, navega su jerarquía de elementos y consulta sus propiedades. Una consola integrada permite preguntas en lenguaje natural con soporte de **tool calling** y elección entre tres backends de IA.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.13 (Fedora Linux) |
| Interfaz gráfica | Tkinter (stdlib) + ttk + ttkthemes |
| Tema visual | equilux (oscuro, plano, moderno) |
| Lectura de IFC | ifcopenshell 0.8.4 |
| IA local | ollama 0.6.1 — modelo `ifc-assistant` sobre el modelo base elegido |
| IA en la nube | anthropic SDK (Claude) / openai SDK (ChatGPT) — opcionales |
| Tests | pytest |
| Empaquetado | setuptools + pyproject.toml |
| Distribución | wheel `py3-none-any` (`python -m build --wheel`) |
| Entorno virtual | `.venv/` en la raíz del proyecto |

## Estado actual del proyecto (260418)

- Carga de archivos IFC **implementada y funcional**.
- Árbol de jerarquía espacial **implementado y funcional**.
- Tabla de propiedades agrupada por PSet con columna de unidades **implementada**.
- Multiselección en el árbol con propiedades fusionadas **implementada**.
- Tema visual oscuro con `ttkthemes` (equilux) **aplicado**.
- Barra de herramientas con botón de backend IA **implementada**.
- Consola IA con streaming, tool calling y botón Detener **funcional**.
- **Tool calling IFC completamente implementado**: 8 herramientas activas.
- **Multi-backend IA implementado**:
  - `OllamaBackend` — modelo local, ifc-assistant personalizado
  - `ClaudeBackend` — Anthropic API (ANTHROPIC_API_KEY)
  - `OpenAIBackend` — OpenAI API (OPENAI_API_KEY)
  - Selector en toolbar con diálogo de cambio y aviso si falta API key
  - Configuración persistida en `~/.config/appcli/config.json`
- **Installer independiente** (`appcli-install`):
  - Descarga Ollama según OS/arquitectura a `~/.local/share/appcli/bin/`
  - Menú de selección de modelo base
  - Pull del modelo + creación de `ifc-assistant`
  - Guarda configuración y acceso directo de escritorio
- Wheel `py3-none-any` (sin binario Ollama embebido).
- Manual de usuario actualizado con multi-backend e instalador.

## Arquitectura de módulos

```
AppCLI/
└── src/appcli/
    ├── ui/
    │   ├── theme.py          # Paleta, fuentes y estilos ttk
    │   ├── app.py            # Ventana principal; toolbar con selector de backend
    │   ├── tree_panel.py     # Árbol jerárquico IFC (multiselección)
    │   ├── props_panel.py    # Tabla de propiedades por PSet
    │   └── ai_console.py     # Consola IA — delega en ToolRunner
    ├── ifc/
    │   ├── loader.py         # IFCLoader: carga, árbol, propiedades
    │   └── query.py          # Funciones IFC puras de consulta
    ├── ai/
    │   ├── ollama_client.py  # Gestión del servidor Ollama (lifecycle)
    │   ├── ifc_tools.py      # Schemas JSON + ejecutor de herramientas IFC
    │   ├── tool_runner.py    # Contexto + bucle tool calling + formateadores
    │   └── backends/
    │       ├── base.py           # AIBackend, ToolCall, ChatResponse
    │       ├── ollama_backend.py # Ollama local
    │       ├── claude_backend.py # Anthropic API
    │       └── openai_backend.py # OpenAI API
    ├── config.py             # ~/.config/appcli/config.json
    ├── installer.py          # appcli-install: descarga Ollama, elige modelo
    ├── main.py
    └── data/
        ├── Modelfile         # FROM {{BASE_MODEL}} — placeholder dinámico
        ├── manual_usuario.md
        └── appcli.desktop
```

## Flujo de tool calling

```
Usuario escribe → AIConsole → ToolRunner.chat()
    │
    ├─ System prompt: base + archivo IFC + elemento seleccionado
    ├─ Tools: 8 herramientas IFC + obtener_seleccion (si hay selección)
    │
    └─ Bucle (no-streaming):
         Backend → tool_calls? → IFCTools.ejecutar() o _fmt_seleccion()
                               → añadir resultado → Backend → …
         Sin tool_calls → respuesta final en streaming → on_token()
```

## Herramientas disponibles en la consola IA

| Herramienta | Cuándo la usa el modelo |
|---|---|
| `obtener_seleccion(modo)` | Preguntas sobre el elemento activo |
| `buscar_elementos` | Listar elementos de un tipo IFC |
| `contar_elementos` | Contar elementos de un tipo |
| `obtener_propiedades` | Propiedades por GlobalId |
| `listar_plantas` | Plantas del edificio |
| `elementos_de_planta` | Elementos de una planta concreta |
| `calcular_area_total` | Suma de áreas por tipo |
| `buscar_por_nombre` | Búsqueda por nombre parcial |

## Configuración de usuario (~/.config/appcli/config.json)

| Clave | Valores | Descripción |
|---|---|---|
| `base_model` | `qwen2.5:1.5b`, … | Modelo base de Ollama elegido en instalación |
| `active_backend` | `ollama` / `claude` / `openai` | Backend activo |
| `ollama_model` | `ifc-assistant`, … | Modelo Ollama activo |
| `claude_model` | `claude-sonnet-4-6`, … | Modelo Claude activo |
| `openai_model` | `gpt-4o-mini`, … | Modelo OpenAI activo |

## Variables de entorno para backends cloud

| Variable | Backend |
|---|---|
| `ANTHROPIC_API_KEY` | Claude (Anthropic) |
| `OPENAI_API_KEY` | ChatGPT (OpenAI) |

## Posibles próximos pasos

- Herramientas para controlar la aplicación (abrir archivo, seleccionar elemento en árbol)
- Tests unitarios para `ifc/query.py`, `ifc_tools.py` y los backends
- Actualizar label de consola cuando se cambia el backend sin reiniciar
- Generar nuevo wheel de distribución
