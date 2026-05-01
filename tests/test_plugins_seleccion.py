"""Tests unitarios para plugins de selección (FiltrarPorPropiedad y ObtenerSeleccion)."""

from unittest.mock import MagicMock, patch

import pytest

from appcli.plugins.ifc.propiedades import FiltrarPorPropiedad
from appcli.plugins.ifc.seleccion import ObtenerSeleccion


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_elem(nombre="Muro norte", tipo="IfcWall", global_id="abc123"):
    e = MagicMock()
    e.get_info.return_value = {"Name": nombre, "GlobalId": global_id}
    e.is_a.return_value = tipo
    return e


def _loader(modelo=True):
    mock = MagicMock()
    mock.model = MagicMock() if modelo else None
    return mock


_ELEM_DICT = {"id": "abc123", "nombre": "Muro norte", "tipo": "IfcWall"}


# ------------------------------------------------------------------
# FiltrarPorPropiedad — sin modelo
# ------------------------------------------------------------------

def test_filtrar_sin_modelo():
    t = FiltrarPorPropiedad(_loader(modelo=False))
    assert "No hay ningún archivo IFC abierto" in t.execute({"propiedad": "x", "valor": "y"})


# ------------------------------------------------------------------
# FiltrarPorPropiedad — fuente=modelo
# ------------------------------------------------------------------

def test_filtrar_modelo_con_resultados():
    t = FiltrarPorPropiedad(_loader())
    with patch("appcli.plugins.ifc.propiedades._q.filtrar_por_propiedad", return_value=[_ELEM_DICT]):
        resultado = t.execute({"propiedad": "IsExternal", "valor": "true"})
    assert "1 elemento(s)" in resultado
    assert t.last_ids == ["abc123"]


def test_filtrar_modelo_sin_resultados():
    t = FiltrarPorPropiedad(_loader())
    with patch("appcli.plugins.ifc.propiedades._q.filtrar_por_propiedad", return_value=[]):
        resultado = t.execute({"propiedad": "X", "valor": "Y"})
    assert "No se encontraron" in resultado
    assert t.last_ids == []


def test_filtrar_modelo_con_tipo():
    t = FiltrarPorPropiedad(_loader())
    with patch("appcli.plugins.ifc.propiedades._q.filtrar_por_propiedad", return_value=[_ELEM_DICT]):
        resultado = t.execute({"propiedad": "IsExternal", "valor": "true", "tipo": "IfcWall"})
    assert "1 elemento(s)" in resultado


def test_filtrar_argumento_faltante():
    t = FiltrarPorPropiedad(_loader())
    assert "Argumento requerido" in t.execute({"propiedad": "X"})


# ------------------------------------------------------------------
# FiltrarPorPropiedad — fuente=seleccion
# ------------------------------------------------------------------

def test_filtrar_seleccion_sin_contexto():
    t = FiltrarPorPropiedad(_loader())
    resultado = t.execute({"propiedad": "x", "valor": "y", "fuente": "seleccion"})
    assert "No hay contexto" in resultado


def test_filtrar_seleccion_sin_elementos():
    t = FiltrarPorPropiedad(_loader(), get_context=lambda: ([], []))
    resultado = t.execute({"propiedad": "x", "valor": "y", "fuente": "seleccion"})
    assert "No hay ningún elemento seleccionado" in resultado


def test_filtrar_seleccion_con_resultados():
    elem = _make_elem()
    t = FiltrarPorPropiedad(_loader(), get_context=lambda: ([elem], []))
    with patch("appcli.plugins.ifc.propiedades._q.filtrar_por_propiedad", return_value=[_ELEM_DICT]):
        resultado = t.execute({"propiedad": "IsExternal", "valor": "true", "fuente": "seleccion"})
    assert "selección" in resultado
    assert t.last_ids == ["abc123"]


def test_filtrar_last_ids_se_resetea_entre_llamadas():
    t = FiltrarPorPropiedad(_loader())
    with patch("appcli.plugins.ifc.propiedades._q.filtrar_por_propiedad", return_value=[_ELEM_DICT]):
        t.execute({"propiedad": "X", "valor": "Y"})
    assert t.last_ids == ["abc123"]
    with patch("appcli.plugins.ifc.propiedades._q.filtrar_por_propiedad", return_value=[]):
        t.execute({"propiedad": "X", "valor": "Y"})
    assert t.last_ids == []


# ------------------------------------------------------------------
# ObtenerSeleccion — sin selección
# ------------------------------------------------------------------

def test_seleccion_sin_elementos():
    t = ObtenerSeleccion(get_context=lambda: ([], []))
    assert "No hay ningún elemento seleccionado" in t.execute({})


# ------------------------------------------------------------------
# ObtenerSeleccion — modo reducido
# ------------------------------------------------------------------

def test_seleccion_reducido_un_elemento():
    e = _make_elem("Muro A", "IfcWall", "id1")
    props = [{"pset": "Pset_WallCommon", "props": []}]
    t = ObtenerSeleccion(get_context=lambda: ([e], props))
    resultado = t.execute({"modo": "reducido"})
    assert "Muro A" in resultado
    assert "IfcWall" in resultado
    assert "Pset_WallCommon" in resultado


def test_seleccion_reducido_modo_por_defecto():
    e = _make_elem()
    t = ObtenerSeleccion(get_context=lambda: ([e], []))
    resultado = t.execute({})
    assert "Muro norte" in resultado


def test_seleccion_reducido_varios_elementos():
    elems = [_make_elem(f"Muro {i}", "IfcWall", f"id{i}") for i in range(3)]
    t = ObtenerSeleccion(get_context=lambda: (elems, [{"pset": "PS1", "props": []}]))
    resultado = t.execute({"modo": "reducido"})
    assert "3 elementos seleccionados" in resultado


def test_seleccion_reducido_mas_de_20():
    elems = [_make_elem(f"E{i}", "IfcWall", f"id{i}") for i in range(25)]
    t = ObtenerSeleccion(get_context=lambda: (elems, []))
    resultado = t.execute({"modo": "reducido"})
    assert "y 5 más" in resultado


# ------------------------------------------------------------------
# ObtenerSeleccion — modo agrupado
# ------------------------------------------------------------------

def test_seleccion_agrupado_un_elemento():
    e = _make_elem("Puerta A", "IfcDoor", "gid1")
    props = [{"pset": "Pset_DoorCommon", "props": [
        {"nombre": "FireRating", "valor": "EI30", "unidad": ""}
    ]}]
    t = ObtenerSeleccion(get_context=lambda: ([e], props))
    resultado = t.execute({"modo": "agrupado"})
    assert "Puerta A" in resultado
    assert "gid1" in resultado
    assert "FireRating" in resultado
    assert "EI30" in resultado


def test_seleccion_agrupado_varios_elementos():
    elems = [_make_elem(f"E{i}", "IfcWall", f"id{i}") for i in range(2)]
    props = [{"pset": "PS1", "props": [{"nombre": "Grosor", "valor": "20", "unidad": "cm"}]}]
    t = ObtenerSeleccion(get_context=lambda: (elems, props))
    resultado = t.execute({"modo": "agrupado"})
    assert "2 elementos seleccionados" in resultado
    assert "Grosor" in resultado


# ------------------------------------------------------------------
# ObtenerSeleccion — modo estadístico
# ------------------------------------------------------------------

def test_seleccion_estadistico_un_elemento_devuelve_agrupado():
    e = _make_elem("Losa", "IfcSlab", "id1")
    props = [{"pset": "PS1", "props": [{"nombre": "Area", "valor": "10.5", "unidad": "m²"}]}]
    t = ObtenerSeleccion(get_context=lambda: ([e], props))
    resultado = t.execute({"modo": "estadistico"})
    assert "Losa" in resultado


def test_seleccion_estadistico_sin_loader():
    elems = [_make_elem(f"E{i}", "IfcWall", f"id{i}") for i in range(2)]
    t = ObtenerSeleccion(get_context=lambda: (elems, []))
    assert "No hay modelo IFC" in t.execute({"modo": "estadistico"})


def test_seleccion_estadistico_con_loader():
    elems = [_make_elem(f"E{i}", "IfcWall", f"id{i}") for i in range(2)]
    loader = MagicMock()
    loader.get_properties.return_value = [
        {"pset": "PS1", "props": [{"nombre": "Area", "valor": "10.0", "unidad": "m²"}]}
    ]
    t = ObtenerSeleccion(get_context=lambda: (elems, []), loader=loader)
    resultado = t.execute({"modo": "estadistico"})
    assert "Resumen estadístico" in resultado
    assert "2 elementos" in resultado
    assert "Area" in resultado


def test_seleccion_estadistico_sin_props_numericas():
    elems = [_make_elem(f"E{i}", "IfcWall", f"id{i}") for i in range(2)]
    loader = MagicMock()
    loader.get_properties.return_value = [
        {"pset": "PS1", "props": [{"nombre": "Nombre", "valor": "texto", "unidad": ""}]}
    ]
    t = ObtenerSeleccion(get_context=lambda: (elems, []), loader=loader)
    resultado = t.execute({"modo": "estadistico"})
    assert "No se encontraron propiedades numéricas" in resultado
