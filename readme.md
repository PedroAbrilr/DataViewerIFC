# AppCLI — Manual de usuario v1.2

## ¿Qué es AppCLI?

AppCLI es una aplicación de escritorio para explorar archivos IFC (Industry Foundation Classes), el formato estándar de intercambio de modelos BIM. Permite navegar la jerarquía de elementos de un edificio, consultar sus propiedades y realizar preguntas sobre el modelo mediante inteligencia artificial, tanto local como en la nube.

---

## Requisitos

- Python 3.11 o superior.
- Conexión a internet la primera vez (para instalar el paquete y, si usas Ollama, descargar el modelo de lenguaje).

---

## Instalación

### 1. Crear el entorno virtual

Se recomienda instalar AppCLI en un entorno virtual para evitar conflictos con otros paquetes de Python.

```bash
# Crear el entorno virtual
python -m venv appcli-env

# Activar el entorno (Linux / macOS)
source appcli-env/bin/activate

# Activar el entorno (Windows)
appcli-env\Scripts\activate
```

### 2. Instalar el paquete

Descarga el wheel desde el repositorio del proyecto e instálalo con pip:

```bash
pip install https://github.com/PedroAbrilr/DataViewerIFC/releases/latest/download/dataviewerifc-1.2.0-py3-none-any.whl
```

El paquete incluye todas las dependencias necesarias (ifcopenshell, ollama, anthropic, openai, ttkthemes).

### 3. Arrancar la aplicación

```bash
appcli
```

La primera vez que uses el asistente local (Ollama), la aplicación descargará automáticamente el modelo de lenguaje. Esto puede tardar unos minutos. Las siguientes veces arrancará al instante.

> Si vas a usar exclusivamente los asistentes en la nube (Claude o ChatGPT), no necesitas esperar la descarga del modelo local.

---

## Arrancar la aplicación

```bash
appcli
```

O bien desde el acceso directo del escritorio (Linux).

---

## Interfaz

La ventana principal se divide en tres zonas:

```
┌─ Toolbar ──────────────────────────────────────  ⚙ Configuración ─┐
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
│  Consola IA                                         backend activo│
│  ┌────────────────────────────────────────────┐ [Enviar]          │
│  │ Escribe tu pregunta aquí...                │                   │
│  └────────────────────────────────────────────┘                   │
└───────────────────────────────────────────────────────────────────┘
```

### Barra de herramientas (superior)
Contiene el botón **Abrir IFC** (`Ctrl+O`) para cargar un archivo, y en el lado derecho el botón **⚙ Configuración**.

### Árbol de elementos (izquierda)
Muestra la jerarquía espacial del modelo IFC: proyecto → emplazamiento → edificio → plantas → elementos. Haz clic en cualquier nodo para ver sus propiedades. Se admite selección múltiple manteniendo `Ctrl`. Cuando el asistente realiza una búsqueda o filtrado, el árbol se actualiza automáticamente para mostrar los elementos resultado.

### Tabla de propiedades (derecha)
Muestra las propiedades del elemento seleccionado, agrupadas por conjunto de propiedades (PSet). Cada fila indica el nombre de la propiedad, su valor y la unidad cuando corresponde. Con varios elementos seleccionados, las propiedades con valores distintos se marcan como *varios…*.

### Consola IA (parte inferior)
Permite hacer preguntas en lenguaje natural sobre el modelo cargado. El asistente tiene acceso a herramientas de consulta IFC y utiliza el contexto del elemento seleccionado automáticamente. El backend activo se muestra en la cabecera de la consola.

---

## Abrir un archivo IFC

1. Pulsa el botón **Abrir IFC** en la barra superior (o `Ctrl+O`).
2. Elige el archivo `.ifc` en el explorador de archivos.
3. El árbol se poblará automáticamente con la jerarquía del modelo.

También puedes pedir al asistente que abra un archivo (ver sección de ejemplos).

---

## Asistentes de IA disponibles

AppCLI soporta cuatro backends de IA que pueden cambiarse en cualquier momento desde **⚙ Configuración**:

### Ollama (local) — recomendado para privacidad

Ejecuta el modelo de lenguaje directamente en tu equipo. No envía ningún dato a servidores externos. El modelo `ifc-assistant` es un asistente personalizado con instrucciones especializadas en BIM/IFC, descargado automáticamente al arrancar la app por primera vez.

- **Ventaja**: privacidad total, no requiere conexión a internet después de la primera descarga.
- **Requisito**: disponer de suficiente RAM (mínimo 4 GB libres para modelos ligeros).
- **Modelos soportados**: cualquier modelo disponible en [ollama.com/library](https://ollama.com/library).

### Claude (Anthropic)

Utiliza los modelos de lenguaje de Anthropic a través de su API. Son modelos de alta calidad con excelente comprensión del lenguaje y capacidad de razonamiento.

- **Ventaja**: alta calidad de respuesta, ideal para análisis complejos.
- **Requisito**: clave de API de Anthropic (obtenla en [console.anthropic.com](https://console.anthropic.com)).
- **Modelos disponibles**:
  - `claude-sonnet-4-6` — equilibrio calidad/velocidad, recomendado.
  - `claude-opus-4-7` — máxima calidad.
  - `claude-haiku-4-5-20251001` — más rápido y económico.

### ChatGPT (OpenAI)

Utiliza los modelos GPT de OpenAI a través de su API.

- **Ventaja**: ampliamente conocido, con buena documentación y soporte.
- **Requisito**: clave de API de OpenAI (obtenla en [platform.openai.com](https://platform.openai.com)).
- **Modelos disponibles**:
  - `gpt-4o-mini` — rápido y económico, recomendado.
  - `gpt-4o` — mayor calidad.
  - `gpt-3.5-turbo` — más económico.

### Gemini (Google)

Utiliza los modelos Gemini de Google a través de su API.

- **Ventaja**: buena velocidad de respuesta y cuota gratuita generosa.
- **Requisito**: clave de API de Google AI Studio (obtenla en [aistudio.google.com](https://aistudio.google.com)).
- **Modelos disponibles**:
  - `gemini-2.0-flash` — rápido, recomendado.
  - `gemini-1.5-flash` — alternativa ligera.
  - `gemini-1.5-pro` — mayor capacidad de contexto.

---

## Ventana de configuración

Pulsa **⚙ Configuración** en la barra superior para abrir la ventana de configuración.

### Sección «Asistente IA»

Permite seleccionar el backend activo y el modelo concreto a utilizar. Al cambiar de backend:

- Se muestra un aviso si el backend no está disponible (por ejemplo, si falta la clave de API o Ollama no está instalado).
- Si seleccionas Claude, ChatGPT o Gemini por primera vez y no hay clave de API guardada, la aplicación la pedirá automáticamente al pulsar **Aplicar**.
- La clave se guarda de forma local en el archivo de configuración del usuario y no se incluye en ninguna distribución.

Al pulsar **Aplicar**, el cambio de backend tiene efecto inmediatamente sin necesidad de reiniciar la aplicación.

Cuando el backend seleccionado es Ollama, aparece el botón **Recrear modelo ifc-assistant**. Úsalo si el asistente no responde o si has cambiado el modelo base: descarga el modelo si es necesario y reconstruye el asistente personalizado.

### Sección «Directorios del sistema»

Muestra las rutas donde AppCLI guarda sus archivos, con un indicador de si el directorio existe (✓/✗) y el espacio ocupado:

| Entrada | Contenido |
|---|---|
| Configuración | Archivo `config.json` con preferencias y claves de API |
| Ollama | Directorio con el binario de Ollama |
| Modelos Ollama | Modelos de lenguaje descargados |
| Acceso directo | Archivo `.desktop` (solo Linux) |

Las rutas exactas varían por sistema operativo (ver tabla en la sección de instalación).

---

## Consola IA — uso y ejemplos

Escribe tu pregunta en el campo de texto y pulsa `Enter` o el botón **Enviar**. Puedes cancelar una respuesta en curso con el botón **Detener**.

El asistente tiene acceso a las siguientes herramientas de consulta:

| Herramienta | Descripción |
|---|---|
| `buscar_elementos` | Busca todos los elementos de un tipo IFC |
| `contar_elementos` | Cuenta elementos de un tipo IFC |
| `obtener_propiedades` | Obtiene todas las propiedades de un elemento |
| `listar_plantas` | Lista las plantas del modelo |
| `elementos_de_planta` | Lista elementos de una planta concreta |
| `calcular_area_total` | Suma las áreas de un tipo de elemento |
| `buscar_por_nombre` | Busca elementos por nombre (parcial) |
| `filtrar_por_propiedad` | Filtra por propiedad y valor, en el modelo o en la selección |
| `estado_app` | Consulta si hay un archivo IFC abierto |
| `cargar_ifc` | Abre un archivo IFC desde el directorio de trabajo |
| `obtener_directorio_proyecto` | Consulta el directorio de proyecto configurado |
| `establecer_directorio_proyecto` | Cambia el directorio de proyecto |
| `buscar_archivos_ifc` | Busca recursivamente archivos .ifc en el directorio de proyecto |

### Ejemplos: directorio de proyecto

El asistente puede gestionar un directorio de proyecto para localizar archivos IFC sin necesidad de indicar rutas completas.

```
¿Cuál es el directorio de proyecto configurado?
```
```
Establece /home/usuario/proyectos como directorio de proyecto
```
```
¿Qué archivos IFC hay disponibles?
```
```
Busca todos los archivos IFC en el proyecto
```

### Ejemplos: abrir archivos

```
Abre el archivo edificio.ifc
```
```
Carga el modelo hospital
```
```
¿Qué archivo está abierto ahora mismo?
```

El asistente buscará el archivo en el directorio de trabajo actual (donde se ejecutó `appcli`). Si hay varios archivos `.ifc` disponibles, los listará para que elijas.

### Ejemplos: consultar y seleccionar elementos

```
¿Cuántos muros hay en el modelo?
```
```
Lista todas las puertas del edificio
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

Cuando el asistente devuelve una lista de elementos, el árbol de la aplicación se actualiza automáticamente para mostrar esos elementos seleccionados y resaltados.

### Ejemplos: filtrar por propiedad

```
¿Qué muros tienen la propiedad IsExternal = True?
```
```
Filtra los elementos de la selección actual cuyo material sea hormigón
```
```
¿Qué elementos tienen un área superior a 20 m²?
```
```
Busca elementos con la propiedad FireRating igual a «EI60»
```

El parámetro `fuente` puede ser `modelo` (busca en todo el IFC) o `seleccion` (filtra solo los elementos seleccionados en ese momento en el árbol).

### Ejemplos: consultar propiedades de un elemento

```
¿Qué propiedades tiene este elemento?
```
```
¿Cuál es el área del elemento seleccionado?
```
```
Dame todos los PSets del muro seleccionado
```
```
¿Cuál es el valor de la propiedad LoadBearing para este elemento?
```

Cuando hay un elemento seleccionado en el árbol, el asistente lo usa automáticamente como referencia sin necesidad de indicar un identificador.

### Ejemplos: cálculos sobre el modelo

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

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El árbol aparece vacío | El archivo IFC no tiene jerarquía espacial | Verifica el archivo con otro visor IFC |
| La tabla de propiedades está vacía | El elemento no tiene PSets asignados | Normal en elementos genéricos |
| La consola IA no responde (Ollama) | Ollama no ha arrancado o el modelo no está creado | Espera unos segundos; si persiste, usa **Recrear modelo ifc-assistant** en ⚙ Configuración |
| Error de clave API | Clave no guardada o incorrecta (Claude, ChatGPT o Gemini) | Abre **⚙ Configuración**, cambia de backend y vuelve a introducir la clave |
| El asistente no encuentra el archivo IFC | El archivo no está en el directorio de trabajo ni en el directorio de proyecto | Configura el directorio de proyecto o ejecuta `appcli` desde la carpeta del archivo |
| Error al abrir el archivo | Archivo IFC corrupto o versión no soportada | Prueba con otro archivo |
| Ollama tarda en responder | El modelo está cargando por primera vez | Espera unos segundos; las respuestas siguientes serán más rápidas |

