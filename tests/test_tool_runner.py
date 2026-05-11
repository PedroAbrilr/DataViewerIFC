"""Tests unitarios para ai/tool_runner.py."""

from unittest.mock import MagicMock

import pytest

from dataviewerifc.ai.tool_runner import ToolRunner, _SYSTEM_BASE
from dataviewerifc.ai.backends.base import ChatResponse, ToolCall
from dataviewerifc.plugins.registry import ToolRegistry


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _elem(nombre="Muro", tipo="IfcWall", gid="abc123"):
    e = MagicMock()
    e.is_a.return_value = tipo
    e.get_info.return_value = {"Name": nombre, "GlobalId": gid}
    return e


def _props():
    return [{"pset": "Pset_WallCommon", "props": [
        {"nombre": "IsExternal", "valor": "True", "unidad": ""},
    ]}]


def _make_tool(name, execute_return="ok", last_ids=None):
    t = MagicMock()
    t.name = name
    t.schema = {"type": "function", "function": {"name": name}}
    t.execute.return_value = execute_return
    t.last_ids = last_ids or []
    return t


def _registry(*tools):
    reg = ToolRegistry()
    for t in tools:
        reg.register(t if not isinstance(t, str) else _make_tool(t))
    return reg


def _runner(registry_base=None, registry_seleccion=None):
    return ToolRunner(backend=MagicMock(),
                      registry_base=registry_base,
                      registry_seleccion=registry_seleccion)


# ------------------------------------------------------------------
# set_archivo
# ------------------------------------------------------------------

def test_set_archivo_actualiza_contexto():
    r = _runner()
    r.set_archivo("edificio.ifc", 150)
    assert "edificio.ifc" in r.contexto_archivo
    assert "150" in r.contexto_archivo


# ------------------------------------------------------------------
# set_seleccion
# ------------------------------------------------------------------

def test_set_seleccion_vacia_limpia():
    r = _runner()
    r.set_seleccion([], [])
    assert r.contexto_seleccion == ""


def test_set_seleccion_un_elemento():
    r = _runner()
    r.set_seleccion([_elem("Muro-1", "IfcWall")], _props())
    assert "Muro-1" in r.contexto_seleccion
    assert "IfcWall" in r.contexto_seleccion


def test_set_seleccion_varios_elementos():
    r = _runner()
    r.set_seleccion([_elem(f"E{i}") for i in range(5)], [])
    assert "5" in r.contexto_seleccion


# ------------------------------------------------------------------
# _tools_disponibles
# ------------------------------------------------------------------

def test_tools_sin_registries():
    assert _runner()._tools_disponibles() == []


def test_tools_con_registry_base():
    r = _runner(registry_base=_registry("buscar_elementos"))
    nombres = [t["function"]["name"] for t in r._tools_disponibles()]
    assert "buscar_elementos" in nombres


def test_tools_con_seleccion_incluye_registry_seleccion():
    r = _runner(registry_seleccion=_registry("obtener_seleccion"))
    r._elementos = [_elem()]
    nombres = [t["function"]["name"] for t in r._tools_disponibles()]
    assert "obtener_seleccion" in nombres


def test_tools_sin_elementos_no_incluye_registry_seleccion():
    r = _runner(registry_base=_registry("buscar_elementos"),
                registry_seleccion=_registry("obtener_seleccion"))
    nombres = [t["function"]["name"] for t in r._tools_disponibles()]
    assert "buscar_elementos" in nombres
    assert "obtener_seleccion" not in nombres


# ------------------------------------------------------------------
# _build_context_prefix
# ------------------------------------------------------------------

def test_build_context_prefix_contiene_base():
    assert "IFC" in _SYSTEM_BASE


def test_build_context_prefix_incluye_archivo():
    r = _runner()
    r.set_archivo("test.ifc", 10)
    assert "test.ifc" in r._build_context_prefix()


def test_build_context_prefix_con_seleccion():
    r = _runner()
    r._elementos = [_elem()]
    r.contexto_seleccion = "Elemento seleccionado: Muro (IfcWall)"
    assert "Muro" in r._build_context_prefix()


def test_build_context_prefix_sin_archivo():
    r = _runner()
    assert "No hay ningún archivo IFC cargado" in r._build_context_prefix()


# ------------------------------------------------------------------
# _ejecutar
# ------------------------------------------------------------------

def test_ejecutar_delega_a_registry_base():
    tool = _make_tool("buscar_elementos", execute_return="resultado ifc")
    r = _runner(registry_base=_registry(tool))
    assert r._ejecutar("buscar_elementos", {"tipo": "IfcWall"}) == "resultado ifc"
    tool.execute.assert_called_once_with({"tipo": "IfcWall"})


def test_ejecutar_delega_a_registry_seleccion():
    tool = _make_tool("obtener_seleccion", execute_return="selección ok")
    r = _runner(registry_seleccion=_registry(tool))
    assert r._ejecutar("obtener_seleccion", {}) == "selección ok"


def test_ejecutar_seleccion_tiene_prioridad_sobre_base():
    base_tool = _make_tool("obtener_seleccion", execute_return="desde base")
    sel_tool  = _make_tool("obtener_seleccion", execute_return="desde seleccion")
    # No podemos registrar el mismo nombre en el mismo registry, usamos dos
    r = _runner(registry_base=_registry(base_tool),
                registry_seleccion=_registry(sel_tool))
    assert r._ejecutar("obtener_seleccion", {}) == "desde seleccion"


def test_ejecutar_herramienta_no_disponible():
    r = _runner()
    assert "no disponible" in r._ejecutar("herramienta_x", {})


def test_ejecutar_dispara_on_seleccionar():
    tool = _make_tool("buscar_elementos", execute_return="2 encontrados",
                      last_ids=["id1", "id2"])
    r = _runner(registry_base=_registry(tool))
    cb = MagicMock()
    r.on_seleccionar = cb
    r._ejecutar("buscar_elementos", {})
    cb.assert_called_once_with(["id1", "id2"])


def test_ejecutar_no_dispara_on_seleccionar_si_last_ids_vacio():
    tool = _make_tool("buscar_elementos", execute_return="nada", last_ids=[])
    r = _runner(registry_base=_registry(tool))
    cb = MagicMock()
    r.on_seleccionar = cb
    r._ejecutar("buscar_elementos", {})
    cb.assert_not_called()


# ------------------------------------------------------------------
# chat — flujo principal
# ------------------------------------------------------------------

def test_chat_sin_tools_stream():
    backend = MagicMock()
    backend.chat_stream.return_value = iter(["Hola ", "mundo"])
    r = ToolRunner(backend=backend)
    tokens = []
    r.chat("pregunta", on_token=tokens.append)
    assert "".join(tokens) == "Hola mundo"


def test_chat_con_tool_call():
    backend = MagicMock()
    tc = ToolCall(id="t1", name="estado_app", arguments={})
    backend.chat_turn.side_effect = [
        ChatResponse(tool_calls=[tc]),
        ChatResponse(content="respuesta final", tool_calls=[]),
    ]
    backend.make_assistant_message.return_value = {"role": "assistant"}
    backend.make_tool_message.return_value = {"role": "tool"}

    tool = _make_tool("estado_app", execute_return="sin archivo")
    r = ToolRunner(backend=backend, registry_base=_registry(tool))

    tokens = []
    r.chat("pregunta", on_token=tokens.append)
    assert "respuesta final" in "".join(tokens)
    tool.execute.assert_called_once_with({})


def test_chat_should_stop_antes_de_tool():
    backend = MagicMock()
    tc = ToolCall(id="t1", name="estado_app", arguments={})
    backend.chat_turn.return_value = ChatResponse(tool_calls=[tc])
    backend.make_assistant_message.return_value = {}

    tool = _make_tool("estado_app")
    r = ToolRunner(backend=backend, registry_base=_registry(tool))

    tokens = []
    r.chat("pregunta", on_token=tokens.append, should_stop=lambda: True)
    assert tokens == []


def test_chat_on_tool_call_callback():
    backend = MagicMock()
    tc = ToolCall(id="t1", name="estado_app", arguments={"x": 1})
    backend.chat_turn.side_effect = [
        ChatResponse(tool_calls=[tc]),
        ChatResponse(tool_calls=[]),
    ]
    backend.make_assistant_message.return_value = {}
    backend.make_tool_message.return_value = {}
    backend.chat_stream.return_value = iter([])

    tool = _make_tool("estado_app", execute_return="ok")
    r = ToolRunner(backend=backend, registry_base=_registry(tool))

    tool_calls_recibidos = []
    r.chat("pregunta", on_token=lambda t: None,
           on_tool_call=lambda n, a: tool_calls_recibidos.append((n, a)))
    assert tool_calls_recibidos == [("estado_app", {"x": 1})]


def test_chat_error_backend_notifica():
    backend = MagicMock()
    backend.chat_stream.side_effect = RuntimeError("fallo de red")
    r = ToolRunner(backend=backend)
    tokens = []
    r.chat("pregunta", on_token=tokens.append)
    assert "Error" in "".join(tokens)
