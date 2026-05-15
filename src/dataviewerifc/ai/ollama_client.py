"""Cliente para comunicación con Ollama en local."""

import logging
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Evita ventana de consola al lanzar subprocesos en Windows
_SUBPROCESS_FLAGS = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}

import ollama

_log = logging.getLogger(__name__)

from dataviewerifc import config as _config

_PKG_DIR      = Path(__file__).parent.parent
_CUSTOM_MODEL = "ifc-assistant"
_MODELFILE    = _PKG_DIR / "data" / "Modelfile"


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

        Lanza ollama serve si no responde. Llama a on_status(msg) para
        informar del progreso.

        Devuelve True si todo está listo, False si hay un error.
        """
        def status(msg):
            if on_status:
                on_status(msg)

        # 1. Comprobar si Ollama responde
        _log.debug("ensure_running() paso 1 — ping")
        if not self._ping():
            status("Iniciando Ollama...")
            try:
                self._proceso = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **_SUBPROCESS_FLAGS,
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

        # 2. Crear el modelo personalizado desde el Modelfile si no existe
        _log.debug("ensure_running() paso 2 — comprobar modelo personalizado")
        modelos = self.modelos_disponibles()
        custom_disponible = any(_CUSTOM_MODEL in m for m in modelos)

        if not custom_disponible:
            base_model = _config.load().get("ollama_base_model", "")
            if not base_model:
                status("Error: selecciona un modelo base en Configuración.")
                return False
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

        # 3. Calentar el modelo: cargarlo en memoria antes de la primera consulta
        _log.debug("ensure_running() paso 3 — warm-up")
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

    def recrear_modelo(self, on_status=None, base_model: str = "") -> bool:
        """Borra ifc-assistant si existe y lo recrea desde el Modelfile.

        base_model sobreescribe el valor guardado en config si se proporciona.
        Devuelve True si el modelo quedó listo, False si hubo error.
        """
        def status(msg):
            if on_status:
                on_status(msg)

        if not self._ping():
            status("Iniciando Ollama...")
            try:
                self._proceso = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **_SUBPROCESS_FLAGS,
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

        if not base_model:
            base_model = _config.load().get("ollama_base_model", "")
        if not base_model:
            status("Error: selecciona un modelo base en Configuración.")
            return False

        # Borrar el modelo personalizado si existe
        modelos = self.modelos_disponibles()
        if any(_CUSTOM_MODEL in m for m in modelos):
            status(f"Eliminando modelo anterior {_CUSTOM_MODEL}...")
            try:
                subprocess.run(
                    ["ollama", "rm", _CUSTOM_MODEL],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **_SUBPROCESS_FLAGS,
                )
            except subprocess.CalledProcessError:
                status(f"Aviso: no se pudo eliminar {_CUSTOM_MODEL}.")

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

    def iniciar_servidor(self, on_status=None) -> bool:
        """Arranca ollama serve si no responde. No crea ni carga modelos."""
        def status(msg):
            if on_status:
                on_status(msg)

        if self._ping():
            return True

        status("Iniciando Ollama...")
        try:
            self._proceso = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **_SUBPROCESS_FLAGS,
            )
        except FileNotFoundError:
            status("Error: Ollama no está instalado.")
            return False

        for _ in range(20):
            time.sleep(0.5)
            if self._ping():
                status("Ollama iniciado.")
                return True
        else:
            status("Error: Ollama no responde.")
            return False

    def modelos_disponibles(self) -> list[str]:
        try:
            return [m.model for m in ollama.list().models]
        except Exception:
            return []
