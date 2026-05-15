Proyecto: DataViewerIFC
Etapa actual: Completado
Fase: —
Último commit: 1817b51 — 260515
Decisiones tomadas:
  - Renombrado AppCLI → DataViewerIFC (260504)
  - Sistema de plugins para herramientas IA (reemplaza ai/ifc_tools.py y ai/app_tools.py)
  - Multi-backend: Ollama, Claude, OpenAI, Gemini
  - Repositorio: https://github.com/PedroAbrilr/DataViewerIFC
Sesión 260510:
  - Venv recreado con Python 3.14.4 e ifcopenshell 0.8.5
  - 184 tests pasando (9 archivos)
  - IAssistant/ migrado a .claude/ y eliminado
  - .Claude/ (mayúscula) migrado a .claude/ y eliminado
  - Documentos de trabajo actualizados: namespaces appcli → dataviewerifc, arquitectura con plugins
Sesión 260511:
  Completado:
  - Tarea 7: cachear config.load y modelos_disponibles (commit 01bfa33)
  - Migración a API web de Ollama del sistema: eliminado binario portable, descarga de modelos
    y gestión de rutas; OllamaClient simplificado; modelo base configurable desde modelos del sistema
    (commit 1a41f84)
  - system_prompt.txt reducido a versión mínima; original conservado en system_prompt_referencia.txt
  - IAssistant/ eliminado (ya migrado a .claude/ en sesión anterior)
  Prueba: app arrancó correctamente; ifc-assistant creado desde cero con modelo base seleccionado en Config

Sesión 260512:
  Completado:
  - Corrección flujo Ollama primer uso (commit 186a37f):
    · ensure_running(): verifica si ifc-assistant existe antes de pedir ollama_base_model
    · _actualizar_combo(): limpia aviso si ollama.list() responde; no llama is_available() para Ollama
    · _recrear_modelo(): guarda contra combo vacío, pasa base_model explícitamente
    · recrear_modelo(): acepta base_model como parámetro
  - Memoria conversacional de sesión con compactación IA (commit bbe404b):
    · ToolRunner._historial: lista de últimos 5 exchanges (user + assistant)
    · ToolRunner._memoria_compactada: resumen IA de exchanges anteriores
    · Al llegar a 5 exchanges, la IA resume el historial (chat_stream con prompt de resumen)
    · El resumen se inyecta como par user/assistant al inicio de cada llamada
    · set_archivo() llama a limpiar_historial() al cargar nuevo IFC
    · Compactación falla silenciosamente (log warning) y vacía el historial de todas formas
Último commit: bbe404b — 260512 Memoria conversacional de sesión con compactación IA
Sesión 260515:
  Completado:
  - ollama_client.py: añadido _SUBPROCESS_FLAGS con CREATE_NO_WINDOW para Windows; propagado
    a todos los subprocess.Popen/run; nuevo método iniciar_servidor() que arranca ollama serve
    sin gestionar modelos
  - config_dialog.py: _actualizar_combo() ya no muestra error estático al fallar Ollama;
    lanza hilo con iniciar_servidor() y refresca el combo si tiene éxito
  Error menor anotado (sin corrección prevista):
  - ensure_running() muestra "Error: Ollama no está arrancado" cuando el binario ollama no está
    en el PATH (p.ej. Ollama en contenedor Podman del host, accedido desde toolbox de Fedora);
    el mensaje es impreciso pero el comportamiento funcional es correcto

Sesión 260515 — Prueba (cierre):
  - 168 tests pasando (0 fallidos)
  Correcciones aplicadas:
    · config_dialog.py: try/except TclError en callbacks _done de _recrear_modelo() y _arrancar_y_refrescar()
    · config_dialog.py: guarda de carrera movida antes de lanzar el hilo en _actualizar_combo(); rama else redundante eliminada
    · ollama_client.py: bucle for/else en iniciar_servidor() coherente con el resto del módulo
    · query.py: _normalizar_tipo renombrada a normalizar_tipo (ahora pública)
    · seleccion.py: _fmt_estadistico() captura excepciones de get_properties() por elemento
  Infos anotados sin corrección prevista:
    · IDs duplicados en Gemini multi-tool call
    · Ausencia de tests para OllamaClient
  Proyecto completado
