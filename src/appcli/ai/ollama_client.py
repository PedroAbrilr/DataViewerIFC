"""Cliente para comunicación con Ollama en local."""

import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path

import ollama

from appcli import config as _config

_PKG_DIR      = Path(__file__).parent.parent          # src/appcli/
_CUSTOM_MODEL  = "ifc-assistant"
_MODELFILE     = _PKG_DIR / "data" / "Modelfile"
_MANUAL_FILE   = _PKG_DIR / "data" / "manual_usuario.md"
_DEFAULT_MODEL = _CUSTOM_MODEL


def _user_ollama_bin() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    suffix = ".exe" if platform.system() == "Windows" else ""
    return base / "appcli" / "ollama" / f"ollama{suffix}"


def _ollama_bin() -> str:
    """Devuelve la ruta al binario de Ollama: APPCLI_OLLAMA_BIN → usuario → sistema."""
    dev_bin = os.environ.get("APPCLI_OLLAMA_BIN")
    if dev_bin and Path(dev_bin).exists() and os.access(dev_bin, os.X_OK):
        return dev_bin
    user_bin = _user_ollama_bin()
    if user_bin.exists() and os.access(user_bin, os.X_OK):
        return str(user_bin)
    return "ollama"


def _prepare_models_dir() -> None:
    """Fija OLLAMA_MODELS en ollama/models/ junto al ejecutable portable."""
    bin_path = Path(_ollama_bin())
    if not bin_path.is_absolute():
        return  # Ollama del sistema: usa ~/.ollama/models por defecto
    models_dir = bin_path.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    os.environ["OLLAMA_MODELS"] = str(models_dir)


def _base_model() -> str:
    return _config.load().get("base_model", "qwen2.5:1.5b")


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

        _prepare_models_dir()

        # 1. Comprobar si Ollama responde
        if not self._ping():
            status("Iniciando Ollama...")
            try:
                self._proceso = subprocess.Popen(
                    [_ollama_bin(), "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
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
        base_model = _base_model()
        modelos = self.modelos_disponibles()
        base_disponible = any(base_model.split(":")[0] in m for m in modelos)

        if not base_disponible:
            status(f"Descargando modelo base {base_model}... (puede tardar varios minutos)")
            try:
                subprocess.run(
                    [_ollama_bin(), "pull", base_model],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                status(f"Error al descargar {base_model}.")
                return False

        # 3. Crear el modelo personalizado desde el Modelfile si no existe
        custom_disponible = any(_CUSTOM_MODEL in m for m in self.modelos_disponibles())

        if not custom_disponible:
            status(f"Creando modelo {_CUSTOM_MODEL}...")
            try:
                modelfile_content = _MODELFILE.read_text(encoding="utf-8")
                modelfile_content = modelfile_content.replace("{{BASE_MODEL}}", base_model)
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
                    )
                finally:
                    Path(tmp_path).unlink(missing_ok=True)

                status(f"Modelo {_CUSTOM_MODEL} listo.")
            except subprocess.CalledProcessError:
                status(f"Error al crear {_CUSTOM_MODEL}. Usando modelo base.")
                self.model = base_model
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
