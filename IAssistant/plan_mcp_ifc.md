# Plan: MCP / Tool Calling sobre el modelo IFC

## Qué es y qué no es MCP aquí

**MCP (Model Context Protocol)** es el protocolo de Anthropic para exponer herramientas a modelos de lenguaje. Ollama no lo soporta nativamente, pero sí soporta **tool calling** (función calling) compatible con OpenAI para modelos que lo implementan (llama3.1, llama3.2, mistral-nemo...).

La estrategia es implementar tool calling de Ollama como capa de herramientas IFC, con la misma semántica que MCP: el modelo decide qué herramienta llamar, la app ejecuta la llamada real contra el modelo IFC y devuelve el resultado. Además, el elemento actualmente seleccionado en la UI se inyecta automáticamente en el system prompt como contexto inmediato.

---

## Tres fuentes de información para el modelo

### 0. Manual de usuario (pasivo, siempre presente)
El contenido de `docs/manual_usuario.md` se incluye en el **Modelfile** (system prompt fijo). El modelo puede responder preguntas sobre cómo usar la aplicación sin necesidad de herramientas ni contexto dinámico.

Ejemplos de preguntas cubiertas:
- "¿Cómo abro un archivo IFC?"
- "¿Para qué sirve la consola IA?"
- "¿Cómo selecciono un elemento?"

El manual se incluye en el Modelfile en lugar del system prompt dinámico porque no cambia en tiempo de ejecución y así queda grabado en el modelo personalizado `ifc-assistant`.

### 1. Contexto de selección (pasivo, automático)
Cuando el usuario selecciona un elemento en el árbol, sus propiedades se incluyen automáticamente en el **system prompt** de cada consulta. El modelo puede responder sobre ese elemento sin necesidad de llamar a ninguna herramienta.

```
System prompt:
  [instrucciones base + manual de usuario — fijo en Modelfile]
  [contexto del archivo IFC: nombre, número de elementos]
  [elemento seleccionado actualmente:]
    Nombre: Muro exterior
    Tipo: IfcWall
    Pset_WallCommon / IsExternal: True
    BaseQuantities / Length: 4.5 m
    ...
```

### 2. Herramientas IFC (activo, bajo demanda)
Para preguntas que van más allá del elemento seleccionado (buscar, contar, comparar, agregar), el modelo llama a las herramientas disponibles.

| Herramienta | Descripción |
|---|---|
| `buscar_elementos` | Filtra elementos por tipo IFC (IfcWall, IfcSlab…) |
| `contar_elementos` | Cuenta elementos de un tipo dado |
| `obtener_propiedades` | Devuelve propiedades de un elemento por GlobalId |
| `listar_plantas` | Lista los IfcBuildingStorey del modelo |
| `elementos_de_planta` | Elementos contenidos en una planta |
| `calcular_area_total` | Suma de áreas de un tipo de elemento |
| `buscar_por_nombre` | Filtra elementos cuyo Name contiene un texto |

---

## Arquitectura propuesta

```
App
 ├─ TreePanel ──on_select──► AIConsole.set_context()
 │                               │
 └─ AIConsole                    ▼
     └─ ToolRunner          ← orquesta contexto + tool calling
         ├─ OllamaClient    ← chat con tools JSON
         └─ IFCTools        ← ejecuta herramientas contra el modelo
              └─ IFCLoader  ← ya existente
```

### Módulos nuevos

**`appcli/ifc/query.py`**
- Funciones IFC puras sin dependencia de UI.
- `buscar_por_tipo(modelo, tipo)`, `contar_por_tipo(modelo, tipo)`, `listar_plantas(modelo)`, `elementos_de_planta(modelo, nombre_planta)`, `calcular_area_total(modelo, tipo)`, `buscar_por_nombre(modelo, texto)`.

**`appcli/ai/ifc_tools.py`**
- Clase `IFCTools(loader: IFCLoader)`.
- `definiciones()` → lista de schemas JSON de herramientas (formato Ollama/OpenAI).
- `ejecutar(nombre, argumentos)` → resultado como `str`.

**`appcli/ai/tool_runner.py`**
- Clase `ToolRunner(ollama_client, ifc_tools)`.
- Atributo `contexto_seleccion: str` — propiedades del elemento activo en UI.
- Atributo `contexto_archivo: str` — nombre del archivo y resumen del modelo.
- Método `set_seleccion(elemento, props)` — actualizado desde `App` al seleccionar.
- Método `set_archivo(nombre, total_elementos)` — actualizado al abrir un IFC.
- Método `chat(prompt, on_token, on_tool_call)` — construye el system prompt completo y ejecuta el bucle tool calling.

### System prompt completo (construido en ToolRunner)

```
Eres un asistente experto en BIM e IFC. Responde en el idioma del usuario.

Archivo IFC: {nombre_archivo} — {N} elementos cargados.

[Si hay elemento seleccionado:]
Elemento actualmente seleccionado en la aplicación:
  Nombre: {nombre}
  Tipo: {tipo_ifc}
  {PSet1}:
    {prop}: {valor} {unidad}
  ...

Tienes herramientas disponibles para consultar el modelo completo.
```

### Cambios en módulos existentes

**`OllamaClient`**
- Añadir parámetro `tools` a `stream()` y `query()`.
- Detectar tool calls en los chunks del stream.

**`AIConsole`**
- Sustituir llamada directa a `OllamaClient.stream()` por `ToolRunner.chat()`.
- `set_context(elemento, props)` delega en `ToolRunner.set_seleccion()`.
- Callback `on_tool_call(nombre, args)` muestra en la consola qué herramienta se usa: `[llamando a buscar_elementos...]`.

**`App`**
- Instanciar `IFCTools` y `ToolRunner` tras cargar el modelo IFC.
- Pasar `ToolRunner` a `AIConsole`.
- En `_actualizar_arbol()` llamar a `tool_runner.set_archivo(nombre, total)`.
- En `_on_elemento_seleccionado()` llamar a `tool_runner.set_seleccion(elemento, props)`.

---

## Flujos de ejemplo

### Pregunta sobre el elemento seleccionado (sin herramientas)
```
Usuario: "¿Este muro es exterior?"
→ El contexto ya incluye IsExternal: True
→ Ollama responde directamente sin tool call
```

### Pregunta que requiere herramienta
```
Usuario: "¿Cuántos muros hay en la planta baja?"
1. ToolRunner → Ollama (prompt + contexto selección + tools)
2. Ollama → tool_call: elementos_de_planta({planta: "Planta baja"})
   + tool_call: contar_elementos({tipo: "IfcWall", ...})
3. ToolRunner → IFCTools.ejecutar(...) → resultados
4. ToolRunner → Ollama (resultados de tools)
5. Ollama → "Hay 12 muros en la planta baja."
6. AIConsole muestra respuesta en streaming
```

---

## Orden de implementación

1. `ifc/query.py` — funciones IFC puras.
2. `ai/ifc_tools.py` — schemas JSON + ejecutor.
3. `ai/tool_runner.py` — gestión de contexto + bucle tool calling.
4. Actualizar `OllamaClient` para pasar `tools` al API.
5. Conectar en `App` y `AIConsole`.

## Consideraciones

- Modelos con mejor soporte de tool calling en Ollama: `llama3.2`, `llama3.1`, `mistral-nemo`.
- El tool calling no es compatible con streaming en el mismo turno: los chunks de tool call llegan completos. Solo el texto final se emite en streaming.
- Modo degradado si el modelo no soporta tools: `ToolRunner` incluye todo el contexto del modelo en el system prompt como texto plano.
- El contexto de selección tiene prioridad semántica sobre las herramientas: preguntas sobre "este elemento" siempre usan el contexto inyectado, no una herramienta.
