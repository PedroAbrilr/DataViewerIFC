"""Punto de entrada para desarrollo. No se incluye en el wheel."""

import os
import sys
from pathlib import Path

_HERE = Path(__file__).parent

# Binario portable de Ollama incluido en el repositorio
os.environ.setdefault(
    "APPCLI_OLLAMA_BIN",
    str(_HERE / "src" / "appcli" / "ollama" / "ollama"),
)

# Directorio de modelos local al proyecto (excluido del repositorio por .gitignore)
os.environ.setdefault(
    "APPCLI_MODELS_DIR",
    str(_HERE / "models"),
)

# Asegurar que src/ está en el path para importar appcli directamente
sys.path.insert(0, str(_HERE / "src"))

from appcli.main import main

main()
