"""Tests unitarios para plugins/base.py (protocolo Tool)."""

import pytest
from appcli.plugins.base import Tool


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

class _ToolCompleto:
    def __init__(self):
        self.name = "herramienta_x"
        self.schema = {"type": "function", "function": {"name": "herramienta_x"}}

    def execute(self, args: dict) -> str:
        return "ok"


class _ToolSinExecute:
    def __init__(self):
        self.name = "sin_execute"
        self.schema = {}


class _ToolConLastIds:
    def __init__(self):
        self.name = "con_ids"
        self.schema = {}
        self.last_ids: list[str] = []

    def execute(self, args: dict) -> str:
        self.last_ids = ["id1", "id2"]
        return "2 encontrados"


# ------------------------------------------------------------------
# isinstance — Python 3.13: solo comprueba métodos, no atributos de datos
# ------------------------------------------------------------------

def test_isinstance_clase_completa_pasa():
    assert isinstance(_ToolCompleto(), Tool)


def test_isinstance_clase_sin_execute_falla():
    assert not isinstance(_ToolSinExecute(), Tool)


def test_tool_es_runtime_checkable():
    # En protocolos no runtime_checkable, isinstance lanza TypeError.
    # Si llega aquí sin excepción, el decorador está presente.
    try:
        isinstance(object(), Tool)
    except TypeError:
        pytest.fail("Tool no es runtime_checkable")


# ------------------------------------------------------------------
# Atributos name y schema — se comprueban con hasattr, no isinstance
# (Python 3.13 no los verifica en isinstance)
# ------------------------------------------------------------------

def test_tool_completo_tiene_name_y_schema():
    t = _ToolCompleto()
    assert hasattr(t, "name")
    assert hasattr(t, "schema")


def test_tool_sin_execute_carece_de_execute():
    assert not hasattr(_ToolSinExecute(), "execute")


# ------------------------------------------------------------------
# last_ids — atributo opcional, acceso via getattr
# ------------------------------------------------------------------

def test_last_ids_no_requerido_en_protocolo():
    t = _ToolCompleto()
    assert isinstance(t, Tool)
    assert getattr(t, "last_ids", []) == []


def test_last_ids_accesible_si_presente():
    t = _ToolConLastIds()
    assert isinstance(t, Tool)
    t.execute({})
    assert getattr(t, "last_ids", []) == ["id1", "id2"]
