"""Plugin: herramienta de consulta sobre la selección activa en la UI."""

from collections import defaultdict


class ObtenerSeleccion:
    name = "obtener_seleccion"
    schema = {
        "type": "function",
        "function": {
            "name": "obtener_seleccion",
            "description": (
                "Devuelve información sobre el/los elemento/s actualmente "
                "seleccionado/s en la interfaz. "
                "Úsala SIEMPRE que el usuario pregunte sobre 'este elemento', "
                "'el elemento seleccionado', 'sus propiedades', 'sus características' "
                "o cualquier detalle del elemento activo. "
                "No necesita ningún identificador: accede directamente a la selección actual."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "modo": {
                        "type": "string",
                        "enum": ["reducido", "agrupado", "estadistico"],
                        "description": (
                            "reducido: nombre, tipo y nombres de PSets disponibles. "
                            "agrupado: todas las propiedades con sus valores — "
                            "USA ESTE MODO cuando el usuario pida propiedades, "
                            "características, dimensiones o detalles del elemento. "
                            "estadistico: resumen numérico mín/máx/media/suma "
                            "(recomendado con varios elementos seleccionados)."
                        ),
                    }
                },
                "required": [],
            },
        },
    }

    def __init__(self, get_context, loader=None):
        self._get_context = get_context
        self._loader = loader
        self.last_ids: list[str] = []

    def execute(self, args: dict) -> str:
        self.last_ids = []
        elementos, props = self._get_context()
        if not elementos:
            return "No hay ningún elemento seleccionado en la aplicación."
        modo = args.get("modo", "reducido")
        if modo == "agrupado":
            return self._fmt_agrupado(elementos, props)
        if modo == "estadistico":
            return self._fmt_estadistico(elementos, props)
        return self._fmt_reducido(elementos, props)

    def _fmt_reducido(self, elementos, props) -> str:
        psets = ", ".join(g["pset"] for g in props) or "ninguno"
        if len(elementos) == 1:
            e = elementos[0]
            info = e.get_info()
            nombre = info.get("Name") or e.is_a()
            return (
                f"Elemento seleccionado: {nombre} ({e.is_a()})\n"
                f"PSets disponibles: {psets}"
            )
        lineas = [f"{len(elementos)} elementos seleccionados:"]
        for e in elementos[:20]:
            info = e.get_info()
            nombre = info.get("Name") or e.is_a()
            lineas.append(f"  - {nombre} ({e.is_a()})")
        if len(elementos) > 20:
            lineas.append(f"  ... y {len(elementos) - 20} más")
        e_activo = elementos[-1]
        nombre_activo = e_activo.get_info().get("Name") or e_activo.is_a()
        lineas.append(f"\nPSets disponibles en elemento activo ({nombre_activo}): {psets}")
        return "\n".join(lineas)

    def _fmt_agrupado(self, elementos, props) -> str:
        if len(elementos) == 1:
            e = elementos[0]
            info = e.get_info()
            nombre = info.get("Name") or e.is_a()
            gid = info.get("GlobalId", "")
            lineas = [
                f"Elemento seleccionado: {nombre} ({e.is_a()})",
                f"GlobalId: {gid}",
            ]
            for grupo in props:
                lineas.append(f"\n{grupo['pset']}:")
                for p in grupo["props"]:
                    unidad = f" {p['unidad']}" if p["unidad"] else ""
                    lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}")
            return "\n".join(lineas)

        lineas = [f"{len(elementos)} elementos seleccionados — propiedades combinadas:"]
        for grupo in props:
            lineas.append(f"\n{grupo['pset']}:")
            for p in grupo["props"]:
                unidad = f" {p['unidad']}" if p["unidad"] else ""
                nota = " (valores distintos)" if p.get("varios") else ""
                lineas.append(f"  {p['nombre']}: {p['valor']}{unidad}{nota}")
        return "\n".join(lineas)

    def _fmt_estadistico(self, elementos, props) -> str:
        if len(elementos) <= 1:
            return self._fmt_agrupado(elementos, props)
        if not self._loader:
            return "No hay modelo IFC cargado para calcular estadísticas."

        acum = defaultdict(list)
        for e in elementos:
            for grupo in self._loader.get_properties(e):
                for p in grupo["props"]:
                    try:
                        acum[(grupo["pset"], p["nombre"], p["unidad"])].append(float(p["valor"]))
                    except (ValueError, TypeError):
                        pass

        n = len(elementos)
        lineas = [f"Resumen estadístico — {n} elementos seleccionados:"]
        encontrado = False
        for (pset, nombre, unidad), vals in acum.items():
            if len(vals) < 2:
                continue
            encontrado = True
            u = f" {unidad}" if unidad else ""
            media = sum(vals) / len(vals)
            lineas.append(
                f"  {pset} / {nombre}: "
                f"mín={min(vals):.4g}{u}  máx={max(vals):.4g}{u}  "
                f"media={media:.4g}{u}  suma={sum(vals):.4g}{u}  "
                f"({len(vals)}/{n} elementos)"
            )
        if not encontrado:
            lineas.append("  No se encontraron propiedades numéricas en varios elementos.")
        return "\n".join(lineas)
