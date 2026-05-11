"""Punto de entrada para desarrollo. No se incluye en el wheel."""

import sys
from pathlib import Path

_HERE = Path(__file__).parent

# Asegurar que src/ está en el path para importar appcli directamente
sys.path.insert(0, str(_HERE / "src"))

import logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s.%(msecs)03d  %(levelname)-5s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("dataviewerifc.ai").setLevel(logging.DEBUG)

from dataviewerifc.main import main

main()
