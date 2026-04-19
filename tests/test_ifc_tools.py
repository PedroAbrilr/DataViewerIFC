"""Tests unitarios para appcli.ai.ifc_tools.IFCTools."""

from unittest.mock import MagicMock, patch

import pytest

from appcli.ai.ifc_tools import IFCTools


@pytest.fixture
def loader():
    mock = MagicMock()
    mock.model = MagicMock()
    return mock


@pytest.fixture
def tools(loader):
    return IFCTools(loader)


# ------------------------------------------------------------------
# Sin modelo cargado
# ------------------------------------------------------------------

def test_sin_modelo(loader):
    loader.model = None
    t = IFCTools(loader)
    assert "No hay ningún archivo IFC abierto" in t.ejecutar("buscar_elementos", {"tipo": "IfcWall"})


# ------------------------------------------------------------------
# buscar_elementos
# ------------------------------------------------------------------

def test_buscar_elementos_con_resultados(tools):
    with patch("appcli.ai.ifc_tools._q.buscar_por_tipo") as mock_fn:
        mock_fn.return_value = [{"id": "abc", "nombre": "Muro", "tipo": "IfcWall"}]
        resultado = tools.ejecutar("buscar_elementos", {"tipo": "IfcWall"})
    assert "1 elemento(s)" in resultado
    assert "Muro" in resultado


def test_buscar_elementos_sin_resultados(tools):
    with patch("appcli.ai.ifc_tools._q.buscar_por_tipo", return_value=[]):
        resultado = tools.ejecutar("buscar_elementos", {"tipo": "IfcBeam"})
    assert "No se encontraron" in resultado


def test_buscar_elementos_argumento_faltante(tools):
    resultado = tools.ejecutar("buscar_elementos", {})
    assert "Argumento requerido" in resultado


# ------------------------------------------------------------------
# contar_elementos
# ------------------------------------------------------------------

def test_contar_elementos(tools):
    with patch("appcli.ai.ifc_tools._q.contar_por_tipo", return_value=5):
        resultado = tools.ejecutar("contar_elementos", {"tipo": "IfcWall"})
    assert "5" in resultado


def test_contar_elementos_cero(tools):
    with patch("appcli.ai.ifc_tools._q.contar_por_tipo", return_value=0):
        resultado = tools.ejecutar("contar_elementos", {"tipo": "IfcBeam"})
    assert "0" in resultado


# ------------------------------------------------------------------
# obtener_propiedades
# ------------------------------------------------------------------

def test_obtener_propiedades_encontrado(tools):
    datos = {
        "encontrado": True,
        "nombre": "Muro norte",
        "tipo": "IfcWall",
        "grupos": [{"pset": "Atributos", "props": [{"nombre": "Name", "valor": "Muro norte", "unidad": ""}]}],
    }
    with patch("appcli.ai.ifc_tools._q.obtener_propiedades", return_value=datos):
        resultado = tools.ejecutar("obtener_propiedades", {"global_id": "abc123"})
    assert "Muro norte" in resultado
    assert "IfcWall" in resultado


def test_obtener_propiedades_no_encontrado(tools):
    with patch("appcli.ai.ifc_tools._q.obtener_propiedades", return_value={"encontrado": False}):
        resultado = tools.ejecutar("obtener_propiedades", {"global_id": "inexistente"})
    assert "no encontrado" in resultado.lower()


# ------------------------------------------------------------------
# listar_plantas
# ------------------------------------------------------------------

def test_listar_plantas_con_resultados(tools):
    with patch("appcli.ai.ifc_tools._q.listar_plantas") as mock_fn:
        mock_fn.return_value = [{"id": "p1", "nombre": "Planta baja", "tipo": "IfcBuildingStorey"}]
        resultado = tools.ejecutar("listar_plantas", {})
    assert "Planta baja" in resultado


def test_listar_plantas_vacio(tools):
    with patch("appcli.ai.ifc_tools._q.listar_plantas", return_value=[]):
        resultado = tools.ejecutar("listar_plantas", {})
    assert "No se encontraron" in resultado


# ------------------------------------------------------------------
# elementos_de_planta
# ------------------------------------------------------------------

def test_elementos_de_planta(tools):
    with patch("appcli.ai.ifc_tools._q.elementos_de_planta") as mock_fn:
        mock_fn.return_value = [{"id": "w1", "nombre": "Muro", "tipo": "IfcWall"}]
        resultado = tools.ejecutar("elementos_de_planta", {"planta": "Planta baja"})
    assert "Muro" in resultado


# ------------------------------------------------------------------
# calcular_area_total
# ------------------------------------------------------------------

def test_calcular_area_total(tools):
    with patch("appcli.ai.ifc_tools._q.calcular_area_total", return_value=42.5):
        resultado = tools.ejecutar("calcular_area_total", {"tipo": "IfcSlab"})
    assert "42.5" in resultado
    assert "m²" in resultado


# ------------------------------------------------------------------
# buscar_por_nombre
# ------------------------------------------------------------------

def test_buscar_por_nombre(tools):
    with patch("appcli.ai.ifc_tools._q.buscar_por_nombre") as mock_fn:
        mock_fn.return_value = [{"id": "x1", "nombre": "Muro norte", "tipo": "IfcWall"}]
        resultado = tools.ejecutar("buscar_por_nombre", {"texto": "norte"})
    assert "Muro norte" in resultado


# ------------------------------------------------------------------
# Herramienta desconocida
# ------------------------------------------------------------------

def test_herramienta_desconocida(tools):
    resultado = tools.ejecutar("herramienta_inventada", {})
    assert "desconocida" in resultado.lower()


# ------------------------------------------------------------------
# definiciones
# ------------------------------------------------------------------

def test_definiciones_devuelve_lista(tools):
    defs = tools.definiciones()
    assert isinstance(defs, list)
    assert len(defs) == 8
    nombres = {d["function"]["name"] for d in defs}
    assert "buscar_elementos" in nombres
    assert "calcular_area_total" in nombres
