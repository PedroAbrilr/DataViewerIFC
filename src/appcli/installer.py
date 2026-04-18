"""Instalador de AppCLI: descarga Ollama, configura el modelo y el acceso directo."""

import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from appcli import config

# --- Rutas ---
_PKG_DIR     = Path(__file__).parent
_MODELFILE   = _PKG_DIR / "data" / "Modelfile"
_MANUAL_FILE = _PKG_DIR / "data" / "manual_usuario.md"
_DESKTOP_SRC = _PKG_DIR / "data" / "appcli.desktop"
_CUSTOM_MODEL = "ifc-assistant"

# Directorio donde se instala el binario de Ollama si no está en el sistema
def _user_bin_dir() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    return base / "appcli" / "bin"


def _user_ollama_bin() -> Path:
    suffix = ".exe" if platform.system() == "Windows" else ""
    return _user_bin_dir() / f"ollama{suffix}"


def _system_ollama() -> str | None:
    """Devuelve la ruta al binario de Ollama del sistema, o None si no existe."""
    path = shutil.which("ollama")
    return path if path else None


def _ollama_bin() -> str:
    user_bin = _user_ollama_bin()
    if user_bin.exists() and os.access(user_bin, os.X_OK):
        return str(user_bin)
    sys_bin = _system_ollama()
    if sys_bin:
        return sys_bin
    return "ollama"


# --- Descarga de Ollama ---

_OLLAMA_RELEASES = "https://github.com/ollama/ollama/releases/latest/download"

_DOWNLOAD_MAP = {
    ("Linux",   "x86_64"):  f"{_OLLAMA_RELEASES}/ollama-linux-amd64",
    ("Linux",   "aarch64"): f"{_OLLAMA_RELEASES}/ollama-linux-arm64",
    ("Darwin",  "x86_64"):  f"{_OLLAMA_RELEASES}/ollama-darwin",
    ("Darwin",  "arm64"):   f"{_OLLAMA_RELEASES}/ollama-darwin",
}


def _download_ollama() -> bool:
    """Descarga el binario de Ollama al directorio de usuario. Devuelve True si tiene éxito."""
    system = platform.system()
    machine = platform.machine()
    url = _DOWNLOAD_MAP.get((system, machine))

    if not url:
        if system == "Windows":
            print(
                "  En Windows instala Ollama manualmente desde https://ollama.com/download\n"
                "  Una vez instalado, vuelve a ejecutar appcli-install."
            )
        else:
            print(f"  Plataforma no soportada para descarga automática: {system} {machine}")
        return False

    dest = _user_ollama_bin()
    dest.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Descargando Ollama para {system} {machine}...")
    try:
        def _progress(count, block_size, total):
            if total > 0:
                pct = min(count * block_size * 100 // total, 100)
                print(f"\r  {pct}% ", end="", flush=True)

        urllib.request.urlretrieve(url, dest, reporthook=_progress)
        print()
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"  Ollama instalado en {dest}")
        return True
    except Exception as exc:
        print(f"  Error al descargar Ollama: {exc}")
        return False


# --- Gestión de Ollama ---

def _ping() -> bool:
    try:
        import ollama as _ollama
        _ollama.list()
        return True
    except Exception:
        return False


def _ensure_ollama_running() -> subprocess.Popen | None:
    if _ping():
        return None
    print("  Iniciando Ollama...")
    proc = subprocess.Popen(
        [_ollama_bin(), "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(0.5)
        if _ping():
            print("  Ollama listo.")
            return proc
    print("  Error: Ollama no responde tras el arranque.")
    return None


def _modelos_disponibles() -> list[str]:
    try:
        import ollama as _ollama
        return [m.model for m in _ollama.list().models]
    except Exception:
        return []


# --- Selección de modelo ---

_MODELOS_RECOMENDADOS = [
    ("qwen2.5:1.5b",  "Qwen 2.5 1.5B  — ligero, ~1 GB, recomendado para equipos con poca RAM"),
    ("qwen2.5:3b",    "Qwen 2.5 3B    — equilibrio calidad/recursos, ~2 GB"),
    ("qwen2.5:7b",    "Qwen 2.5 7B    — mejor calidad, ~5 GB"),
    ("llama3.2:3b",   "Llama 3.2 3B   — buen soporte tool calling, ~2 GB"),
    ("mistral:7b",    "Mistral 7B     — alta calidad, ~5 GB"),
]


def _elegir_modelo() -> str:
    print("\nElige el modelo base para el asistente IA:\n")
    for i, (tag, desc) in enumerate(_MODELOS_RECOMENDADOS, 1):
        print(f"  {i}. {desc}")
    print(f"  {len(_MODELOS_RECOMENDADOS) + 1}. Introducir un modelo personalizado")

    while True:
        raw = input("\nOpción [1]: ").strip()
        if raw == "":
            return _MODELOS_RECOMENDADOS[0][0]
        if raw.isdigit():
            n = int(raw)
            if 1 <= n <= len(_MODELOS_RECOMENDADOS):
                return _MODELOS_RECOMENDADOS[n - 1][0]
            if n == len(_MODELOS_RECOMENDADOS) + 1:
                modelo = input("Nombre del modelo (p. ej. gemma3:4b): ").strip()
                if modelo:
                    return modelo
        print("  Opción no válida, inténtalo de nuevo.")


# --- Creación del modelo personalizado ---

def _crear_ifc_assistant(base_model: str) -> bool:
    print(f"\n  Creando modelo ifc-assistant basado en {base_model}...")
    try:
        modelfile_content = _MODELFILE.read_text(encoding="utf-8")
        modelfile_content = modelfile_content.replace("{{BASE_MODEL}}", base_model)
        if "{{MANUAL_USUARIO}}" in modelfile_content:
            manual = _MANUAL_FILE.read_text(encoding="utf-8") if _MANUAL_FILE.exists() else ""
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

        print(f"  Modelo {_CUSTOM_MODEL} creado correctamente.")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"  Error al crear {_CUSTOM_MODEL}: {exc}")
        return False


# --- Acceso directo de escritorio ---

def _instalar_acceso_directo() -> None:
    if platform.system() != "Linux":
        return
    if not _DESKTOP_SRC.exists():
        return
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    dest = desktop_dir / "appcli.desktop"
    shutil.copy(_DESKTOP_SRC, dest)
    try:
        subprocess.run(
            ["update-desktop-database", str(desktop_dir)],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass
    print(f"  Acceso directo instalado en {dest}")


# --- Punto de entrada ---

def main() -> None:
    print("=== Instalador de AppCLI ===\n")

    # 1. Comprobar / descargar Ollama
    if _system_ollama():
        print(f"✓ Ollama encontrado en el sistema: {_system_ollama()}")
    elif _user_ollama_bin().exists():
        print(f"✓ Ollama encontrado en {_user_ollama_bin()}")
    else:
        print("Ollama no está instalado. Se descargará ahora.")
        if not _download_ollama():
            print("\nNo se pudo instalar Ollama. Instálalo manualmente y vuelve a ejecutar appcli-install.")
            sys.exit(1)

    # 2. Selección de modelo
    base_model = _elegir_modelo()

    # 3. Arrancar Ollama y descargar el modelo base
    proc = _ensure_ollama_running()
    modelos = _modelos_disponibles()
    base_tag = base_model.split(":")[0]
    if not any(base_tag in m for m in modelos):
        print(f"\n  Descargando {base_model} (puede tardar varios minutos)...")
        try:
            subprocess.run(
                [_ollama_bin(), "pull", base_model],
                check=True,
            )
        except subprocess.CalledProcessError:
            print(f"  Error al descargar {base_model}.")
            if proc:
                proc.terminate()
            sys.exit(1)
    else:
        print(f"  Modelo {base_model} ya disponible.")

    # 4. Crear ifc-assistant
    if not _crear_ifc_assistant(base_model):
        if proc:
            proc.terminate()
        sys.exit(1)

    # 5. Guardar configuración
    config.save({"base_model": base_model})
    print(f"  Configuración guardada en ~/.config/appcli/config.json")

    # 6. Acceso directo
    _instalar_acceso_directo()

    if proc:
        proc.terminate()

    print("\n✓ Instalación completada. Ejecuta 'appcli' para iniciar la aplicación.")
