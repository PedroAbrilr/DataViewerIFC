"""Abstracción de diferencias de sistema operativo relevantes para DataViewerIFC."""

import os
import platform
import shutil
import stat
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

_OLLAMA_BASE = "https://github.com/ollama/ollama/releases/latest/download"


class Platform(ABC):
    """Interfaz de plataforma: rutas, permisos, descarga y acceso directo."""

    # ---- Rutas ----

    @property
    @abstractmethod
    def config_dir(self) -> Path:
        """Directorio de configuración del usuario."""

    @property
    @abstractmethod
    def data_dir(self) -> Path:
        """Directorio de datos del usuario."""

    @property
    def ollama_dir(self) -> Path:
        return self.data_dir / "ollama"

    @property
    @abstractmethod
    def ollama_bin_name(self) -> str:
        """Nombre del ejecutable de Ollama."""

    @property
    def ollama_bin_path(self) -> Path:
        return self.ollama_dir / self.ollama_bin_name

    @property
    def models_dir(self) -> Path:
        """Directorio de modelos (respeta OLLAMA_MODELS si está definido)."""
        env = os.environ.get("OLLAMA_MODELS")
        return Path(env) if env else self.ollama_dir / "models"

    @property
    def shortcut_path(self) -> Path | None:
        """Ruta del acceso directo de escritorio, o None si no aplica."""
        return None

    # ---- Comportamientos ----

    @abstractmethod
    def is_executable(self, path: Path) -> bool:
        """Comprueba si un archivo es ejecutable en esta plataforma."""

    @abstractmethod
    def set_executable(self, path: Path) -> None:
        """Marca un archivo como ejecutable (no-op en Windows)."""

    @abstractmethod
    def ollama_download_url(self) -> str | None:
        """URL de descarga automática de Ollama, o None si requiere instalación manual."""

    def ollama_install_hint(self) -> str:
        """Mensaje de ayuda cuando no hay descarga automática disponible."""
        return (
            f"Plataforma no soportada para descarga automática: "
            f"{platform.system()} {platform.machine()}"
        )

    def install_shortcut(self, desktop_src: Path) -> None:
        """Instala el acceso directo de escritorio (no-op salvo en Linux)."""

    # ---- Display ----

    @property
    def config_dir_display(self) -> str:
        """Ruta de configuración legible para mostrar al usuario."""
        return str(self.config_dir)


class _UnixPlatform(Platform):
    """Base compartida para Linux y macOS."""

    @property
    def config_dir(self) -> Path:
        return Path.home() / ".config" / "dataviewerifc"

    @property
    def data_dir(self) -> Path:
        return Path.home() / ".local" / "share" / "dataviewerifc"

    @property
    def ollama_bin_name(self) -> str:
        return "ollama"

    def is_executable(self, path: Path) -> bool:
        return path.exists() and os.access(path, os.X_OK)

    def set_executable(self, path: Path) -> None:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def ollama_download_url(self) -> str | None:
        return None


class LinuxPlatform(_UnixPlatform):

    def ollama_download_url(self) -> str | None:
        urls = {
            "x86_64":  f"{_OLLAMA_BASE}/ollama-linux-amd64",
            "aarch64": f"{_OLLAMA_BASE}/ollama-linux-arm64",
        }
        return urls.get(platform.machine())

    @property
    def shortcut_path(self) -> Path | None:
        return Path.home() / ".local" / "share" / "applications" / "dataviewerifc.desktop"

    def install_shortcut(self, desktop_src: Path) -> None:
        if not desktop_src.exists():
            return
        dest = self.shortcut_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(desktop_src, dest)
        try:
            subprocess.run(
                ["update-desktop-database", str(dest.parent)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass


class MacOSPlatform(_UnixPlatform):

    def ollama_download_url(self) -> str | None:
        return f"{_OLLAMA_BASE}/ollama-darwin"


class WindowsPlatform(Platform):

    @property
    def config_dir(self) -> Path:
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
        return base / "dataviewerifc"

    @property
    def data_dir(self) -> Path:
        localappdata = os.environ.get("LOCALAPPDATA")
        base = Path(localappdata) if localappdata else Path.home() / "AppData" / "Local"
        return base / "dataviewerifc"

    @property
    def ollama_bin_name(self) -> str:
        return "ollama.exe"

    def is_executable(self, path: Path) -> bool:
        return path.exists() and path.suffix.lower() == ".exe"

    def set_executable(self, path: Path) -> None:
        pass  # Windows: ejecutable por extensión, sin bits de permisos

    def ollama_download_url(self) -> str | None:
        return None

    def ollama_install_hint(self) -> str:
        return (
            "En Windows instala Ollama manualmente desde https://ollama.com/download\n"
            "Una vez instalado, vuelve a ejecutar dataviewerifc-install."
        )

    @property
    def config_dir_display(self) -> str:
        appdata = os.environ.get("APPDATA", "%APPDATA%")
        return str(Path(appdata) / "dataviewerifc")


_instance: Platform | None = None


def get_platform() -> Platform:
    """Devuelve el singleton de Platform para el SO actual."""
    global _instance
    if _instance is None:
        system = platform.system()
        if system == "Windows":
            _instance = WindowsPlatform()
        elif system == "Darwin":
            _instance = MacOSPlatform()
        else:
            _instance = LinuxPlatform()
    return _instance
