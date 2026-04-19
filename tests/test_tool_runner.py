"""Tests unitarios para ai/tool_runner.py."""

from unittest.mock import MagicMock
import pytest

from appcli.ai.tool_runner import ToolRunner
from appcli.ai.backends.base import ChatResponse, ToolCall


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


def _props_numericas():
    return [{"pset": "Qto_WallBaseQuantities", "props": [
        {"nombre": "Length", "valor": "3.5", "unidad": "m"},
        {"nombre": "Height", "valor": "2.8", "unidad": "m"},
    ]}]


def _runner(ifc_tools=None):
    return ToolRunner(backend=MagicMock(), ifc_tools=ifc_tools)


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

def test_tools_sin_nada():
    assert _runner()._tools_disponibles() == []


def test_tools_con_seleccion_incluye_obtener_seleccion():
    r = _runner()
    r._elementos = [_elem()]
    nombres = [t["function"]["name"] for t in r._tools_disponibles()]
    assert "obtener_seleccion" in nombres


def test_tools_con_app_tools():
    r = _runner()
    app = MagicMock()
    app.definiciones.return_value = [{"type": "function", "function": {"name": "estado_app"}}]
    r.set_app_tools(app)
    nombres = [t["function"]["name"] for t in r._tools_disponibles()]
    assert "estado_app" in nombres


def test_tools_con_ifc_tools():
    ifc = MagicMock()
    ifc.definiciones.return_value = [{"type": "function", "function": {"name": "buscar_elementos"}}]
    r = _runner(ifc_tools=ifc)
    nombres = [t["function"]["name"] for t in r._tools_disponibles()]
    assert "buscar_elementos" in nombres


# ------------------------------------------------------------------
# _build_system
# ------------------------------------------------------------------

def test_build_system_contiene_base():
    assert "BIM" in _runner()._build_system(False)


def test_build_system_incluye_archivo():
    r = _runner()
    r.set_archivo("test.ifc", 10)
    assert "test.ifc" in r._build_system(False)


def test_build_system_con_seleccion_y_herramientas():
    r = _runner()
    r._elementos = [_elem()]
    r.contexto_seleccion = "Elemento seleccionado: Muro (IfcWall)"
    assert "obtener_seleccion" in r._build_system(True)


def test_build_system_sin_seleccion_con_herramientas():
    r = _runner()
    system = r._build_system(True)
    assert "modelo IFC completo" in system


# ------------------------------------------------------------------
# _fmt_seleccion
# ------------------------------------------------------------------

def test_fmt_sin_elementos():
    assert "No hay ningún elemento" in _runner()._fmt_seleccion("reducido")


def test_fmt_reducido_un_elemento():
    r = _runner()
    r._elementos = [_elem("Muro-A", "IfcWall")]
    r._props = _props()
    result = r._fmt_seleccion("reducido")
    assert "Muro-A" in result
    assert "Pset_WallCommon" in result


def test_fmt_reducido_varios():
    r = _runner()
    r._elementos = [_elem(f"E{i}") for i in range(3)]
    r._props = _props()
    assert "3 elementos" in r._fmt_seleccion("reducido")


def test_fmt_reducido_trunca_mas_de_20():
    r = _runner()
    r._elementos = [_elem(f"E{i}") for i in range(25)]
    r._props = _props()
    result = r._fmt_seleccion("reducido")
    assert "más" in result


def test_fmt_agrupado_un_elemento():
    r = _runner()
    r._elementos = [_elem("Muro-A", "IfcWall", "gid-xyz")]
    r._props = _props()
    result = r._fmt_seleccion("agrupado")
    assert "gid-xyz" in result
    assert "IsExternal" in result


def test_fmt_agrupado_varios_elementos():
    r = _runner()
    r._elementos = [_elem(f"E{i}") for i in range(2)]
    r._props = [{"pset": "Pset_WallCommon", "props": [
        {"nombre": "IsExternal", "valor": "True", "unidad": "", "varios": False},
    ]}]
    result = r._fmt_seleccion("agrupado")
    assert "combinadas" in result


def test_fmt_estadistico_un_elemento_delega_agrupado():
    r = _runner()
    r._elementos = [_elem("Muro-A", "IfcWall", "gid-1")]
    r._props = _props()
    result = r._fmt_seleccion("estadistico")
    assert "gid-1" in result


def test_fmt_estadistico_sin_ifc_tools():
    r = _runner(ifc_tools=None)
    r._elementos = [_elem(), _elem()]
    r._props = _props()
    result = r._fmt_seleccion("estadistico")
    assert "No hay modelo IFC" in result


def test_fmt_estadistico_propiedades_numericas():
    ifc_tools = MagicMock()
    loader = MagicMock()
    loader.get_properties.return_value = _props_numericas()
    ifc_tools._loader = loader
    r = _runner(ifc_tools=ifc_tools)
    elems = [_elem(f"E{i}") for i in range(2)]
    r._elementos = elems
    r._props = _props_numericas()
    result = r._fmt_seleccion("estadistico")
    assert "mín" in result
    assert "Length" in result


# ------------------------------------------------------------------
# _ejecutar
# ------------------------------------------------------------------

def test_ejecutar_obtener_seleccion_sin_elementos():
    assert "No hay ningún elemento" in _runner()._ejecutar("obtener_seleccion", {})


def test_ejecutar_delega_a_ifc_tools():
    ifc = MagicMock()
    ifc.ejecutar.return_value = "resultado ifc"
    ifc._last_ids = []
    r = _runner(ifc_tools=ifc)
    assert r._ejecutar("buscar_elementos", {"tipo": "IfcWall"}) == "resultado ifc"
    ifc.ejecutar.assert_called_once_with("buscar_elementos", {"tipo": "IfcWall"})


def test_ejecutar_delega_a_app_tools():
    r = _runner()
    app = MagicMock()
    app.ejecutar.return_value = "estado ok"
    r.set_app_tools(app)
    assert r._ejecutar("estado_app", {}) == "estado ok"


def test_ejecutar_dispara_on_seleccionar():
    ifc = MagicMock()
    ifc.ejecutar.return_value = "2 encontrados"
    ifc._last_ids = ["id1", "id2"]
    r = _runner(ifc_tools=ifc)
    cb = MagicMock()
    r.on_seleccionar = cb
    r._ejecutar("buscar_elementos", {})
    cb.assert_called_once_with(["id1", "id2"])


def test_ejecutar_sin_modelo_ifc():
    r = _runner(ifc_tools=None)
    assert "No hay modelo IFC" in r._ejecutar("buscar_elementos", {})


# ------------------------------------------------------------------
# chat — flujo principal
# ------------------------------------------------------------------

def test_chat_sin_tools_stream():
    backend = MagicMock()
    backend.chat_stream.return_value = iter(["Hola ", "mundo"])
    r = ToolRunner(backend=backend, ifc_tools=None)
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

    app = MagicMock()
    app.definiciones.return_value = [{"type": "function", "function": {"name": "estado_app"}}]
    app.ejecutar.return_value = "sin archivo"

    r = ToolRunner(backend=backend, ifc_tools=None)
    r.set_app_tools(app)

    tokens = []
    r.chat("pregunta", on_token=tokens.append)
    assert "respuesta final" in "".join(tokens)
    app.ejecutar.assert_called_once_with("estado_app", {})


def test_chat_should_stop_antes_de_tool():
    backend = MagicMock()
    tc = ToolCall(id="t1", name="estado_app", arguments={})
    backend.chat_turn.return_value = ChatResponse(tool_calls=[tc])
    backend.make_assistant_message.return_value = {}

    app = MagicMock()
    app.definiciones.return_value = [{"type": "function", "function": {"name": "estado_app"}}]

    r = ToolRunner(backend=backend, ifc_tools=None)
    r.set_app_tools(app)

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

    app = MagicMock()
    app.definiciones.return_value = [{"type": "function", "function": {"name": "estado_app"}}]
    app.ejecutar.return_value = "ok"

    r = ToolRunner(backend=backend, ifc_tools=None)
    r.set_app_tools(app)

    tool_calls_recibidos = []
    r.chat("pregunta", on_token=lambda t: None,
           on_tool_call=lambda n, a: tool_calls_recibidos.append((n, a)))
    assert tool_calls_recibidos == [("estado_app", {"x": 1})]


def test_chat_error_backend_notifica():
    backend = MagicMock()
    backend.chat_stream.side_effect = RuntimeError("fallo de red")
    r = ToolRunner(backend=backend, ifc_tools=None)
    tokens = []
    r.chat("pregunta", on_token=tokens.append)
    assert "Error" in "".join(tokens)
