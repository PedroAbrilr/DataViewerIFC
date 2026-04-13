"""Cliente para comunicación con Ollama en local."""

import os
import subprocess
import tempfile
import time
from pathlib import Path

import ollama

# Rutas del entorno portable
_PKG_DIR      = Path(__file__).parent.parent          # src/appcli/
_BIN_LOCAL    = _PKG_DIR / "bin" / "ollama"
_MODELS_DIR   = _PKG_DIR.parents[1] / "models"        # junto al paquete instalado
_BASE_MODEL    = "qwen2.5:1.5b"
_CUSTOM_MODEL  = "ifc-assistant"
_MODELFILE     = _PKG_DIR / "data" / "Modelfile"
_MANUAL_FILE   = _PKG_DIR / "data" / "manual_usuario.md"
_DEFAULT_MODEL = _CUSTOM_MODEL


def _ollama_bin() -> str:
    """Devuelve la ruta al binario de Ollama: local primero, luego sistema."""
    if _BIN_LOCAL.exists() and os.access(_BIN_LOCAL, os.X_OK):
        return str(_BIN_LOCAL)
    return "ollama"


def _env_portable() -> dict:
    """Variables de entorno para usar el directorio de modelos del proyecto."""
    env = os.environ.copy()
    if _BIN_LOCAL.exists():
        env["OLLAMA_MODELS"] = str(_MODELS_DIR.resolve())
    return env


class OllamaClient:
    def __init__(self, model: str = _DEFAULT_MODEL):
        self.model = model
        self._proceso = None  # subproceso de ollama serve

    # ------------------------------------------------------------------
    # Gestión del servidor
    # ------------------------------------------------------------------
    def ensure_running(self, on_status=None) -> bool:
        """Asegura que Ollama está en ejecución y el modelo disponible.

        Lanza ollama serve si no responde. Descarga el modelo si no lo
        encuentra. Llama a on_status(msg) para informar del progreso.

        Devuelve True si todo está listo, False si hay un error.
        """
        def status(msg):
            if on_status:
                on_status(msg)

        # 1. Comprobar si Ollama responde
        if not self._ping():
            status("Iniciando Ollama...")
            try:
                _MODELS_DIR.mkdir(parents=True, exist_ok=True)
                self._proceso = subprocess.Popen(
                    [_ollama_bin(), "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=_env_portable(),
                )
            except FileNotFoundError:
                status("Error: Ollama no está instalado. Descárgalo en https://ollama.com")
                return False

            # Esperar a que arranque (máx. 10 segundos)
            for _ in range(20):
                time.sleep(0.5)
                if self._ping():
                    break
            else:
                status("Error: Ollama no responde tras el arranque.")
                return False

            status("Ollama iniciado.")

        # 2. Descargar el modelo base si no está disponible
        modelos = self.modelos_disponibles()
        base_disponible = any(_BASE_MODEL.split(":")[0] in m for m in modelos)

        if not base_disponible:
            status(f"Descargando modelo base {_BASE_MODEL}... (puede tardar varios minutos)")
            try:
                subprocess.run(
                    [_ollama_bin(), "pull", _BASE_MODEL],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=_env_portable(),
                )
            except subprocess.CalledProcessError:
                status(f"Error al descargar {_BASE_MODEL}.")
                return False

        # 3. Crear el modelo personalizado desde el Modelfile si no existe
        custom_disponible = any(_CUSTOM_MODEL in m for m in self.modelos_disponibles())

        if not custom_disponible:
            status(f"Creando modelo {_CUSTOM_MODEL}...")
            try:
                modelfile_content = _MODELFILE.read_text(encoding="utf-8")
                if "{{MANUAL_USUARIO}}" in modelfile_content:
                    if _MANUAL_FILE.exists():
                        manual = _MANUAL_FILE.read_text(encoding="utf-8")
                    else:
                        manual = "(Manual de usuario no disponible)"
                    modelfile_content = modelfile_content.replace("{{MANUAL_USUARIO}}", manual)

                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", suffix=".modelfile", delete=False
                ) as tmp:
                    tmp.write(modelfile_content)
                    tmp_path = tmp.name

                try:
                    subprocess.run(
                        [_ollama_bin(), "create", _CUSTOM_MODEL, "-f", tmp_path],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=_env_portable(),
                    )
                finally:
                    Path(tmp_path).unlink(missing_ok=True)

                status(f"Modelo {_CUSTOM_MODEL} listo.")
            except subprocess.CalledProcessError:
                status(f"Error al crear {_CUSTOM_MODEL}. Usando modelo base.")
                self.model = _BASE_MODEL
        else:
            status(f"Modelo {_CUSTOM_MODEL} listo.")

        return True

    def _ping(self) -> bool:
        """Devuelve True si Ollama responde."""
        try:
            ollama.list()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # API de consulta
    # ------------------------------------------------------------------
    def query(self, prompt: str, system: str = "") -> str:
        """Envía un prompt a Ollama y devuelve la respuesta completa."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = ollama.chat(model=self.model, messages=messages)
        return response.message.content

    def stream(self, prompt: str, system: str = ""):
        """Envía un prompt y devuelve un generador de fragmentos de texto."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        for chunk in ollama.chat(model=self.model, messages=messages, stream=True):
            content = chunk.message.content
            if content:
                yield content

    def modelos_disponibles(self) -> list[str]:
        """Devuelve la lista de modelos instalados en Ollama."""
        try:
            return [m.model for m in ollama.list().models]
        except Exception:
            return []
