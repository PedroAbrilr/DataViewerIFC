# Guía de desarrollo

## Activar el entorno y arrancar la app

```bash
source .venv/bin/activate
python -m appcli
# o bien:
python src/appcli/main.py
```

## Instalar dependencias

```bash
.venv/bin/pip install -e ".[dev]"
```

Dependencias principales: `ifcopenshell`, `ollama`.  
Dependencias de desarrollo: `pytest`.

## Ejecutar tests

```bash
.venv/bin/pytest
```

## Requisito externo: Ollama

La consola IA requiere Ollama corriendo en local (`http://localhost:11434`):

```bash
ollama serve
ollama pull llama3.2
```

## Mejoras pendientes / backlog

- **Diálogo de archivo nativo multiplataforma** — `tkinter.filedialog` ya es nativo en Windows y macOS; en Linux usa el diálogo Tk propio. La librería `plyer` unifica los tres sistemas con una sola API (`plyer.filechooser.open_file()`). Implementar con fallback a `tkinter.filedialog` si `plyer` no está disponible.

---

## Próximos pasos de implementación

1. **`OllamaClient.stream()`** — `ollama.chat(..., stream=True)`, yield de fragmentos.
2. **`AIConsole._on_send()`** — lanzar streaming en hilo, tokens con `root.after()`.
3. **`App`** — pasar contexto del elemento seleccionado como system prompt a la consola.
4. **Diálogo de apertura al inicio** — mostrar selector de archivo al arrancar si no hay modelo cargado.
