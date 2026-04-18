# Contexto del proyecto: AppCLI — IFC Viewer con IA local

## Qué es este proyecto

Aplicación de escritorio en Python para **explorar archivos IFC** (Industry Foundation Classes, el formato estándar de intercambio en BIM). El usuario abre un archivo `.ifc`, navega su jerarquía de elementos y consulta sus propiedades. Una consola integrada permite preguntas en lenguaje natural mediante **Ollama** en local con soporte de **tool calling**.

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

## Estado actual del proyecto (260417)

- Carga de archivos IFC **implementada y funcional**.
- Árbol de jerarquía espacial **implementado y funcional**.
- Tabla de propiedades agrupada por PSet con columna de unidades **implementada**.
- Multiselección en el árbol con propiedades fusionadas (valores comunes / "varios") **implementada**.
- Tema visual oscuro con `ttkthemes` (equilux) **aplicado**.
- Barra de herramientas superior y barra de estado inferior **implementadas**.
- Consola IA conectada a Ollama **implementada y funcional** (streaming).
- **Tool calling IFC completamente implementado y funcional**:
  - 7 herramientas de consulta IFC activas (buscar, contar, propiedades, plantas, área, nombre)
  - Herramienta `obtener_seleccion` con modos reducido/agrupado/estadistico
  - Contexto pasivo reducido a una línea (nombre y tipo del elemento activo)
  - Botón "Detener" para cancelar respuestas colgadas
  - Carga de propiedades en hilo secundario (no bloquea la UI al seleccionar)
- Modelo personalizado `ifc-assistant` con system prompt especializado en BIM/IFC.
- Ollama portable (`appcli/bin/ollama`) gestionado automáticamente por la app.
- Distribución por wheel con datos incluidos (`appcli/bin/ollama`, `appcli/data/`).

## Arquitectura de módulos

```
AppCLI/
└── src/appcli/
    ├── ui/
    │   ├── theme.py          # Paleta, fuentes y estilos ttk
    │   ├── app.py            # Ventana principal; coordina paneles y capas
    │   ├── tree_panel.py     # Árbol jerárquico IFC (multiselección)
    │   ├── props_panel.py    # Tabla de propiedades por PSet
    │   └── ai_console.py     # Consola IA — delega en ToolRunner
    ├── ifc/
    │   ├── loader.py         # IFCLoader: carga, árbol, propiedades
    │   └── query.py          # Funciones IFC puras de consulta
    └── ai/
        ├── ollama_client.py  # Gestión del servidor Ollama + query/stream
        ├── ifc_tools.py      # Schemas JSON + ejecutor de herramientas IFC
        └── tool_runner.py    # Contexto + bucle tool calling + obtener_seleccion
```

## Flujo de tool calling

```
Usuario escribe → AIConsole → ToolRunner.chat()
    │
    ├─ System prompt: base + archivo IFC + elemento seleccionado (1 línea)
    ├─ Tools: 7 herramientas IFC + obtener_seleccion (si hay selección)
    │
    └─ Bucle (no-streaming):
         Ollama → tool_calls? → IFCTools.ejecutar() o _fmt_seleccion()
                               → añadir resultado → Ollama → …
         Sin tool_calls → respuesta final en streaming → on_token()
```

## Herramientas disponibles en la consola IA

| Herramienta | Cuándo la usa el modelo |
|---|---|
| `obtener_seleccion(modo)` | Preguntas sobre el elemento activo (reducido/agrupado/estadistico) |
| `buscar_elementos` | Listar elementos de un tipo IFC |
| `contar_elementos` | Contar elementos de un tipo |
| `obtener_propiedades` | Propiedades de un elemento por GlobalId (de búsquedas) |
| `listar_plantas` | Plantas del edificio |
| `elementos_de_planta` | Elementos de una planta concreta |
| `calcular_area_total` | Suma de áreas por tipo |
| `buscar_por_nombre` | Búsqueda por nombre parcial |

## Posibles próximos pasos

- Herramientas para controlar la aplicación (abrir archivo, seleccionar elemento en árbol)
- Tests unitarios para `ifc/query.py` e `ifc_tools.py`
- Mejorar modelo base (llama3.2 o mistral-nemo tienen mejor soporte de tool calling)
- Actualizar manual de usuario con las nuevas capacidades de la consola IA
- Generar nuevo wheel de distribución
