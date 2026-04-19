# Plan de refactor — AppCLI

Plan autocontenido de limpieza, deduplicación y mejoras de eficiencia del código fuente. Basado en la auditoría del **260419**. Suite actual: **97 tests pasando**; cualquier cambio debe mantener los 97 tests en verde.

---

## Reglas generales de ejecución

1. **Pedir confirmación antes de editar código** (regla global del usuario en `~/.claude/CLAUDE.md`).
2. **Ejecutar la suite completa (`.venv/bin/pytest`) después de cada tarea** y no avanzar si falla algún test.
3. **No introducir emojis** en código ni mensajes (regla global).
4. **Un commit por tarea** con mensaje `aammdd Descripción breve`.
5. Cuando un cambio afecte a documentación interna, actualizar `IAssistant/contexto_proyecto.md` y `IAssistant/arquitectura.md` al final del bloque correspondiente.
6. Cada tarea indica **archivos**, **líneas aproximadas** (pueden variar) y **cómo verificar**.

---

## Estado inicial (referencia)

- Rama: `main`, limpia.
- Repositorio: https://github.com/PedroAbrilr/ifc_IA_CLI
- Tests: 97 (ver `tests/`).
- Archivos principales involucrados:
  - `src/appcli/ifc/loader.py` (136 líneas)
  - `src/appcli/ifc/query.py` (225 líneas)
  - `src/appcli/ai/ollama_client.py` (195 líneas)
  - `src/appcli/ai/tool_runner.py` (319 líneas)
  - `src/appcli/ai/backends/ollama_backend.py` (56 líneas)
  - `src/appcli/ai/backends/openai_backend.py` (102 líneas)
  - `src/appcli/ai/backends/claude_backend.py` (147 líneas)
  - `src/appcli/ui/app.py` (319 líneas)
  - `src/appcli/ui/ai_console.py` (230 líneas)
  - `src/appcli/ui/config_dialog.py` (320 líneas)
  - `src/appcli/ui/tree_panel.py` (72 líneas)
  - `src/appcli/config.py` (42 líneas)

---

# PRIORIDAD ALTA

## Tarea 1 — Deduplicar extracción de PSets IFC

**Problema.** El patrón de iterar `IsDefinedBy → IfcRelDefinesByProperties → (IfcPropertySet | IfcElementQuantity)` está duplicado en tres sitios con pequeñas variaciones:

- `ifc/loader.py::IFCLoader.get_properties()` (aprox. líneas 77–105)
- `ifc/query.py::obtener_propiedades()` (aprox. líneas 188–218)
- `ifc/query.py::filtrar_por_propiedad()` (aprox. líneas 122–149)

**Solución.**

1. En `ifc/query.py`, extraer dos helpers puros a nivel de módulo:
   - `_extraer_valor_cantidad(cantidad)` → devuelve `(valor_str, unidad)` o `(None, "")` iterando `LengthValue`/`AreaValue`/`VolumeValue`/`WeightValue`/`CountValue`/`TimeValue`.
   - `_grupos_pset(elemento)` → devuelve la lista de grupos `[{"pset": ..., "props": [{"nombre","valor","unidad"}]}]`, idéntica estructura a la actual de `IFCLoader.get_properties`, pero SIN el grupo "Atributos".
2. En `ifc/loader.py::IFCLoader.get_properties()`:
   - Mantener la construcción del grupo "Atributos" (`GlobalId`, `Name`, `Description`, `ObjectType`, `Tipo IFC`) tal como está.
   - Reemplazar el bloque de iteración de PSets por `grupos.extend(_grupos_pset(elemento))`.
   - Eliminar los métodos privados `_unidad()` y `_cantidad()` si dejan de usarse.
3. En `ifc/query.py::obtener_propiedades()`:
   - Mantener la construcción de "Atributos".
   - Sustituir la iteración manual de PSets por `grupos.extend(_grupos_pset(elemento))`.
   - Eliminar el dict local `_unidades_cantidad` (queda dentro del helper).
4. En `ifc/query.py::filtrar_por_propiedad()`:
   - Refactor opcional: se puede mantener su lógica actual (compara por nombre y valor sin construir toda la estructura), PERO debe usar el mismo diccionario de atributos de cantidad. Extraer `_CANTIDAD_ATTRS = ("LengthValue", "AreaValue", "VolumeValue", "WeightValue", "CountValue", "TimeValue")` como constante de módulo y usarla aquí.

**Nota importante sobre `_unidad`.** `IFCLoader._unidad()` lee `prop.Unit` del PropertySingleValue; la función actual en `query.obtener_propiedades()` no lo hace (devuelve `""` para PropertySingleValue). Para NO perder información, el helper compartido debe delegar a `_unidad(prop)` para `IfcPropertySingleValue`. Mover `_unidad` también a `ifc/query.py`.

**Resultado esperado.** `loader.py` baja a ~50 líneas; `query.py` gana un helper y evita repetir la lógica de unidades/valores de cantidad. Ahorro neto estimado: ~40 líneas.

**Verificar:**
```bash
.venv/bin/pytest tests/test_ifc_query.py tests/test_ifc_tools.py -v
.venv/bin/pytest  # suite completa: 97 tests
```

---

## Tarea 2 — Borrar código muerto en `OllamaClient`

**Problema.** `OllamaClient.query()` y `OllamaClient.stream()` (aprox. líneas 170–188 de `src/appcli/ai/ollama_client.py`) no se invocan desde ningún lugar del código fuente; todo el chat pasa ahora por la jerarquía de `AIBackend`.

**Verificación previa (antes de borrar):**
```bash
# Ambas búsquedas deben devolver 0 resultados (excepto la propia definición).
```
Usar la herramienta Grep con patrones `\.query\(` y `\.stream\(` sobre `src/appcli/`. El único match permitido es `client.messages.stream(` dentro de `claude_backend.py`.

**Solución.**

1. Eliminar los métodos `query()` y `stream()` de `OllamaClient`.
2. Eliminar el atributo `self.model` si deja de usarse (verificar; se usa en `query`/`stream` solo).
3. Simplificar `_DEFAULT_MODEL` (alias de `_CUSTOM_MODEL`): sustituir las referencias por `_CUSTOM_MODEL` y borrar la constante redundante.
4. El parámetro `model` del constructor de `OllamaClient` puede quedarse o eliminarse según se siga usando desde `App`. Revisar `ui/app.py`: `OllamaClient()` se instancia sin argumentos (línea ~31). Si el constructor ya no necesita `model`, quitarlo.

**Resultado esperado.** `ollama_client.py` queda centrado en lifecycle (arranque/modelo base/modelfile). Ahorro: ~25 líneas.

**Verificar:**
```bash
.venv/bin/pytest
python -c "from appcli.ai.ollama_client import OllamaClient; OllamaClient()"
```

---

## Tarea 3 — Constante única de unidades de cantidad IFC

**Problema.** El diccionario que mapea atributo → unidad aparece dos veces:

- `ifc/loader.py::_cantidad()` (dentro del bucle, se recrea por iteración) — aprox. líneas 127–134
- `ifc/query.py::obtener_propiedades()` — aprox. líneas 179–186

**Solución.** Si la Tarea 1 ya se ha ejecutado completamente, este diccionario vive solo dentro del helper `_extraer_valor_cantidad`. En ese caso, convertir a constante a nivel de módulo en `ifc/query.py`:

```python
_UNIDADES_CANTIDAD = {
    "LengthValue": "m",
    "AreaValue":   "m²",
    "VolumeValue": "m³",
    "WeightValue": "kg",
    "CountValue":  "",
    "TimeValue":   "s",
}
```

Si por cualquier razón la Tarea 1 se salta, hacer este extract aquí como tarea independiente.

**Verificar:**
```bash
.venv/bin/pytest
```

---

# PRIORIDAD MEDIA

## Tarea 4 — Propiedades públicas en `ToolRunner`

**Problema.** Varios módulos acceden a atributos con guion bajo inicial:

- `ui/ai_console.py:18, 122` → `tool_runner._backend`
- `ui/app.py:241` → `tool_runner._ifc_tools`
- `ui/config_dialog.py:298` → `tool_runner._backend`

**Solución.** En `src/appcli/ai/tool_runner.py`:

1. Renombrar el atributo `self._backend` a `self.backend` (público).
2. Renombrar `self._ifc_tools` a `self.ifc_tools` (público).
3. Actualizar todas las referencias internas del propio `tool_runner.py`.
4. Actualizar:
   - `ui/ai_console.py` — dos accesos (`__init__` y `set_runner`).
   - `ui/app.py::_actualizar_arbol` — `self.tool_runner._ifc_tools = IFCTools(...)` → `self.tool_runner.ifc_tools = ...`.
   - `ui/config_dialog.py::_aplicar` — `self._app.tool_runner._backend = ...` → `self._app.tool_runner.backend = ...`.
5. Revisar si algún test accede a estos atributos (`tests/test_tool_runner.py`): actualizar.
6. **Mantener `_app_tools` como privado** (solo se accede mediante `set_app_tools`).

**Verificar:**
```bash
.venv/bin/pytest tests/test_tool_runner.py -v
.venv/bin/pytest
```

---

## Tarea 5 — Helper común para preparar mensajes con system

**Problema.** `OllamaBackend` y `OpenAIBackend` anteponen `{"role": "system", ...}` a la lista de mensajes:

- `ollama_backend.py:13, 35` — código inline duplicado.
- `openai_backend.py:14–22` — en `_prepare_messages`.

**Solución.** En `src/appcli/ai/backends/base.py` añadir una función libre:

```python
def prepend_system(system: str, messages: list) -> list:
    return [{"role": "system", "content": system}] + list(messages)
```

`OpenAIBackend._prepare_messages` mantiene su lógica adicional (convertir objetos Message con `.role`/`.content` a dict). Puede refactorizarse así:

```python
def _prepare_messages(system: str, messages: list) -> list:
    msgs = prepend_system(system, [])
    for msg in messages:
        if isinstance(msg, dict):
            msgs.append(msg)
        else:
            msgs.append({"role": msg.role, "content": msg.content or ""})
    return msgs
```

`OllamaBackend` pasa a usar `prepend_system(system, messages)` en `chat_turn` y `chat_stream`.

**`ClaudeBackend` no aplica** — Claude separa `system` como parámetro top-level.

**Verificar:**
```bash
.venv/bin/pytest tests/test_backends.py -v
.venv/bin/pytest
```

---

## Tarea 6 — Reducir buffer de tokens en streaming

**Problema.** `ToolRunner.chat` usa `_BUFFER_TOKENS = 8` (línea ~20 y ~106–113 de `tool_runner.py`). Acumula 8 fragmentos antes de llamar a `on_token`, introduciendo latencia perceptible en la consola IA.

**Solución.** Dos alternativas (elegir una; la primera es más simple y segura):

**Opción A (recomendada).** Eliminar el buffer: llamar a `on_token(text)` directamente por cada chunk.

```python
# En chat(), sustituir el bloque del buffer por:
for text in self._backend.chat_stream(system, messages):
    if should_stop and should_stop():
        return
    on_token(text)
```

**Opción B.** Mantener buffer por tiempo (no por número de tokens): flush cada 50 ms. Más complejo; solo si la Opción A muestra demasiadas actualizaciones de Tk.

En ambos casos, retirar la constante `_BUFFER_TOKENS` si no queda referenciada.

**Verificar:**
```bash
.venv/bin/pytest tests/test_tool_runner.py -v
# Prueba manual: lanzar la app con dev_bootstrap.py y observar que la respuesta
# en streaming aparece fluida desde el primer token.
.venv/bin/python dev_bootstrap.py
```

---

# PRIORIDAD BAJA

## Tarea 7 — Cachear `config.load()` y `modelos_disponibles()`

**Problema.** Llamadas redundantes a I/O:

- `ui/config_dialog.py::_aplicar()` — `_config.load()` se invoca 3 veces (líneas aprox. 285, 285 y 293) entre comprobación de clave y guardado.
- `ai/ollama_client.py::ensure_running()` — `self.modelos_disponibles()` se invoca 2 veces (líneas 103 y 120).

**Solución.**

1. En `config_dialog.py::_aplicar()`: leer `cfg = _config.load()` una vez al principio y reutilizar. Tras `_config.save(...)` releer si hay que propagar (se usa en `_crear_backend`).
2. En `ollama_client.py::ensure_running()`: guardar la lista en una variable local, recalcularla solo si se acaba de hacer `pull` (cambia la lista).

**Verificar:**
```bash
.venv/bin/pytest
# Comportamiento manual: abrir la app, cambiar backend, reabrir el diálogo.
```

---

## Tarea 8 — Helper para botones con estilo

**Problema.** Los botones con estilo "accent" (azul) y "surface" (gris oscuro) se construyen con los mismos parámetros en:

- `ui/app.py` (Abrir IFC, Configuración)
- `ui/ai_console.py` (Enviar, Detener)
- `ui/config_dialog.py` (Aceptar, Cancelar × 2 diálogos)

**Solución.** Añadir en `src/appcli/ui/theme.py`:

```python
def make_button(parent, text, command, variant="accent", **kwargs):
    """variant: 'accent' (azul), 'surface' (gris), 'danger' (rojo)."""
    base = {
        "accent":  {"bg": ACCENT, "fg": "#ffffff",
                    "activebackground": "#3a82d6", "activeforeground": "#ffffff",
                    "font": FONT_BOLD},
        "surface": {"bg": BG_SURFACE, "fg": FG_PRIMARY,
                    "activebackground": BG_HEADER, "font": FONT_UI},
        "danger":  {"bg": "#c0392b", "fg": "#ffffff",
                    "activebackground": "#a93226", "activeforeground": "#ffffff",
                    "font": FONT_BOLD},
    }[variant]
    return tk.Button(
        parent, text=text, command=command,
        relief="flat", bd=0, cursor="hand2",
        padx=14, pady=5,
        **base, **kwargs,
    )
```

Sustituir cada construcción manual de `tk.Button` que use ACCENT/BG_SURFACE por una llamada a `theme.make_button(...)`. Mantener `padx`/`pady` ajustables por `**kwargs` donde difieran del default.

**Verificar:**
```bash
.venv/bin/pytest
.venv/bin/python dev_bootstrap.py  # revisar visualmente los botones
```

---

## Tarea 9 — Reutilizar GlobalId precalculado en `TreePanel.load()`

**Problema.** `tree_panel.py::_insertar()` (líneas 48–53) llama a `elemento.get_info().get("GlobalId")` aunque `loader._nodo()` ya guarda `nodo["id"]` con el GlobalId.

**Solución.** Sustituir:

```python
try:
    gid = nodo["elemento"].get_info().get("GlobalId")
    if gid:
        self._gid_to_iid[gid] = iid
except Exception:
    pass
```

por:

```python
if nodo.get("id"):
    self._gid_to_iid[nodo["id"]] = iid
```

**Verificar:**
```bash
.venv/bin/pytest
```

---

## Tarea 10 — Mover `_unidades` fuera del bucle en `loader._cantidad`

**Estado.** Esta tarea se vuelve innecesaria si la Tarea 1 (deduplicación) se ejecuta — `_cantidad` desaparece. Solo hacer si se saltaron las tareas anteriores.

---

# Orden recomendado de ejecución

Ejecutar las tareas secuencialmente, commiteando tras cada una que termine con tests en verde:

1. **Tarea 1** — Deduplicar extracción PSets (la más grande; hacerla primero con la suite entera en verde).
2. **Tarea 2** — Borrar código muerto Ollama.
3. **Tarea 3** — Constante unidades (trivial tras Tarea 1).
4. **Tarea 4** — Propiedades públicas ToolRunner.
5. **Tarea 5** — Helper `prepend_system`.
6. **Tarea 6** — Reducir buffer tokens.
7. **Tarea 7** — Cache `config.load` / `modelos_disponibles`.
8. **Tarea 8** — Helper `theme.make_button`.
9. **Tarea 9** — Reutilizar GlobalId en TreePanel.

**Total estimado**: ~150 líneas eliminadas/simplificadas, sin pérdida funcional y con los 97 tests manteniéndose verdes.

---

# Al terminar

1. Verificar suite completa en verde: `.venv/bin/pytest`.
2. Prueba manual mínima: abrir la app, cargar un IFC pequeño, hacer una consulta a la IA, cambiar de backend, cerrar.
3. Actualizar `IAssistant/contexto_proyecto.md`:
   - Nueva entrada en la sección de sesión describiendo el refactor.
   - Actualizar número de tests si cambió.
4. Actualizar `IAssistant/arquitectura.md` si cambió la API pública (ToolRunner, helpers de backend).
5. Actualizar `IAssistant/MEMORY.md` **no** — memorias son para preferencias/hechos del usuario, no para resúmenes de refactors.
6. Commit final opcional con `git log --oneline` para confirmar que todo está publicado.
7. Preguntar al usuario si se hace push a `origin/main`.
