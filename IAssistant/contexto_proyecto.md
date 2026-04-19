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

## Estado actual del proyecto (260419 — sesión de cierre)

- Carga de archivos IFC **implementada y funcional**.
- Árbol de jerarquía espacial **implementado y funcional**.
- Tabla de propiedades agrupada por PSet con columna de unidades **implementada**.
- Multiselección en el árbol con propiedades fusionadas **implementada**.
- Tema visual oscuro con `ttkthemes` (equilux) **aplicado**.
- Consola IA con streaming, tool calling y botón Detener **funcional**.
- **Tool calling IFC completamente implementado**: 8 herramientas activas.
- **Selección del árbol sincronizada con la IA**: cuando una herramienta devuelve una lista de elementos (buscar, filtrar, elementos de planta…) el árbol se actualiza automáticamente para seleccionarlos.
- **Multi-backend IA implementado**:
  - `OllamaBackend` — modelo local, ifc-assistant personalizado
  - `ClaudeBackend` — Anthropic API
  - `OpenAIBackend` — OpenAI API
  - Configuración persistida en `~/.config/appcli/config.json`
- **Ventana de configuración** (`ui/config_dialog.py`):
  - Selector de backend IA y modelo
  - Diálogo emergente de API key al elegir Claude u OpenAI (se guarda en config.json)
  - Sección de directorios del sistema con estado y tamaño
  - Label de consola actualizado al cambiar de backend
- **Herramientas de app** (`ai/app_tools.py`): `estado_app` y `cargar_ifc` permiten a la IA consultar el estado y abrir archivos IFC.
- **Gestión de rutas de Ollama**:
  - Binario portable en `src/appcli/ollama/ollama` (desarrollo) o `~/.local/share/appcli/ollama/ollama` (producción)
  - Modelos en `ollama/models/` junto al binario (`OLLAMA_MODELS` configurado automáticamente)
  - `dev_bootstrap.py` como punto de entrada en desarrollo (fija `APPCLI_OLLAMA_BIN`)
- **Installer independiente** (`appcli-install`):
  - Descarga Ollama según OS/arquitectura a `~/.local/share/appcli/ollama/`
  - Menú de selección de modelo base
  - Pull del modelo + creación de `ifc-assistant`
  - Guarda configuración y acceso directo de escritorio
- Wheel `py3-none-any` (sin binario Ollama embebido).
- Tests unitarios: 54 tests pasando (`ifc/query.py`, `ifc_tools.py`, backends y config).
- Manual de usuario actualizado.

## Arquitectura de módulos

```
AppCLI/
├── dev_bootstrap.py          ← punto de entrada desarrollo (no en wheel)
├── tests/
│   ├── test_ifc_query.py     # 21 tests de ifc/query.py
│   ├── test_ifc_tools.py     # 18 tests de ai/ifc_tools.py
│   └── test_backends.py      # 15 tests de backends y config
└── src/appcli/
    ├── ui/
    │   ├── theme.py          # Paleta, fuentes y estilos ttk
    │   ├── app.py            # Ventana principal; toolbar con botón Configuración
    │   ├── config_dialog.py  # Ventana de configuración: IA, credenciales, directorios
    │   ├── tree_panel.py     # Árbol jerárquico IFC (multiselección + select_by_ids)
    │   ├── props_panel.py    # Tabla de propiedades por PSet
    │   └── ai_console.py     # Consola IA — delega en ToolRunner
    ├── ifc/
    │   ├── loader.py         # IFCLoader: carga, árbol, propiedades
    │   └── query.py          # Funciones IFC puras de consulta
    ├── ai/
    │   ├── ollama_client.py  # Gestión del servidor Ollama (lifecycle + rutas)
    │   ├── ifc_tools.py      # Schemas JSON + ejecutor; _last_ids para selección
    │   ├── tool_runner.py    # Contexto + bucle tool calling + on_seleccionar callback
    │   ├── app_tools.py      # Herramientas de app: estado_app, cargar_ifc
    │   └── backends/
    │       ├── base.py           # AIBackend, ToolCall, ChatResponse
    │       ├── ollama_backend.py # Ollama local
    │       ├── claude_backend.py # Anthropic API
    │       └── openai_backend.py # OpenAI API
    ├── config.py             # ~/.config/appcli/config.json + inject_env()
    ├── installer.py          # appcli-install: descarga Ollama, elige modelo
    ├── main.py
    ├── ollama/               # Binario portable (gitignored) + models/ (gitignored)
    └── data/
        ├── Modelfile         # FROM {{BASE_MODEL}} — placeholder dinámico
        ├── manual_usuario.md
        └── appcli.desktop
```

## Rutas del sistema

| Ruta | Contenido | Entorno |
|---|---|---|
| `src/appcli/ollama/ollama` | Binario portable | Desarrollo |
| `src/appcli/ollama/models/` | Modelos Ollama | Desarrollo |
| `~/.local/share/appcli/ollama/ollama` | Binario portable | Producción |
| `~/.local/share/appcli/ollama/models/` | Modelos Ollama | Producción |
| `~/.config/appcli/config.json` | Configuración y API keys | Ambos |
| `~/.local/share/applications/appcli.desktop` | Acceso directo | Producción Linux |

## Variables de entorno

| Variable | Propósito |
|---|---|
| `APPCLI_OLLAMA_BIN` | Ruta al binario de Ollama (fijada por `dev_bootstrap.py`) |
| `OLLAMA_MODELS` | Directorio de modelos (fijado automáticamente por `_prepare_models_dir()`) |
| `ANTHROPIC_API_KEY` | Inyectada desde config.json al arrancar |
| `OPENAI_API_KEY` | Inyectada desde config.json al arrancar |

## Configuración de usuario (~/.config/appcli/config.json)

| Clave | Descripción |
|---|---|
| `base_model` | Modelo base de Ollama elegido en instalación |
| `active_backend` | Backend activo: `ollama` / `claude` / `openai` |
| `ollama_model` | Modelo Ollama activo |
| `claude_model` | Modelo Claude activo |
| `openai_model` | Modelo OpenAI activo |
| `anthropic_api_key` | Clave API de Anthropic (nunca se distribuye) |
| `openai_api_key` | Clave API de OpenAI (nunca se distribuye) |

## Resumen sesión 260419

Trabajo completado en esta sesión:

1. **Herramienta `filtrar_por_propiedad`** — filtra elementos por valor de propiedad, en el modelo completo o en la selección actual. Usa un sentinel `_DELEGAR_SELECCION_` para que `ToolRunner` resuelva el filtrado sobre `_elementos`.
2. **`AppTools`** — nuevo módulo con herramientas `estado_app` y `cargar_ifc` que permiten a la IA consultar el estado de la aplicación y abrir archivos IFC desde la consola.
3. **Sincronización árbol ↔ IA** — cuando una herramienta devuelve una lista de elementos, el árbol se actualiza automáticamente: `IFCTools._last_ids` → `ToolRunner.on_seleccionar` → `TreePanel.select_by_ids()`. Verificado que no produce bucle (el cambio de selección actualiza contexto pero no relanza la IA).
4. **54 tests unitarios** pasando — `ifc/query.py`, `ifc_tools.py`, backends y config.
5. **Documentación** actualizada — manual, arquitectura, contexto y guía de desarrollo.

## Posibles próximos pasos

- Publicar en GitHub y crear primera Release con el wheel
- Ampliar cobertura de tests: `app_tools.py`, `tool_runner.py`, `config_dialog.py`
- Herramienta de selección inversa: seleccionar elementos en la IA desde el árbol y consultarlos por GlobalId
- Exportar resultados de consultas a CSV o tabla
