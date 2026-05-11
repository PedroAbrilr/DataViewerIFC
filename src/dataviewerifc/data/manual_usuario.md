# DataViewerIFC — Manual de usuario

## ¿Qué es DataViewerIFC?

DataViewerIFC es una aplicación de escritorio para explorar archivos IFC, el formato estándar de los modelos de edificios en BIM. Con DataViewerIFC puedes navegar por todos los elementos de un edificio —muros, forjados, puertas, ventanas, pilares…—, consultar sus propiedades y hacer preguntas sobre el modelo en lenguaje natural gracias a un asistente de inteligencia artificial.

---

## Requisitos

- Un ordenador con Windows, macOS o Linux.
- Python 3.11 o superior instalado.
- Conexión a internet la primera vez, para descargar el paquete y el modelo de IA local.

---

## Instalación

### 1. Crear un entorno de trabajo

Abre una terminal y ejecuta:

```bash
python -m venv dataviewerifc-env
```

Activa el entorno:

```bash
# En Linux o macOS
source dataviewerifc-env/bin/activate

# En Windows
dataviewerifc-env\Scripts\activate
```

### 2. Instalar DataViewerIFC

```bash
pip install https://github.com/PedroAbrilr/DataViewerIFC/releases/latest/download/dataviewerifc-1.2.0-py3-none-any.whl
```

### 3. Arrancar la aplicación

```bash
dataviewerifc
```

La primera vez que uses el asistente de IA local (Ollama), la aplicación descargará automáticamente el modelo de lenguaje. Esto puede tardar unos minutos según la velocidad de tu conexión. Las siguientes veces arrancará al instante.

---

## La ventana de la aplicación

La ventana se divide en tres zonas:

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

**Barra superior** — Contiene el botón **Abrir IFC** para cargar un archivo y el botón **⚙ Configuración** a la derecha.

**Árbol de elementos** (izquierda) — Muestra la jerarquía del edificio: proyecto → emplazamiento → edificio → plantas → elementos. Haz clic en cualquier elemento para ver sus propiedades. Puedes seleccionar varios a la vez manteniendo `Ctrl`. Cuando el asistente busca o filtra elementos, el árbol se actualiza automáticamente.

**Tabla de propiedades** (derecha) — Muestra todas las propiedades del elemento seleccionado, organizadas por grupos. Cada fila indica el nombre de la propiedad, su valor y la unidad si corresponde.

**Consola IA** (parte inferior) — Escribe aquí tus preguntas. El asistente responde en lenguaje natural y puede buscar, filtrar y analizar el modelo por ti.

---

## Abrir un archivo IFC

1. Pulsa **Abrir IFC** en la barra superior, o usa el atajo `Ctrl+O`.
2. Busca el archivo `.ifc` en tu ordenador y ábrelo.
3. El árbol se cargará con todos los elementos del modelo.

También puedes pedírselo directamente al asistente:

```
Abre el archivo edificio.ifc
```

---

## El asistente de IA

### Cómo usarlo

Escribe tu pregunta en el campo de texto de la consola y pulsa `Enter` o el botón **Enviar**. Si quieres cancelar una respuesta que está tardando, pulsa **Detener**.

El asistente entiende el contexto: si tienes un elemento seleccionado en el árbol, lo usa automáticamente como referencia. No necesitas indicar identificadores ni códigos.

### Ejemplos: buscar archivos del proyecto

Si has configurado una carpeta de proyecto, el asistente puede buscar en ella:

```
¿Qué archivos IFC tengo disponibles?
```
```
Establece /home/usuario/proyectos como carpeta de proyecto
```
```
¿Cuál es la carpeta de proyecto configurada?
```

### Ejemplos: abrir un modelo

```
Abre el archivo edificio.ifc
```
```
Carga el modelo del hospital
```
```
¿Qué archivo tengo abierto ahora?
```

### Ejemplos: explorar el modelo

```
¿Cuántos muros hay en el edificio?
```
```
Lista todas las puertas
```
```
¿Qué elementos hay en la planta baja?
```
```
Busca todos los pilares
```
```
Muéstrame los elementos cuyo nombre contiene «fachada»
```

Cuando el asistente devuelve una lista de elementos, el árbol se actualiza para mostrarlos seleccionados.

### Ejemplos: consultar propiedades

```
¿Qué propiedades tiene este elemento?
```
```
¿Cuál es el área del elemento seleccionado?
```
```
¿Este muro es exterior?
```
```
¿Cuál es el material de este forjado?
```

### Ejemplos: filtrar elementos

```
¿Qué muros son exteriores?
```
```
Filtra los elementos seleccionados que sean de hormigón
```
```
Busca elementos con resistencia al fuego EI60
```

### Ejemplos: cálculos

```
¿Cuál es el área total de los forjados?
```
```
¿Cuántas ventanas hay en cada planta?
```
```
Calcula el área total de muros exteriores
```

---

## El asistente de IA — opciones disponibles

DataViewerIFC puede conectarse a cuatro asistentes distintos. Puedes cambiar entre ellos en cualquier momento desde **⚙ Configuración**.

### Ollama — asistente local

Funciona directamente en tu ordenador, sin enviar ningún dato a internet. Es la opción recomendada si trabajas con modelos confidenciales. El asistente usa un modelo personalizado llamado `ifc-assistant`, entrenado con instrucciones específicas sobre BIM e IFC.

La primera vez descarga el modelo automáticamente. A partir de ahí funciona sin conexión.

### Claude (Anthropic)

Asistente en la nube de alta calidad, con excelente comprensión del lenguaje técnico. Requiere una clave de API de Anthropic.

### ChatGPT (OpenAI)

Asistente en la nube ampliamente conocido. Requiere una clave de API de OpenAI.

### Gemini (Google)

Asistente en la nube de Google con buena velocidad de respuesta. Requiere una clave de API de Google AI Studio.

---

## Configuración

Pulsa **⚙ Configuración** en la barra superior para abrir la ventana de ajustes.

**Sección «Asistente IA»** — Elige el asistente y el modelo que quieres usar. Si seleccionas Claude, ChatGPT o Gemini por primera vez, la aplicación te pedirá tu clave de API al pulsar **Aplicar**. La clave se guarda de forma local en tu ordenador y no se comparte con nadie.

Cuando el backend seleccionado es Ollama, aparece el botón **Recrear modelo ifc-assistant**. Úsalo si el asistente no responde correctamente o si has cambiado el modelo base: descarga el modelo si es necesario y reconstruye el asistente personalizado con las instrucciones de BIM/IFC.

**Sección «Directorios del sistema»** — Muestra las carpetas donde DataViewerIFC guarda su configuración, el binario de Ollama y los modelos descargados.

Al pulsar **Aplicar**, los cambios tienen efecto inmediatamente sin necesidad de reiniciar.

---

## Solución de problemas

| Qué ocurre | Por qué | Qué hacer |
|---|---|---|
| El árbol aparece vacío | El archivo no tiene jerarquía espacial definida | Comprueba el archivo con otro visor IFC |
| La tabla de propiedades está vacía | El elemento no tiene propiedades asignadas | Es normal en algunos elementos genéricos |
| El asistente local no responde | Ollama no ha arrancado o el modelo no está creado | Espera unos segundos; si persiste, usa **Recrear modelo ifc-assistant** en ⚙ Configuración |
| Error de clave API | La clave no está guardada o es incorrecta | Abre **⚙ Configuración** e introduce la clave de nuevo (Anthropic, OpenAI o Google según el asistente elegido) |
| El asistente no encuentra un archivo IFC | El archivo no está en la carpeta de trabajo ni en la carpeta de proyecto | Configura la carpeta de proyecto o abre el archivo manualmente con **Abrir IFC** |
| El archivo no se abre | El archivo está dañado o es de una versión no compatible | Prueba con otro archivo IFC |
| El asistente tarda en responder | El modelo local se está cargando | Las primeras respuestas son más lentas; las siguientes van mucho más rápido |

---

---

# Anejo técnico

*Esta sección contiene información de referencia para usuarios avanzados y para el funcionamiento interno del asistente.*

---

## Herramientas del asistente

El asistente dispone de las siguientes herramientas para consultar el modelo IFC y gestionar la aplicación. Las usa de forma automática cuando la pregunta lo requiere.

### Consulta IFC

| Herramienta | Descripción |
|---|---|
| `buscar_elementos(tipo)` | Busca todos los elementos de un tipo IFC y los selecciona en el árbol |
| `contar_elementos(tipo)` | Cuenta cuántos elementos hay de un tipo |
| `obtener_propiedades(global_id)` | Devuelve todos los PSets y atributos de un elemento por su GlobalId |
| `obtener_seleccion(modo)` | Devuelve información del elemento o elementos seleccionados. Modos: `reducido`, `agrupado`, `estadistico` |
| `listar_plantas()` | Lista todas las plantas (IfcBuildingStorey) con nombre e identificador |
| `elementos_de_planta(planta)` | Lista y selecciona los elementos de una planta concreta |
| `calcular_area_total(tipo)` | Suma las áreas de todos los elementos de un tipo |
| `buscar_por_nombre(texto)` | Busca elementos cuyo nombre contiene el texto (parcial, sin distinguir mayúsculas) |
| `filtrar_por_propiedad(propiedad, valor, fuente, tipo)` | Filtra elementos por propiedad y valor. `fuente`: `modelo` o `seleccion` |

### Aplicación

| Herramienta | Descripción |
|---|---|
| `estado_app()` | Comprueba si hay un archivo IFC abierto y cuál es |
| `cargar_ifc(nombre)` | Abre un archivo IFC por nombre desde el directorio de trabajo |

### Directorio de proyecto

| Herramienta | Descripción |
|---|---|
| `obtener_directorio_proyecto()` | Devuelve la carpeta de proyecto configurada |
| `establecer_directorio_proyecto(ruta)` | Guarda una nueva carpeta de proyecto en la configuración |
| `buscar_archivos_ifc()` | Busca recursivamente archivos `.ifc` en la carpeta de proyecto |

---

## Modelos de IA disponibles

### Ollama (local)

El modelo base por defecto es `qwen2.5:1.5b`. Se puede cambiar en la configuración. Cualquier modelo disponible en [ollama.com/library](https://ollama.com/library) es compatible. El asistente personalizado `ifc-assistant` se construye sobre el modelo base configurado con instrucciones especializadas en BIM/IFC.

### Claude (Anthropic)

| Modelo | Características |
|---|---|
| `claude-sonnet-4-6` | Equilibrio calidad/velocidad, recomendado |
| `claude-opus-4-7` | Máxima calidad |
| `claude-haiku-4-5-20251001` | Más rápido y económico |

### ChatGPT (OpenAI)

| Modelo | Características |
|---|---|
| `gpt-4o-mini` | Rápido y económico, recomendado |
| `gpt-4o` | Mayor calidad |

### Gemini (Google)

Requiere `GOOGLE_API_KEY`. Clave obtenible en [aistudio.google.com](https://aistudio.google.com).

| Modelo | Características |
|---|---|
| `gemini-2.0-flash` | Rápido, recomendado |
| `gemini-1.5-flash` | Alternativa ligera |
| `gemini-1.5-pro` | Mayor capacidad de contexto |

---

## Rutas de instalación por sistema operativo

| Elemento | Linux | macOS | Windows |
|---|---|---|---|
| Configuración | `~/.config/dataviewerifc/` | `~/.config/dataviewerifc/` | `%APPDATA%\dataviewerifc\` |
| Binario Ollama | `~/.local/share/dataviewerifc/ollama/` | `~/.local/share/dataviewerifc/ollama/` | `%LOCALAPPDATA%\dataviewerifc\ollama\` |
| Modelos Ollama | directorio `models/` junto al binario | directorio `models/` junto al binario | directorio `models/` junto al binario |
| Acceso directo | `~/.local/share/applications/` | — | — |

---

## Archivo de configuración

La configuración se guarda en `config.json` dentro de la carpeta de configuración del usuario. Contiene las preferencias activas: backend seleccionado, modelos elegidos, claves de API y carpeta de proyecto. No se incluye en ninguna distribución ni se envía a servidores externos.
