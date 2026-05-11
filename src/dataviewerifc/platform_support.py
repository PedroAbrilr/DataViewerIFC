"""Abstracción de diferencias de sistema operativo relevantes para DataViewerIFC."""

import os
import platform
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class Platform(ABC):
    """Interfaz de plataforma: rutas y acceso directo."""

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
    def shortcut_path(self) -> Path | None:
        """Ruta del acceso directo de escritorio, o None si no aplica."""
        return None

    # ---- Comportamientos ----

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


class LinuxPlatform(_UnixPlatform):

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
    pass


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
