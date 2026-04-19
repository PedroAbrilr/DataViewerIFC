"""Tests unitarios para appcli.ifc.query."""

import ifcopenshell
import ifcopenshell.guid
import pytest

from appcli.ifc.query import (
    _normalizar_tipo,
    buscar_por_nombre,
    buscar_por_tipo,
    calcular_area_total,
    contar_por_tipo,
    elementos_de_planta,
    listar_plantas,
    obtener_propiedades,
)


@pytest.fixture
def modelo():
    """Modelo IFC mínimo: una planta con un muro y una puerta."""
    m = ifcopenshell.file()

    guid_planta = ifcopenshell.guid.new()
    guid_muro   = ifcopenshell.guid.new()
    guid_puerta = ifcopenshell.guid.new()

    planta = m.create_entity("IfcBuildingStorey", GlobalId=guid_planta, Name="Planta baja")
    muro   = m.create_entity("IfcWall",           GlobalId=guid_muro,   Name="Muro norte")
    puerta = m.create_entity("IfcDoor",           GlobalId=guid_puerta, Name="Puerta principal")

    m.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        RelatingStructure=planta,
        RelatedElements=[muro, puerta],
    )

    # PSet con propiedades del muro
    pset = m.create_entity("IfcPropertySet", GlobalId=ifcopenshell.guid.new(), Name="Pset_WallCommon")
    prop = m.create_entity(
        "IfcPropertySingleValue",
        Name="IsExternal",
        NominalValue=m.create_entity("IfcBoolean", wrappedValue=True),
    )
    pset.HasProperties = [prop]
    m.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[muro],
        RelatingPropertyDefinition=pset,
    )

    return m, guid_muro, guid_puerta, guid_planta


# ------------------------------------------------------------------
# _normalizar_tipo
# ------------------------------------------------------------------

def test_normalizar_tipo_sin_prefijo():
    assert _normalizar_tipo("Wall") == "IfcWall"


def test_normalizar_tipo_con_prefijo():
    assert _normalizar_tipo("IfcWall") == "IfcWall"


# ------------------------------------------------------------------
# buscar_por_tipo
# ------------------------------------------------------------------

def test_buscar_por_tipo_existente(modelo):
    m, *_ = modelo
    resultado = buscar_por_tipo(m, "IfcWall")
    assert len(resultado) == 1
    assert resultado[0]["tipo"] == "IfcWall"
    assert resultado[0]["nombre"] == "Muro norte"


def test_buscar_por_tipo_sin_prefijo(modelo):
    m, *_ = modelo
    assert len(buscar_por_tipo(m, "Wall")) == 1


def test_buscar_por_tipo_inexistente(modelo):
    m, *_ = modelo
    assert buscar_por_tipo(m, "IfcColumn") == []


def test_buscar_por_tipo_invalido(modelo):
    m, *_ = modelo
    assert buscar_por_tipo(m, "TipoQueNoExiste") == []


# ------------------------------------------------------------------
# contar_por_tipo
# ------------------------------------------------------------------

def test_contar_por_tipo_existente(modelo):
    m, *_ = modelo
    assert contar_por_tipo(m, "IfcWall") == 1


def test_contar_por_tipo_inexistente(modelo):
    m, *_ = modelo
    assert contar_por_tipo(m, "IfcBeam") == 0


# ------------------------------------------------------------------
# listar_plantas
# ------------------------------------------------------------------

def test_listar_plantas(modelo):
    m, *_ = modelo
    plantas = listar_plantas(m)
    assert len(plantas) == 1
    assert plantas[0]["nombre"] == "Planta baja"


def test_listar_plantas_vacio():
    m = ifcopenshell.file()
    assert listar_plantas(m) == []


# ------------------------------------------------------------------
# elementos_de_planta
# ------------------------------------------------------------------

def test_elementos_de_planta_exacto(modelo):
    m, *_ = modelo
    elems = elementos_de_planta(m, "Planta baja")
    assert len(elems) == 2


def test_elementos_de_planta_parcial(modelo):
    m, *_ = modelo
    elems = elementos_de_planta(m, "baja")
    assert len(elems) == 2


def test_elementos_de_planta_case_insensitive(modelo):
    m, *_ = modelo
    elems = elementos_de_planta(m, "PLANTA")
    assert len(elems) == 2


def test_elementos_de_planta_sin_coincidencia(modelo):
    m, *_ = modelo
    assert elementos_de_planta(m, "Primera planta") == []


# ------------------------------------------------------------------
# buscar_por_nombre
# ------------------------------------------------------------------

def test_buscar_por_nombre_parcial(modelo):
    m, *_ = modelo
    resultado = buscar_por_nombre(m, "norte")
    assert any(e["nombre"] == "Muro norte" for e in resultado)


def test_buscar_por_nombre_case_insensitive(modelo):
    m, *_ = modelo
    assert len(buscar_por_nombre(m, "MURO")) >= 1


def test_buscar_por_nombre_sin_resultados(modelo):
    m, *_ = modelo
    assert buscar_por_nombre(m, "xyzabc") == []


# ------------------------------------------------------------------
# obtener_propiedades
# ------------------------------------------------------------------

def test_obtener_propiedades_existente(modelo):
    m, guid_muro, *_ = modelo
    resultado = obtener_propiedades(m, guid_muro)
    assert resultado["encontrado"] is True
    assert resultado["nombre"] == "Muro norte"
    assert resultado["tipo"] == "IfcWall"
    pset_nombres = [g["pset"] for g in resultado["grupos"]]
    assert "Pset_WallCommon" in pset_nombres


def test_obtener_propiedades_inexistente(modelo):
    m, *_ = modelo
    resultado = obtener_propiedades(m, "GlobalIdQueNoExiste1234")
    assert resultado["encontrado"] is False


# ------------------------------------------------------------------
# calcular_area_total
# ------------------------------------------------------------------

def test_calcular_area_total_sin_datos(modelo):
    m, *_ = modelo
    assert calcular_area_total(m, "IfcWall") == 0.0


def test_calcular_area_total_tipo_invalido(modelo):
    m, *_ = modelo
    assert calcular_area_total(m, "TipoInexistente") == 0.0
