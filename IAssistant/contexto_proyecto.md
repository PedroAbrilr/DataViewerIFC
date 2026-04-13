# Contexto del proyecto: AppCLI — IFC Viewer con IA local

## Qué es este proyecto

Aplicación de escritorio en Python para **explorar archivos IFC** (Industry Foundation Classes, el formato estándar de intercambio en BIM). El usuario abre un archivo `.ifc`, navega su jerarquía de elementos y consulta sus propiedades. Una consola integrada permite preguntas en lenguaje natural mediante **Ollama** en local.

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11+ |
| Interfaz gráfica | Tkinter (stdlib) + ttk + ttkthemes |
| Tema visual | equilux (oscuro, plano, moderno) |
| Lectura de IFC | ifcopenshell 0.8.4 |
| IA local | ollama 0.6.1 |
| Tests | pytest |
| Empaquetado | setuptools + pyproject.toml |
| Entorno virtual | `.venv/` en la raíz del proyecto |

## Estado actual del proyecto

- Carga de archivos IFC **implementada y funcional**.
- Árbol de jerarquía espacial **implementado y funcional**.
- Tabla de propiedades agrupada por PSet con columna de unidades **implementada**.
- Tema visual oscuro con `ttkthemes` (equilux) **aplicado**.
- Barra de herramientas superior y barra de estado inferior **implementadas**.
- Márgenes interiores en el layout principal **aplicados**.
- Consola IA: esqueleto pendiente de conectar con Ollama.

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
│  │  CONSOLA IA                                    │  │
│  │  ┌──────────────────────────────────┐ [Enviar] │  │
│  │  └──────────────────────────────────┘          │  │
│  └─────────────────────────────────────────────────┘  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
├──────────────────────────────────────────────────────┤
│  42 elementos cargados · Muro exterior [IfcWall]     │  ← statusbar
└──────────────────────────────────────────────────────┘
```

## Estructura de archivos

```
AppCLI/
├── pyproject.toml              # Dependencias y metadatos
├── .gitignore
├── .venv/                      # Entorno virtual (no versionar)
├── docs/
│   └── manual_usuario.md
├── tests/
│   └── __init__.py
├── IAssistant/                 # Archivos de trabajo del asistente IA
└── src/
    └── appcli/
        ├── main.py             # Punto de entrada
        ├── ui/
        │   ├── theme.py        # Paleta, fuentes y estilos ttk centralizados
        │   ├── app.py          # Ventana principal, toolbar, statusbar, coordinación
        │   ├── tree_panel.py   # Árbol jerárquico IFC
        │   ├── props_panel.py  # Tabla de propiedades por PSet
        │   └── ai_console.py   # Consola de IA
        ├── ifc/
        │   └── loader.py       # IFCLoader: carga y parseo IFC
        └── ai/
            └── ollama_client.py # OllamaClient: query() y stream()
```
