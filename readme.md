# AppCLI — Manual de usuario v1.1

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
pip install https://github.com/PedroAbrilr/ifc_IA_CLI/releases/latest/download/appcli-1.1.0-py3-none-any.whl
```

El paquete incluye todas las dependencias necesarias (ifcopenshell, ollama, anthropic, openai, ttkthemes).

### 3. Ejecutar el instalador

El instalador configura el backend de IA local (Ollama) y el acceso directo de escritorio:

```bash
appcli-install
```

El instalador realiza los pasos siguientes:

1. Comprueba si Ollama ya está instalado en el sistema. Si no lo está, lo descarga e instala automáticamente en el directorio de datos de AppCLI.
2. Muestra un menú para elegir el modelo de lenguaje base:
   - **Qwen 2.5 1.5B** — ligero, ~1 GB, recomendado para equipos con poca RAM.
   - **Qwen 2.5 3B** — equilibrio calidad/recursos, ~2 GB.
   - **Qwen 2.5 7B** — mejor calidad, ~5 GB.
   - **Llama 3.2 3B** — buen soporte de herramientas, ~2 GB.
   - **Mistral 7B** — alta calidad, ~5 GB.
   - También puedes introducir el nombre de cualquier otro modelo disponible en Ollama.
3. Descarga el modelo elegido y crea el asistente personalizado `ifc-assistant` con instrucciones especializadas en BIM/IFC.
4. Guarda la configuración en el directorio de configuración de usuario.
5. Instala el acceso directo de escritorio (solo Linux).

> Si solo vas a usar los backends de IA en la nube (Claude o ChatGPT), puedes omitir `appcli-install`. La aplicación funciona sin Ollama.

### Rutas de instalación por sistema operativo

| Elemento | Linux | macOS | Windows |
|---|---|---|---|
| Configuración | `~/.config/appcli/` | `~/.config/appcli/` | `%APPDATA%\appcli\` |
| Binario Ollama | `~/.local/share/appcli/ollama/` | `~/.local/share/appcli/ollama/` | `%LOCALAPPDATA%\appcli\ollama\` |
| Modelos Ollama | `~/.local/share/appcli/ollama/models/` | `~/.local/share/appcli/ollama/models/` | `%LOCALAPPDATA%\appcli\ollama\models\` |
| Acceso directo | `~/.local/share/applications/` | — | — |

---

## Arrancar la aplicación

```bash
appcli
```

O bien desde el acceso directo del escritorio (Linux) o el menú de inicio (Windows/macOS, si se ha instalado manualmente).

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

AppCLI soporta tres backends de IA que pueden cambiarse en cualquier momento desde **⚙ Configuración**:

### Ollama (local) — recomendado para privacidad

Ejecuta el modelo de lenguaje directamente en tu equipo. No envía ningún dato a servidores externos. El modelo `ifc-assistant` es un asistente personalizado con instrucciones especializadas en BIM/IFC, creado durante la instalación.

- **Ventaja**: privacidad total, no requiere conexión a internet después de la instalación.
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

---

## Ventana de configuración

Pulsa **⚙ Configuración** en la barra superior para abrir la ventana de configuración.

### Sección «Asistente IA»

Permite seleccionar el backend activo y el modelo concreto a utilizar. Al cambiar de backend:

- Se muestra un aviso si el backend no está disponible (por ejemplo, si falta la clave de API o Ollama no está instalado).
- Si seleccionas Claude o ChatGPT por primera vez y no hay clave de API guardada, la aplicación la pedirá automáticamente al pulsar **Aplicar**.
- La clave se guarda de forma local en el archivo de configuración del usuario y no se incluye en ninguna distribución.

Al pulsar **Aplicar**, el cambio de backend tiene efecto inmediatamente sin necesidad de reiniciar la aplicación.

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
| La consola IA no responde (Ollama) | Ollama no está instalado o no arranca | Ejecuta `appcli-install` |
| Error de clave API (Claude o ChatGPT) | Clave no guardada o incorrecta | Abre **⚙ Configuración**, cambia de backend y vuelve a introducir la clave |
| El asistente no encuentra el archivo IFC | El archivo no está en el directorio de trabajo | Ejecuta `appcli` desde el directorio donde se encuentra el archivo |
| Error al abrir el archivo | Archivo IFC corrupto o versión no soportada | Prueba con otro archivo |
| Ollama tarda en responder | El modelo está cargando por primera vez | Espera unos segundos; las respuestas siguientes serán más rápidas |
