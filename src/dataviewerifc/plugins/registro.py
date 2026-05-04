"""Registro de plugins activos de la aplicación.

Para añadir o eliminar una herramienta, editar únicamente este archivo:
  - Importar la clase del plugin correspondiente.
  - Añadir o quitar la línea reg_base.register(...) o reg_sel.register(...).
"""

from dataviewerifc.plugins.registry import ToolRegistry
from dataviewerifc.plugins.ifc.buscar import BuscarElementos, BuscarPorNombre, ContarElementos
from dataviewerifc.plugins.ifc.estructura import ListarPlantas, ElementosDePlanta, CalcularAreaTotal
from dataviewerifc.plugins.ifc.propiedades import ObtenerPropiedades, FiltrarPorPropiedad
from dataviewerifc.plugins.ifc.seleccion import ObtenerSeleccion
from dataviewerifc.plugins.app.herramientas import EstadoApp, CargarIfc
from dataviewerifc.plugins.app.proyecto import ObtenerDirectorioProyecto, EstablecerDirectorioProyecto, BuscarArchivosIfc


def construir_registries(loader, get_context, get_archivo_activo, on_cargar):
    """Instancia y registra todos los plugins activos.

    Devuelve (registry_base, registry_seleccion).
    registry_base      — herramientas siempre disponibles.
    registry_seleccion — herramientas disponibles solo con selección activa.
    """
    reg_base = ToolRegistry()
    reg_base.register(BuscarElementos(loader))
    reg_base.register(BuscarPorNombre(loader))
    reg_base.register(ContarElementos(loader))
    reg_base.register(ObtenerPropiedades(loader))
    reg_base.register(FiltrarPorPropiedad(loader, get_context=get_context))
    reg_base.register(ListarPlantas(loader))
    reg_base.register(ElementosDePlanta(loader))
    reg_base.register(CalcularAreaTotal(loader))
    reg_base.register(EstadoApp(get_archivo_activo))
    reg_base.register(CargarIfc(on_cargar))
    reg_base.register(ObtenerDirectorioProyecto())
    reg_base.register(EstablecerDirectorioProyecto())
    reg_base.register(BuscarArchivosIfc())

    reg_sel = ToolRegistry()
    reg_sel.register(ObtenerSeleccion(get_context=get_context, loader=loader))

    return reg_base, reg_sel
