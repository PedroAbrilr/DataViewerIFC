"""Tests unitarios para ai/app_tools.py."""

import pytest
from unittest.mock import MagicMock

from appcli.ai.app_tools import AppTools


def _make(archivo=None, cargar=None):
    on_cargar = cargar or MagicMock()
    return AppTools(MagicMock(return_value=archivo), on_cargar), on_cargar


# ------------------------------------------------------------------
# estado_app
# ------------------------------------------------------------------

def test_estado_sin_archivo():
    tools, _ = _make(archivo=None)
    assert "No hay ningún archivo IFC" in tools.ejecutar("estado_app", {})


def test_estado_con_archivo():
    tools, _ = _make(archivo="edificio.ifc")
    assert "edificio.ifc" in tools.ejecutar("estado_app", {})


# ------------------------------------------------------------------
# cargar_ifc — validaciones
# ------------------------------------------------------------------

def test_cargar_nombre_vacio():
    tools, _ = _make()
    assert "Indica el nombre" in tools.ejecutar("cargar_ifc", {"nombre": ""})


def test_cargar_nombre_con_slash():
    tools, _ = _make()
    assert "directorio de trabajo" in tools.ejecutar("cargar_ifc", {"nombre": "subdir/archivo.ifc"})


def test_cargar_nombre_con_backslash():
    tools, _ = _make()
    assert "directorio de trabajo" in tools.ejecutar("cargar_ifc", {"nombre": "sub\\archivo.ifc"})


# ------------------------------------------------------------------
# cargar_ifc — búsqueda de archivo
# ------------------------------------------------------------------

def test_cargar_archivo_encontrado(tmp_path, monkeypatch):
    (tmp_path / "edificio.ifc").touch()
    monkeypatch.chdir(tmp_path)
    on_cargar = MagicMock()
    tools = AppTools(MagicMock(return_value=None), on_cargar)
    result = tools.ejecutar("cargar_ifc", {"nombre": "edificio.ifc"})
    on_cargar.assert_called_once()
    assert "Cargando" in result


def test_cargar_sin_extension(tmp_path, monkeypatch):
    (tmp_path / "edificio.ifc").touch()
    monkeypatch.chdir(tmp_path)
    on_cargar = MagicMock()
    tools = AppTools(MagicMock(return_value=None), on_cargar)
    result = tools.ejecutar("cargar_ifc", {"nombre": "edificio"})
    on_cargar.assert_called_once()
    assert "Cargando" in result


def test_cargar_case_insensitive(tmp_path, monkeypatch):
    (tmp_path / "Edificio.IFC").touch()
    monkeypatch.chdir(tmp_path)
    on_cargar = MagicMock()
    tools = AppTools(MagicMock(return_value=None), on_cargar)
    tools.ejecutar("cargar_ifc", {"nombre": "edificio.ifc"})
    on_cargar.assert_called_once()


def test_cargar_no_encontrado_lista_disponibles(tmp_path, monkeypatch):
    (tmp_path / "otro.ifc").touch()
    monkeypatch.chdir(tmp_path)
    tools, _ = _make()
    result = tools.ejecutar("cargar_ifc", {"nombre": "noexiste.ifc"})
    assert "otro.ifc" in result


def test_cargar_no_encontrado_sin_ifc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tools, _ = _make()
    result = tools.ejecutar("cargar_ifc", {"nombre": "noexiste.ifc"})
    assert "no hay archivos .ifc" in result


# ------------------------------------------------------------------
# definiciones / ejecutar desconocida
# ------------------------------------------------------------------

def test_definiciones_devuelve_dos_herramientas():
    tools, _ = _make()
    defs = tools.definiciones()
    assert len(defs) == 2
    nombres = {d["function"]["name"] for d in defs}
    assert nombres == {"estado_app", "cargar_ifc"}


def test_ejecutar_herramienta_desconocida():
    tools, _ = _make()
    assert "desconocida" in tools.ejecutar("herramienta_x", {})
