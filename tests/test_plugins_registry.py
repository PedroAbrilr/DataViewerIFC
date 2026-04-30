"""Tests unitarios para plugins/registry.py (ToolRegistry)."""

import pytest
from appcli.plugins.registry import ToolRegistry


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_SCHEMA_BASE = {"type": "function", "function": {"name": "{name}", "description": "", "parameters": {}}}


def _make_tool(name: str, result: str = "ok"):
    schema = {"type": "function", "function": {"name": name, "description": "", "parameters": {}}}

    class _T:
        pass

    t = _T()
    t.name = name
    t.schema = schema
    t.execute = lambda args: result
    return t


def _registry(*names: str) -> ToolRegistry:
    r = ToolRegistry()
    for n in names:
        r.register(_make_tool(n))
    return r


# ------------------------------------------------------------------
# register
# ------------------------------------------------------------------

def test_register_añade_tool():
    r = ToolRegistry()
    t = _make_tool("herramienta_a")
    r.register(t)
    assert "herramienta_a" in r


def test_register_duplicado_lanza_ValueError():
    r = _registry("herramienta_a")
    with pytest.raises(ValueError):
        r.register(_make_tool("herramienta_a"))


def test_register_mensaje_error_contiene_nombre():
    r = _registry("herramienta_a")
    with pytest.raises(ValueError) as exc:
        r.register(_make_tool("herramienta_a"))
    assert "herramienta_a" in str(exc.value)


# ------------------------------------------------------------------
# execute
# ------------------------------------------------------------------

def test_execute_despacha_al_tool_correcto():
    r = _registry()
    r.register(_make_tool("herramienta_a", result="resultado_a"))
    assert r.execute("herramienta_a", {}) == "resultado_a"


def test_execute_nombre_desconocido_lanza_KeyError():
    r = _registry("herramienta_a")
    with pytest.raises(KeyError):
        r.execute("no_existe", {})


def test_execute_pasa_args_correctamente():
    recibidos = {}

    class _T:
        name = "captura"
        schema = {}

        def execute(self, args):
            recibidos.update(args)
            return "ok"

    r = ToolRegistry()
    r.register(_T())
    r.execute("captura", {"clave": "valor"})
    assert recibidos == {"clave": "valor"}


# ------------------------------------------------------------------
# schemas
# ------------------------------------------------------------------

def test_schemas_devuelve_lista_de_dicts():
    r = _registry("a", "b")
    schemas = r.schemas()
    assert isinstance(schemas, list)
    assert all(isinstance(s, dict) for s in schemas)


def test_schemas_orden_de_registro():
    r = _registry("primero", "segundo", "tercero")
    nombres = [s["function"]["name"] for s in r.schemas()]
    assert nombres == ["primero", "segundo", "tercero"]


def test_schemas_lista_vacia_si_no_hay_tools():
    assert ToolRegistry().schemas() == []


# ------------------------------------------------------------------
# get_tool
# ------------------------------------------------------------------

def test_get_tool_devuelve_instancia():
    t = _make_tool("herramienta_a")
    r = ToolRegistry()
    r.register(t)
    assert r.get_tool("herramienta_a") is t


def test_get_tool_desconocido_devuelve_None():
    assert _registry("herramienta_a").get_tool("no_existe") is None


# ------------------------------------------------------------------
# __contains__
# ------------------------------------------------------------------

def test_contains_verdadero():
    assert "herramienta_a" in _registry("herramienta_a")


def test_contains_falso():
    assert "no_existe" not in _registry("herramienta_a")


# ------------------------------------------------------------------
# __len__
# ------------------------------------------------------------------

def test_len_vacio():
    assert len(ToolRegistry()) == 0


def test_len_con_tools():
    assert len(_registry("a", "b", "c")) == 3


# ------------------------------------------------------------------
# names
# ------------------------------------------------------------------

def test_names_orden_de_registro():
    assert _registry("x", "y", "z").names() == ["x", "y", "z"]


def test_names_lista_vacia_si_no_hay_tools():
    assert ToolRegistry().names() == []


# ------------------------------------------------------------------
# last_ids — patrón getattr que usará el runner
# ------------------------------------------------------------------

def test_last_ids_accesible_via_getattr_si_presente():
    class _TConIds:
        name = "con_ids"
        schema = {}

        def execute(self, args):
            self.last_ids = ["id1", "id2"]
            return "ok"

    r = ToolRegistry()
    r.register(_TConIds())
    r.execute("con_ids", {})
    assert getattr(r.get_tool("con_ids"), "last_ids", []) == ["id1", "id2"]


def test_last_ids_vacio_si_no_presente():
    r = _registry("sin_ids")
    r.execute("sin_ids", {})
    assert getattr(r.get_tool("sin_ids"), "last_ids", []) == []
