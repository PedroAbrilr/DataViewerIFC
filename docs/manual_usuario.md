# AppCLI — Manual de usuario

## ¿Qué es AppCLI?

AppCLI es una aplicación de escritorio para explorar archivos IFC (Industry Foundation Classes), el formato estándar de intercambio de modelos BIM. Permite navegar la jerarquía de elementos de un edificio, consultar sus propiedades y realizar preguntas sobre el modelo mediante inteligencia artificial local.

---

## Requisitos

- Python 3.11 o superior.
- [Ollama](https://ollama.com) instalado y en ejecución para usar la consola IA.

---

## Instalación

```bash
# Clonar o descomprimir el proyecto
cd AppCLI

# Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -e .
```

---

## Arrancar la aplicación

```bash
source .venv/bin/activate
python -m appcli
```

---

## Interfaz

La ventana principal se divide en tres zonas:

```
┌────────────────────┬──────────────────────────────┐
│   Árbol de         │   Propiedades                │
│   elementos        │                              │
│                    │   ▼ Atributos                │
│   IfcProject       │     Name     │ ...  │        │
│   └ IfcSite        │   ▼ Pset_... │      │        │
│     └ Edificio     │     Área     │ 25.3 │ m²     │
│       └ Planta     │     ...      │ ...  │ ...    │
│         └ Muro     │                              │
├────────────────────┴──────────────────────────────┤
│  Consola IA                                       │
│  ┌────────────────────────────────────┐ [Enviar]  │
│  │ Escribe tu pregunta aquí...        │           │
│  └────────────────────────────────────┘           │
└───────────────────────────────────────────────────┘
```

### Árbol de elementos (izquierda)
Muestra la jerarquía espacial del modelo IFC: proyecto → emplazamiento → edificio → plantas → elementos. Haz clic en cualquier nodo para ver sus propiedades.

### Tabla de propiedades (derecha)
Muestra las propiedades del elemento seleccionado, agrupadas por conjunto de propiedades (PSet). Cada fila indica el nombre de la propiedad, su valor y la unidad cuando corresponde.

### Consola IA (parte inferior)
Permite hacer preguntas en lenguaje natural sobre el modelo cargado. Requiere Ollama en ejecución (ver sección siguiente).

---

## Abrir un archivo IFC

1. En el menú superior, selecciona **Archivo → Abrir IFC…** (o pulsa `Ctrl+O`).
2. Elige el archivo `.ifc` en el explorador de archivos.
3. El árbol se poblará automáticamente con la jerarquía del modelo.

---

## Consola IA

La consola IA utiliza un modelo de lenguaje local a través de **Ollama**. Para usarla:

1. Asegúrate de que Ollama está en ejecución:
   ```bash
   ollama serve
   ```
2. Descarga el modelo si no lo tienes aún:
   ```bash
   ollama pull llama3.2
   ```
3. Escribe tu pregunta en el campo de texto y pulsa `Enter` o el botón **Enviar**.

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El árbol aparece vacío | El archivo IFC no tiene jerarquía espacial definida | Verifica el archivo con otro visor IFC |
| La tabla de propiedades está vacía | El elemento no tiene PSets asignados | Normal en elementos genéricos |
| La consola IA no responde | Ollama no está en ejecución | Ejecuta `ollama serve` |
| Error al abrir el archivo | Archivo IFC corrupto o versión no soportada | Prueba con otro archivo |
