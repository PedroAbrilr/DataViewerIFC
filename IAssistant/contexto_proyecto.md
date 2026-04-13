# Contexto del proyecto: AppCLI — IFC Viewer con IA local

## Qué es este proyecto

Aplicación de escritorio en Python para **explorar archivos IFC** (Industry Foundation Classes, el formato estándar de intercambio en BIM — Building Information Modeling). El usuario puede abrir un archivo `.ifc`, navegar su jerarquía de elementos constructivos y consultar sus propiedades. Una consola integrada permite hacer preguntas en lenguaje natural sobre el modelo mediante **Ollama** corriendo en local.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11+ |
| Interfaz gráfica | Tkinter (stdlib) + ttk |
| Lectura de IFC | ifcopenshell 0.8.4 |
| IA local | ollama 0.6.1 (cliente Python) |
| Empaquetado | setuptools + pyproject.toml |
| Entorno virtual | `.venv/` en la raíz del proyecto |

## Estado actual del proyecto

El proyecto está en fase de **esqueleto estructural**. Las clases y módulos existen con sus interfaces definidas (firmas de métodos y docstrings) pero **sin lógica implementada**. Es el punto de partida para el desarrollo.

---

## Layout de la interfaz

```
┌─────────────────────────────────────────────────┐
│                  AppCLI — IFC Viewer             │
├──────────────────┬──────────────────────────────┤
│                  │                              │
│   Árbol IFC      │   Tabla de propiedades       │
│   (TreePanel)    │   (PropsPanel)               │
│                  │                              │
│  Jerarquía de    │  Clave | Valor               │
│  elementos:      │  ──────┼──────               │
│  Proyecto        │  Name  │ Muro exterior        │
│  └ Edificio      │  Type  │ IfcWall              │
│    └ Planta      │  ...   │ ...                  │
│      └ Muro      │                              │
│        └ ...     │                              │
├──────────────────┴──────────────────────────────┤
│  Consola IA (AIConsole)                         │
│  > ¿Cuántos muros hay en la planta baja?        │
│  < Hay 12 muros en la planta baja...            │
│  ┌─────────────────────────────────┐ [Enviar]   │
│  │ Escribe tu pregunta aquí...     │            │
│  └─────────────────────────────────┘            │
└─────────────────────────────────────────────────┘
```

---

## Estructura de archivos

```
AppCLI/
├── pyproject.toml              # Dependencias y metadatos
├── .gitignore
├── .venv/                      # Entorno virtual (no versionar)
├── IAssistant/                 # Documentación interna del asistente
└── src/
    └── appcli/
        ├── main.py             # Punto de entrada: instancia App y llama a run()
        ├── ui/
        │   ├── app.py          # Ventana principal, ensambla los tres paneles
        │   ├── tree_panel.py   # Panel árbol (ttk.Treeview)
        │   ├── props_panel.py  # Panel propiedades (ttk.Treeview en modo tabla)
        │   └── ai_console.py   # Consola IA: área de texto + campo de entrada
        ├── ifc/
        │   └── loader.py       # IFCLoader: open(), get_tree(), get_properties()
        └── ai/
            └── ollama_client.py # OllamaClient: query(), stream()
```
