"""Utilidades de formato compartidas por los plugins IFC."""

_MAX_RESULTADOS = 50


def _extract_ids(elementos: list) -> list[str]:
    return [e["id"] for e in elementos if e.get("id")]


def _fmt_lista(elementos: list, contexto: str) -> str:
    if not elementos:
        return f"No se encontraron elementos para: {contexto}."
    total = len(elementos)
    muestra = elementos[:_MAX_RESULTADOS]
    lineas = [f"- {e['nombre']} ({e['tipo']}) [id: {e['id']}]" for e in muestra]
    cabecera = f"{total} elemento(s) encontrado(s) para: {contexto}."
    if total > _MAX_RESULTADOS:
        cabecera += f" Mostrando los primeros {_MAX_RESULTADOS}."
    return cabecera + "\n" + "\n".join(lineas)


def _fmt_propiedades(resultado: dict) -> str:
    if not resultado.get("encontrado"):
        return "Elemento no encontrado."
    lineas = [f"{resultado['nombre']} ({resultado['tipo']})"]
    for grupo in resultado.get("grupos", []):
        lineas.append(f"\n{grupo['pset']}:")
        for p in grupo["props"]:
            unidad = f" {p['unidad']}" if p["unidad"] else ""
            lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}")
    return "\n".join(lineas)
