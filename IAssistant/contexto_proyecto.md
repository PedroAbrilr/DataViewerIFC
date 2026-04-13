# Contexto del proyecto: AppCLI — IFC Viewer con IA local

## Qué es este proyecto

Aplicación de escritorio en Python para **explorar archivos IFC** (Industry Foundation Classes, el formato estándar de intercambio en BIM). El usuario abre un archivo `.ifc`, navega su jerarquía de elementos y consulta sus propiedades. Una consola integrada permite preguntas en lenguaje natural mediante **Ollama** en local.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.13 (Fedora Linux) |
| Interfaz gráfica | Tkinter (stdlib) + ttk + ttkthemes |
| Tema visual | equilux (oscuro, plano, moderno) |
| Lectura de IFC | ifcopenshell 0.8.4 |
| IA local | ollama 0.6.1 — modelo `ifc-assistant` sobre `qwen2.5:1.5b` |
| Tests | pytest |
| Empaquetado | setuptools + pyproject.toml |
| Distribución | wheel (`python -m build --wheel`) |
| Entorno virtual | `.venv/` en la raíz del proyecto |

## Estado actual del proyecto

- Carga de archivos IFC **implementada y funcional**.
- Árbol de jerarquía espacial **implementado y funcional**.
- Tabla de propiedades agrupada por PSet con columna de unidades **implementada**.
- Tema visual oscuro con `ttkthemes` (equilux) **aplicado**.
- Barra de herramientas superior y barra de estado inferior **implementadas**.
- Consola IA conectada a Ollama **implementada y funcional** (streaming).
- Contexto dinámico del archivo IFC y del elemento seleccionado inyectado en cada consulta.
- Modelo personalizado `ifc-assistant` con system prompt especializado en BIM/IFC.
- El `Modelfile` usa un placeholder `{{MANUAL_USUARIO}}` que `OllamaClient` sustituye al crear el modelo leyendo `appcli/data/manual_usuario.md`.
- Ollama portable (`appcli/bin/ollama`) gestionado automáticamente por la app.
- Distribución por wheel con datos incluidos (`appcli/bin/ollama`, `appcli/data/`).

## Layout de la interfaz

```
┌──────────────────────────────────────────────────────┐
│  [Abrir IFC]  nombre_archivo.ifc       (toolbar)     │
├──────────────────────────────────────────────────────┤
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │ ← margen
│  ┌──────────────────┬─────────────────────────────┐  │
│  │  ESTRUCTURA      │  PROPIEDADES                │  │
│  │                  │  ▼ Atributos                │  │
│  │  IfcProject      │    Name     │ Muro  │       │  │
│  │  └ IfcSite       │    Tipo IFC │ IfcW… │       │  │
│  │    └ Edificio    │  ▼ Pset_... │       │       │  │
│  │      └ Planta    │    Área     │ 25.3  │ m²    │  │
│  │        └ Muro    │                             │  │
│  ├──────────────────┴─────────────────────────────┤  │
│  │  CONSOLA IA                    [ifc-assistant]  │  │
│  │  ▶ ¿Cuántas ventanas hay?                      │  │
│  │  Hay 24 ventanas (IfcWindow) en el modelo.     │  │
│  │  ┌──────────────────────────────────┐ [Enviar] │  │
│  │  └──────────────────────────────────┘          │  │
│  └─────────────────────────────────────────────────┘  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
├──────────────────────────────────────────────────────┤
│  42 elementos · Muro exterior [IfcWall]  v0.1        │ ← statusbar
└──────────────────────────────────────────────────────┘
```

## Estructura de archivos

```
AppCLI/
├── pyproject.toml              # Dependencias y metadatos
├── setup.cfg                   # Tag de plataforma del wheel (linux_x86_64)
├── Modelfile                   # Plantilla del modelo Ollama (con {{MANUAL_USUARIO}})
├── .gitignore
├── .venv/                      # Entorno virtual (no versionar)
├── dist/                       # Wheel generado (no versionar)
├── models/                     # Modelos descargados por Ollama (no versionar)
├── docs/
│   └── manual_usuario.md       # Manual de usuario (fuente de verdad)
├── tests/
│   └── __init__.py
├── IAssistant/                 # Archivos de trabajo del asistente IA
└── src/
    └── appcli/
        ├── main.py             # Punto de entrada
        ├── data/               # Datos incluidos en el wheel
        │   ├── Modelfile       # Copia del Modelfile (con placeholder)
        │   └── manual_usuario.md  # Copia del manual
        ├── bin/                # Binario portable de Ollama (no versionar)
        │   └── ollama
        ├── ui/
        │   ├── theme.py        # Paleta, fuentes y estilos ttk centralizados
        │   ├── app.py          # Ventana principal, toolbar, statusbar, coordinación
        │   ├── tree_panel.py   # Árbol jerárquico IFC
        │   ├── props_panel.py  # Tabla de propiedades por PSet
        │   └── ai_console.py   # Consola de IA con streaming
        ├── ifc/
        │   └── loader.py       # IFCLoader: carga y parseo IFC
        └── ai/
            └── ollama_client.py # OllamaClient: gestión de Ollama + query/stream
```
