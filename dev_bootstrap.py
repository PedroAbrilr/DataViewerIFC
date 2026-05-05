"""Punto de entrada para desarrollo. No se incluye en el wheel."""

import os
import sys
from pathlib import Path

_HERE = Path(__file__).parent

# Binario portable de Ollama incluido en el repositorio
os.environ.setdefault(
    "DATAVIEWERIFC_OLLAMA_BIN",
    str(_HERE / "src" / "dataviewerifc" / "ollama" / "ollama"),
)

# Directorio de modelos local al proyecto (excluido del repositorio por .gitignore)
os.environ.setdefault(
    "DATAVIEWERIFC_MODELS_DIR",
    str(_HERE / "models"),
)

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
