"""Cliente para comunicación con Ollama en local."""

import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path

import ollama

_log = logging.getLogger(__name__)

from dataviewerifc import config as _config
from dataviewerifc.platform_support import get_platform

_PKG_DIR      = Path(__file__).parent.parent
_CUSTOM_MODEL = "ifc-assistant"
_MODELFILE    = _PKG_DIR / "data" / "Modelfile"


def _ollama_bin() -> str:
    """Devuelve la ruta al binario de Ollama: DATAVIEWERIFC_OLLAMA_BIN → usuario → sistema."""
    dev_bin = os.environ.get("DATAVIEWERIFC_OLLAMA_BIN")
    if dev_bin and Path(dev_bin).exists() and os.access(dev_bin, os.X_OK):
        return dev_bin
    plat = get_platform()
    user_bin = plat.ollama_bin_path
    if plat.is_executable(user_bin):
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


def _parse_modelfile(content: str) -> tuple[str, dict]:
    """Extrae (system_prompt, parámetros) de un Modelfile."""
    system_lines: list[str] = []
    params: dict = {}
    in_system = False

    for line in content.splitlines():
        if not in_system and line.startswith("SYSTEM \"\"\""):
            in_system = True
            rest = line[len('SYSTEM """'):]
            if rest:
                system_lines.append(rest)
        elif in_system:
            if line.strip() == '"""':
                in_system = False
            else:
                system_lines.append(line)
        elif line.startswith("PARAMETER "):
            parts = line.split(None, 2)
            if len(parts) == 3:
                key, val = parts[1], parts[2]
                try:
                    params[key] = float(val) if "." in val else int(val)
                except ValueError:
                    params[key] = val

    return "\n".join(system_lines).strip(), params


class OllamaClient:
    def __init__(self):
        self._proceso = None  # subproceso de ollama serve

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
        _log.debug("ensure_running() paso 1 — ping")
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

            for _ in range(20):
                time.sleep(0.5)
                if self._ping():
                    break
            else:
                status("Error: Ollama no responde tras el arranque.")
                return False

            status("Ollama iniciado.")

        _log.debug("ensure_running() paso 2 — comprobar modelo base")
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
            modelos = self.modelos_disponibles()

        _log.debug("ensure_running() paso 3 — comprobar modelo personalizado")
        # 3. Crear el modelo personalizado desde el Modelfile si no existe
        custom_disponible = any(_CUSTOM_MODEL in m for m in modelos)

        if not custom_disponible:
            status(f"Creando modelo {_CUSTOM_MODEL}...")
            try:
                modelfile_content = _MODELFILE.read_text(encoding="utf-8")
                system_prompt, params = _parse_modelfile(modelfile_content)
                for _ in ollama.create(
                    model=_CUSTOM_MODEL,
                    from_=base_model,
                    system=system_prompt,
                    parameters=params,
                    stream=True,
                ):
                    pass
                status(f"Modelo {_CUSTOM_MODEL} listo.")
            except Exception:
                status(f"Error al crear {_CUSTOM_MODEL}. Usando modelo base.")
        else:
            status(f"Modelo {_CUSTOM_MODEL} listo.")

        # 4. Calentar el modelo: cargarlo en memoria antes de la primera consulta
        _log.debug("ensure_running() paso 4 — warm-up")
        status("Cargando modelo en memoria...")
        t0 = time.perf_counter()
        try:
            ollama.generate(model=_CUSTOM_MODEL, prompt="hola", options={"num_predict": 1}, keep_alive="30m")
            _log.debug("warm-up completado en %.1fs", time.perf_counter() - t0)
        except Exception as e:
            _log.debug("warm-up falló en %.1fs: %s", time.perf_counter() - t0, e)

        status("Listo.")
        return True

    def _ping(self) -> bool:
        try:
            ollama.list()
            return True
        except Exception:
            return False

    def stop(self) -> None:
        """Termina el proceso ollama serve si fue iniciado por la app."""
        if self._proceso and self._proceso.poll() is None:
            self._proceso.terminate()
            try:
                self._proceso.wait(timeout=5)
            except Exception:
                self._proceso.kill()
        self._proceso = None

    def recrear_modelo(self, on_status=None) -> bool:
        """Borra ifc-assistant si existe y lo recrea desde el Modelfile.

        Devuelve True si el modelo quedó listo, False si hubo error.
        """
        def status(msg):
            if on_status:
                on_status(msg)

        _prepare_models_dir()

        if not self._ping():
            status("Iniciando Ollama...")
            try:
                self._proceso = subprocess.Popen(
                    [_ollama_bin(), "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                status("Error: Ollama no está instalado.")
                return False
            for _ in range(20):
                time.sleep(0.5)
                if self._ping():
                    break
            else:
                status("Error: Ollama no responde.")
                return False

        # Borrar el modelo personalizado si existe
        modelos = self.modelos_disponibles()
        if any(_CUSTOM_MODEL in m for m in modelos):
            status(f"Eliminando modelo anterior {_CUSTOM_MODEL}...")
            try:
                subprocess.run(
                    [_ollama_bin(), "rm", _CUSTOM_MODEL],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.CalledProcessError:
                status(f"Aviso: no se pudo eliminar {_CUSTOM_MODEL}.")

        # Descargar modelo base si no está disponible
        base_model = _base_model()
        if not any(base_model.split(":")[0] in m for m in modelos):
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

        # Crear modelo personalizado con streaming para ver el progreso real
        status(f"Creando modelo {_CUSTOM_MODEL}...")
        try:
            modelfile_content = _MODELFILE.read_text(encoding="utf-8")
            system_prompt, params = _parse_modelfile(modelfile_content)

            for resp in ollama.create(
                model=_CUSTOM_MODEL,
                from_=base_model,
                system=system_prompt,
                parameters=params,
                stream=True,
            ):
                msg = (resp.status or "").strip()
                if msg:
                    if "sha256:" in msg:
                        msg = msg.split("sha256:")[0].rstrip(" \t:")
                    status(msg)

            status(f"Modelo {_CUSTOM_MODEL} creado correctamente.")
            return True
        except Exception as e:
            status(f"Error al crear {_CUSTOM_MODEL}: {e}")
            return False

    def modelos_disponibles(self) -> list[str]:
        try:
            return [m.model for m in ollama.list().models]
        except Exception:
            return []
