"""Tests unitarios para plugins/ifc/ (herramientas IFC simples)."""

from unittest.mock import MagicMock, patch

import pytest

from dataviewerifc.plugins.ifc.buscar import BuscarElementos, BuscarPorNombre, ContarElementos
from dataviewerifc.plugins.ifc.estructura import CalcularAreaTotal, ElementosDePlanta, ListarPlantas
from dataviewerifc.plugins.ifc.propiedades import ObtenerPropiedades


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _loader(modelo=True):
    mock = MagicMock()
    mock.model = MagicMock() if modelo else None
    return mock


_ELEM = {"id": "abc123", "nombre": "Muro norte", "tipo": "IfcWall"}
_PROPS = {
    "encontrado": True,
    "nombre": "Muro norte",
    "tipo": "IfcWall",
    "grupos": [{"pset": "Atributos", "props": [{"nombre": "Name", "valor": "Muro norte", "unidad": ""}]}],
}


# ------------------------------------------------------------------
# Sin modelo cargado — todas las tools devuelven el mismo aviso
# ------------------------------------------------------------------

@pytest.mark.parametrize("tool_cls,args", [
    (BuscarElementos, {"tipo": "IfcWall"}),
    (ContarElementos, {"tipo": "IfcWall"}),
    (BuscarPorNombre, {"texto": "muro"}),
    (ObtenerPropiedades, {"global_id": "abc"}),
    (ListarPlantas, {}),
    (ElementosDePlanta, {"planta": "PB"}),
    (CalcularAreaTotal, {"tipo": "IfcSlab"}),
])
def test_sin_modelo(tool_cls, args):
    t = tool_cls(_loader(modelo=False))
    assert "No hay ningún archivo IFC abierto" in t.execute(args)


# ------------------------------------------------------------------
# BuscarElementos
# ------------------------------------------------------------------

def test_buscar_elementos_con_resultados():
    t = BuscarElementos(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.buscar_por_tipo", return_value=[_ELEM]):
        resultado = t.execute({"tipo": "IfcWall"})
    assert "1 elemento(s)" in resultado
    assert "Muro norte" in resultado


def test_buscar_elementos_sin_resultados():
    t = BuscarElementos(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.buscar_por_tipo", return_value=[]):
        resultado = t.execute({"tipo": "IfcBeam"})
    assert "No se encontraron" in resultado


def test_buscar_elementos_actualiza_last_ids():
    t = BuscarElementos(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.buscar_por_tipo", return_value=[_ELEM]):
        t.execute({"tipo": "IfcWall"})
    assert t.last_ids == ["abc123"]


def test_buscar_elementos_last_ids_vacio_sin_resultados():
    t = BuscarElementos(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.buscar_por_tipo", return_value=[]):
        t.execute({"tipo": "IfcWall"})
    assert t.last_ids == []


def test_buscar_elementos_argumento_faltante():
    t = BuscarElementos(_loader())
    assert "Argumento requerido" in t.execute({})


def test_buscar_elementos_schema_nombre():
    assert BuscarElementos(_loader()).schema["function"]["name"] == "buscar_elementos"


# ------------------------------------------------------------------
# ContarElementos
# ------------------------------------------------------------------

def test_contar_elementos_devuelve_numero():
    t = ContarElementos(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.contar_por_tipo", return_value=7):
        resultado = t.execute({"tipo": "IfcWall"})
    assert "7" in resultado


def test_contar_elementos_cero():
    t = ContarElementos(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.contar_por_tipo", return_value=0):
        resultado = t.execute({"tipo": "IfcBeam"})
    assert "0" in resultado


def test_contar_elementos_argumento_faltante():
    t = ContarElementos(_loader())
    assert "Argumento requerido" in t.execute({})


# ------------------------------------------------------------------
# BuscarPorNombre
# ------------------------------------------------------------------

def test_buscar_por_nombre_con_resultados():
    t = BuscarPorNombre(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.buscar_por_nombre", return_value=[_ELEM]):
        resultado = t.execute({"texto": "norte"})
    assert "Muro norte" in resultado


def test_buscar_por_nombre_actualiza_last_ids():
    t = BuscarPorNombre(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.buscar_por_nombre", return_value=[_ELEM]):
        t.execute({"texto": "norte"})
    assert t.last_ids == ["abc123"]


def test_buscar_por_nombre_sin_resultados():
    t = BuscarPorNombre(_loader())
    with patch("dataviewerifc.plugins.ifc.buscar._q.buscar_por_nombre", return_value=[]):
        resultado = t.execute({"texto": "xyz"})
    assert "No se encontraron" in resultado


# ------------------------------------------------------------------
# ObtenerPropiedades
# ------------------------------------------------------------------

def test_obtener_propiedades_encontrado():
    t = ObtenerPropiedades(_loader())
    with patch("dataviewerifc.plugins.ifc.propiedades._q.obtener_propiedades", return_value=_PROPS):
        resultado = t.execute({"global_id": "abc123"})
    assert "Muro norte" in resultado
    assert "IfcWall" in resultado


def test_obtener_propiedades_no_encontrado():
    t = ObtenerPropiedades(_loader())
    with patch("dataviewerifc.plugins.ifc.propiedades._q.obtener_propiedades", return_value={"encontrado": False}):
        resultado = t.execute({"global_id": "inexistente"})
    assert "no encontrado" in resultado.lower()


def test_obtener_propiedades_argumento_faltante():
    t = ObtenerPropiedades(_loader())
    assert "Argumento requerido" in t.execute({})


# ------------------------------------------------------------------
# ListarPlantas
# ------------------------------------------------------------------

def test_listar_plantas_con_resultados():
    t = ListarPlantas(_loader())
    plantas = [{"id": "p1", "nombre": "Planta baja", "tipo": "IfcBuildingStorey"}]
    with patch("dataviewerifc.plugins.ifc.estructura._q.listar_plantas", return_value=plantas):
        resultado = t.execute({})
    assert "Planta baja" in resultado


def test_listar_plantas_vacio():
    t = ListarPlantas(_loader())
    with patch("dataviewerifc.plugins.ifc.estructura._q.listar_plantas", return_value=[]):
        resultado = t.execute({})
    assert "No se encontraron" in resultado


# ------------------------------------------------------------------
# ElementosDePlanta
# ------------------------------------------------------------------

def test_elementos_de_planta_con_resultados():
    t = ElementosDePlanta(_loader())
    with patch("dataviewerifc.plugins.ifc.estructura._q.elementos_de_planta", return_value=[_ELEM]):
        resultado = t.execute({"planta": "Planta baja"})
    assert "Muro norte" in resultado


def test_elementos_de_planta_actualiza_last_ids():
    t = ElementosDePlanta(_loader())
    with patch("dataviewerifc.plugins.ifc.estructura._q.elementos_de_planta", return_value=[_ELEM]):
        t.execute({"planta": "Planta baja"})
    assert t.last_ids == ["abc123"]


def test_elementos_de_planta_argumento_faltante():
    t = ElementosDePlanta(_loader())
    assert "Argumento requerido" in t.execute({})


# ------------------------------------------------------------------
# CalcularAreaTotal
# ------------------------------------------------------------------

def test_calcular_area_total():
    t = CalcularAreaTotal(_loader())
    with patch("dataviewerifc.plugins.ifc.estructura._q.calcular_area_total", return_value=42.5):
        resultado = t.execute({"tipo": "IfcSlab"})
    assert "42.5" in resultado
    assert "m²" in resultado


def test_calcular_area_total_argumento_faltante():
    t = CalcularAreaTotal(_loader())
    assert "Argumento requerido" in t.execute({})


# ------------------------------------------------------------------
# Schemas — nombre correcto en cada clase
# ------------------------------------------------------------------

@pytest.mark.parametrize("tool_cls,expected_name", [
    (BuscarElementos, "buscar_elementos"),
    (ContarElementos, "contar_elementos"),
    (BuscarPorNombre, "buscar_por_nombre"),
    (ObtenerPropiedades, "obtener_propiedades"),
    (ListarPlantas, "listar_plantas"),
    (ElementosDePlanta, "elementos_de_planta"),
    (CalcularAreaTotal, "calcular_area_total"),
])
def test_schema_nombre(tool_cls, expected_name):
    t = tool_cls(_loader())
    assert t.schema["function"]["name"] == expected_name
    assert t.name == expected_name
