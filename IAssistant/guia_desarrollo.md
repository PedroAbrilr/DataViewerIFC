# Guía de desarrollo

## Activar el entorno y arrancar la app

```bash
source .venv/bin/activate
.venv/bin/python dev_bootstrap.py
```

`dev_bootstrap.py` fija automáticamente `APPCLI_OLLAMA_BIN` al binario portable del repositorio (`src/appcli/ollama/ollama`) y `OLLAMA_MODELS` a `src/appcli/ollama/models/`. No se incluye en el wheel.

## Instalar dependencias

```bash
.venv/bin/pip install -e ".[dev]"
```

Dependencias principales: `ifcopenshell`, `ollama`, `ttkthemes`.
Dependencias opcionales: `anthropic`, `openai` (backends en la nube).
Dependencias de desarrollo: `pytest`, `build`.

## Ejecutar tests

```bash
.venv/bin/pytest
```

## Generar wheel de distribución

```bash
.venv/bin/python -m build --wheel
```

El wheel se genera en `dist/appcli-<version>-py3-none-any.whl`.
Incluye el Modelfile y el manual de usuario (`appcli/data/`).
El binario de Ollama **no se incluye** — el instalador (`appcli-install`) lo descarga en el equipo del usuario.

## Ollama — gestión en desarrollo

El binario portable está en `src/appcli/ollama/ollama` (gitignored).
Los modelos se descargan en `src/appcli/ollama/models/` (gitignored).

`OllamaClient.ensure_running()` al arrancar:
1. Fija `OLLAMA_MODELS` al directorio `models/` junto al binario.
2. Comprueba si Ollama responde; lo arranca si no.
3. Descarga el modelo base si no está disponible.
4. Crea `ifc-assistant` desde `appcli/data/Modelfile` si no existe.

Para forzar la recreación del asistente (p. ej. tras actualizar el manual):
```bash
OLLAMA_MODELS=src/appcli/ollama/models src/appcli/ollama/ollama rm ifc-assistant
# relanzar la app
```

**Primera ejecución tras instalar el binario portable**: Ollama necesita generar su clave de identidad (`~/.ollama/id_ed25519`). Si la descarga falla con ese error, ejecutar una vez:
```bash
OLLAMA_MODELS=src/appcli/ollama/models src/appcli/ollama/ollama serve &
sleep 5 && kill %1
```

## Credenciales de backends en la nube

Las claves API se guardan en `~/.config/appcli/config.json` e se inyectan en `os.environ` al arrancar. Se introducen desde la ventana **⚙ Configuración** de la app — no hace falta definirlas manualmente en el entorno.

## Actualizar el manual de usuario

1. Editar `src/appcli/data/manual_usuario.md`.
2. Borrar el modelo `ifc-assistant` y relanzar la app para regenerarlo con el nuevo contenido.

## Estructura de archivos relevante para desarrollo

```
AppCLI/
├── dev_bootstrap.py          ← arranque en desarrollo
├── src/appcli/
│   ├── ollama/
│   │   ├── ollama            ← binario portable (gitignored)
│   │   └── models/           ← modelos (gitignored)
│   ├── ui/
│   │   └── config_dialog.py  ← ventana de configuración
│   ├── ai/
│   │   └── ollama_client.py  ← _ollama_bin(), _prepare_models_dir()
│   └── config.py             ← load(), save(), inject_env()
└── IAssistant/               ← documentos de trabajo (no en wheel)
```
