"""Tests unitarios para plugins/app/herramientas.py."""

from unittest.mock import MagicMock

import pytest

from appcli.plugins.app.herramientas import CargarIfc, EstadoApp


# ------------------------------------------------------------------
# EstadoApp
# ------------------------------------------------------------------

def test_estado_sin_archivo():
    t = EstadoApp(MagicMock(return_value=None))
    assert "No hay ningún archivo IFC" in t.execute({})


def test_estado_con_archivo():
    t = EstadoApp(MagicMock(return_value="edificio.ifc"))
    assert "edificio.ifc" in t.execute({})


def test_estado_tiene_schema():
    t = EstadoApp(MagicMock())
    assert t.schema["function"]["name"] == "estado_app"


# ------------------------------------------------------------------
# CargarIfc — validaciones
# ------------------------------------------------------------------

def test_cargar_nombre_vacio():
    t = CargarIfc(MagicMock())
    assert "Indica el nombre" in t.execute({"nombre": ""})


def test_cargar_nombre_con_slash():
    t = CargarIfc(MagicMock())
    assert "directorio de trabajo" in t.execute({"nombre": "subdir/archivo.ifc"})


def test_cargar_nombre_con_backslash():
    t = CargarIfc(MagicMock())
    assert "directorio de trabajo" in t.execute({"nombre": "sub\\archivo.ifc"})


# ------------------------------------------------------------------
# CargarIfc — búsqueda de archivo
# ------------------------------------------------------------------

def test_cargar_archivo_encontrado(tmp_path, monkeypatch):
    (tmp_path / "edificio.ifc").touch()
    monkeypatch.chdir(tmp_path)
    on_cargar = MagicMock()
    result = CargarIfc(on_cargar).execute({"nombre": "edificio.ifc"})
    on_cargar.assert_called_once()
    assert "Cargando" in result


def test_cargar_sin_extension(tmp_path, monkeypatch):
    (tmp_path / "edificio.ifc").touch()
    monkeypatch.chdir(tmp_path)
    on_cargar = MagicMock()
    result = CargarIfc(on_cargar).execute({"nombre": "edificio"})
    on_cargar.assert_called_once()
    assert "Cargando" in result


def test_cargar_case_insensitive(tmp_path, monkeypatch):
    (tmp_path / "Edificio.IFC").touch()
    monkeypatch.chdir(tmp_path)
    on_cargar = MagicMock()
    CargarIfc(on_cargar).execute({"nombre": "edificio.ifc"})
    on_cargar.assert_called_once()


def test_cargar_no_encontrado_lista_disponibles(tmp_path, monkeypatch):
    (tmp_path / "otro.ifc").touch()
    monkeypatch.chdir(tmp_path)
    result = CargarIfc(MagicMock()).execute({"nombre": "noexiste.ifc"})
    assert "otro.ifc" in result


def test_cargar_no_encontrado_sin_ifc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CargarIfc(MagicMock()).execute({"nombre": "noexiste.ifc"})
    assert "no hay archivos .ifc" in result


def test_cargar_tiene_schema():
    t = CargarIfc(MagicMock())
    assert t.schema["function"]["name"] == "cargar_ifc"
