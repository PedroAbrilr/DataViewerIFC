# AppCLI — Manual de usuario

## ¿Qué es AppCLI?

AppCLI es una aplicación de escritorio para explorar archivos IFC (Industry Foundation Classes), el formato estándar de intercambio de modelos BIM. Permite navegar la jerarquía de elementos de un edificio, consultar sus propiedades y realizar preguntas sobre el modelo mediante inteligencia artificial, tanto local como en la nube.

---

## Requisitos

- Python 3.11 o superior.
- Conexión a internet la primera vez (para descargar Ollama y el modelo base).

---

## Instalación

```bash
# Instalar el paquete
pip install appcli-*.whl

# Ejecutar el instalador (descarga Ollama, configura el modelo y el acceso directo)
appcli-install
```

El instalador:
1. Descarga el binario de Ollama adecuado para tu sistema operativo y lo instala en `~/.local/share/appcli/ollama/`.
2. Muestra un menú para elegir el modelo de lenguaje base.
3. Descarga el modelo elegido en `~/.local/share/appcli/ollama/models/` y crea el asistente personalizado `ifc-assistant`.
4. Guarda la configuración en `~/.config/appcli/config.json`.
5. Instala el acceso directo de escritorio (solo Linux).

Para usar los backends de IA en la nube también es necesario instalar los paquetes correspondientes:

```bash
pip install anthropic   # Para Claude (Anthropic)
pip install openai      # Para ChatGPT (OpenAI)
```

---

## Arrancar la aplicación

```bash
appcli
```

O bien desde el acceso directo del escritorio (Linux) o el menú de inicio (Windows/macOS).

---

## Interfaz

La ventana principal se divide en tres zonas:

```
┌─ Toolbar ─────────────────────────────────────  ⚙ Configuración ─┐
├────────────────────┬──────────────────────────────────────────────┤
│   Árbol de         │   Propiedades                                │
│   elementos        │                                              │
│                    │   ▼ Atributos                                │
│   IfcProject       │     Name     │ ...  │                        │
│   └ IfcSite        │   ▼ Pset_... │      │                        │
│     └ Edificio     │     Área     │ 25.3 │ m²                     │
│       └ Planta     │     ...      │ ...  │ ...                    │
│         └ Muro     │                                              │
├────────────────────┴──────────────────────────────────────────────┤
│  Consola IA                                          backend activo│
│  ┌────────────────────────────────────────────┐ [Enviar]          │
│  │ Escribe tu pregunta aquí...                │                   │
│  └────────────────────────────────────────────┘                   │
└───────────────────────────────────────────────────────────────────┘
```

### Barra de herramientas (superior)
Contiene el botón **Abrir IFC** y, en el lado derecho, el botón **⚙ Configuración**.

### Árbol de elementos (izquierda)
Muestra la jerarquía espacial del modelo IFC: proyecto → emplazamiento → edificio → plantas → elementos. Haz clic en cualquier nodo para ver sus propiedades. Se admite selección múltiple manteniendo `Ctrl`.

### Tabla de propiedades (derecha)
Muestra las propiedades del elemento seleccionado, agrupadas por conjunto de propiedades (PSet). Cada fila indica el nombre de la propiedad, su valor y la unidad cuando corresponde. Con varios elementos seleccionados, las propiedades con valores distintos se marcan como *varios…*.

### Consola IA (parte inferior)
Permite hacer preguntas en lenguaje natural sobre el modelo cargado. El asistente tiene acceso a herramientas de consulta IFC y utiliza el contexto del elemento seleccionado automáticamente. El backend activo se muestra en la cabecera de la consola.

---

## Abrir un archivo IFC

1. Pulsa el botón **Abrir IFC** en la barra superior (o `Ctrl+O`).
2. Elige el archivo `.ifc` en el explorador de archivos.
3. El árbol se poblará automáticamente con la jerarquía del modelo.

---

## Consola IA

Escribe tu pregunta en el campo de texto y pulsa `Enter` o el botón **Enviar**. Puedes cancelar una respuesta en curso con el botón **Detener**.

El asistente entiende preguntas como:
- *¿Cuántos muros hay en el modelo?*
- *¿Qué propiedades tiene este elemento?*
- *¿Cuál es el área total de los forjados?*
- *Lista los elementos de la planta baja.*
- *¿Qué elementos tienen la propiedad IsExternal = True?*
- *Filtra los elementos seleccionados cuyo material sea hormigón.*
- *Abre el archivo edificio.ifc.*

Cuando hay un elemento seleccionado en el árbol, el asistente lo usa como referencia sin necesidad de indicar un identificador.

Cuando el asistente devuelve una lista de elementos como resultado de una búsqueda o filtrado, el árbol de la aplicación se actualiza automáticamente para mostrar esos elementos seleccionados.

---

## Configuración

Pulsa el botón **⚙ Configuración** en la barra superior para abrir la ventana de configuración.

### Asistente IA

Permite seleccionar el backend de IA y el modelo a utilizar. Hay tres opciones:

#### Ollama (local)
Utiliza un modelo de lenguaje ejecutado en tu propio equipo. No envía datos a ningún servidor externo. Requiere que Ollama esté instalado (`appcli-install` lo gestiona automáticamente).

Modelos disponibles:
- **ifc-assistant** — modelo personalizado con conocimiento especializado en BIM/IFC (recomendado).
- El modelo base elegido durante la instalación (por ejemplo, `qwen2.5:1.5b`).

#### Claude (Anthropic)
Utiliza la API de Anthropic. Al seleccionarlo por primera vez, la aplicación pedirá la clave de API, que se guardará en `~/.config/appcli/config.json`. También es necesario instalar el paquete:

```bash
pip install anthropic
```

Modelos disponibles: `claude-sonnet-4-6` (recomendado), `claude-opus-4-7`, `claude-haiku-4-5-20251001`.

#### ChatGPT (OpenAI)
Utiliza la API de OpenAI. Al seleccionarlo por primera vez, la aplicación pedirá la clave de API, que se guardará en `~/.config/appcli/config.json`. También es necesario instalar el paquete:

```bash
pip install openai
```

Modelos disponibles: `gpt-4o-mini` (recomendado), `gpt-4o`, `gpt-3.5-turbo`.

### Directorios del sistema

Muestra las rutas donde AppCLI guarda sus archivos, con indicador de existencia y tamaño:

| Directorio | Contenido |
|---|---|
| `~/.config/appcli/` | Configuración y claves de API |
| `~/.local/share/appcli/ollama/` | Binario de Ollama |
| `~/.local/share/appcli/ollama/models/` | Modelos descargados |
| `~/.local/share/applications/appcli.desktop` | Acceso directo (Linux) |

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El árbol aparece vacío | El archivo IFC no tiene jerarquía espacial | Verifica el archivo con otro visor IFC |
| La tabla de propiedades está vacía | El elemento no tiene PSets asignados | Normal en elementos genéricos |
| La consola IA no responde (Ollama) | Ollama no está instalado o no arranca | Ejecuta `appcli-install` |
| Error de clave API al usar Claude o ChatGPT | Clave no guardada o incorrecta | Abre **⚙ Configuración**, cambia de backend y vuelve a introducir la clave |
| Error «paquete no instalado» | Falta `anthropic` u `openai` | Ejecuta `pip install anthropic` o `pip install openai` |
| Error al abrir el archivo | Archivo IFC corrupto o versión no soportada | Prueba con otro archivo |
