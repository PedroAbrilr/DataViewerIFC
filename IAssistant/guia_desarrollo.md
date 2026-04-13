# Guía de desarrollo

## Activar el entorno y arrancar la app

```bash
source .venv/bin/activate
.venv/bin/python src/appcli/main.py
```

## Instalar dependencias

```bash
.venv/bin/pip install -e ".[dev]"
```

Dependencias principales: `ifcopenshell`, `ollama`, `ttkthemes`.  
Dependencias de desarrollo: `pytest`, `build`.

## Ejecutar tests

```bash
.venv/bin/pytest
```

## Generar wheel de distribución

```bash
.venv/bin/python -m build --wheel
```

El wheel se genera en `dist/appcli-<version>-py3-none-linux_x86_64.whl`.  
Incluye el binario portable de Ollama, el Modelfile y el manual de usuario.  
El tag de plataforma (`linux_x86_64`) está definido en `setup.cfg`.

Para instalar en otro equipo Linux x86_64:
```bash
pip install dist/appcli-0.1.0-py3-none-linux_x86_64.whl
```

## Ollama — gestión automática

La app gestiona Ollama sin intervención del usuario:

1. Al arrancar, `OllamaClient.ensure_running()` comprueba si Ollama responde.
2. Si no, lanza `bin/ollama serve` (binario portable) o `ollama` del sistema.
3. Descarga `qwen2.5:1.5b` si no está disponible.
4. Crea el modelo `ifc-assistant` desde `appcli/data/Modelfile` si no existe.

Para forzar la recreación del modelo (p. ej. tras actualizar el manual):
```bash
ollama rm ifc-assistant
# relanzar la app
```

## Actualizar el manual de usuario

1. Editar `docs/manual_usuario.md` (fuente de verdad).
2. Copiar a `src/appcli/data/manual_usuario.md`.
3. Borrar el modelo `ifc-assistant` y relanzar la app para regenerarlo.

---

## Mejoras pendientes / backlog

- **MCP / tool calling sobre el modelo IFC** — ver `plan_mcp_ifc.md`. Implementar `ifc/query.py`, `ai/ifc_tools.py` y `ai/tool_runner.py` para que el modelo pueda consultar el IFC completo (buscar, contar, agregar) más allá del elemento seleccionado.

- **Diálogo de archivo nativo multiplataforma** — `tkinter.filedialog` ya es nativo en Windows y macOS; en Linux usa el diálogo Tk propio. La librería `plyer` unifica los tres sistemas. Implementar con fallback a `tkinter.filedialog` si `plyer` no está disponible.

- **Wheel multiplataforma** — el binario de Ollama incluido es Linux x86_64. Para Windows/macOS habría que generar wheels separados con el binario de cada plataforma o descargar Ollama en el primer arranque.
