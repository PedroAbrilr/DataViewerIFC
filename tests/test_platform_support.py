"""Tests para la capa de abstracción de plataforma."""

import os
import stat
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import appcli.platform_support as ps


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Resetea el singleton entre tests."""
    original = ps._instance
    ps._instance = None
    yield
    ps._instance = original


# ---------------------------------------------------------------------------
# LinuxPlatform
# ---------------------------------------------------------------------------

class TestLinuxPlatform:
    @pytest.fixture
    def plat(self):
        return ps.LinuxPlatform()

    def test_config_dir(self, plat):
        assert plat.config_dir == Path.home() / ".config" / "appcli"

    def test_data_dir(self, plat):
        assert plat.data_dir == Path.home() / ".local" / "share" / "appcli"

    def test_ollama_bin_name(self, plat):
        assert plat.ollama_bin_name == "ollama"

    def test_ollama_bin_path(self, plat):
        assert plat.ollama_bin_path == plat.data_dir / "ollama" / "ollama"

    def test_ollama_download_url_x86(self, plat):
        with patch("platform.machine", return_value="x86_64"):
            url = plat.ollama_download_url()
        assert url and "amd64" in url

    def test_ollama_download_url_arm(self, plat):
        with patch("platform.machine", return_value="aarch64"):
            url = plat.ollama_download_url()
        assert url and "arm64" in url

    def test_ollama_download_url_unsupported(self, plat):
        with patch("platform.machine", return_value="riscv64"):
            assert plat.ollama_download_url() is None

    def test_shortcut_path(self, plat):
        expected = Path.home() / ".local" / "share" / "applications" / "appcli.desktop"
        assert plat.shortcut_path == expected

    def test_is_executable_missing(self, plat, tmp_path):
        assert not plat.is_executable(tmp_path / "nope")

    def test_is_executable_true(self, plat, tmp_path):
        f = tmp_path / "bin"
        f.write_bytes(b"")
        f.chmod(f.stat().st_mode | stat.S_IXUSR)
        assert plat.is_executable(f)

    def test_models_dir_env(self, plat, tmp_path, monkeypatch):
        monkeypatch.setenv("OLLAMA_MODELS", str(tmp_path))
        assert plat.models_dir == tmp_path

    def test_models_dir_default(self, plat, monkeypatch):
        monkeypatch.delenv("OLLAMA_MODELS", raising=False)
        assert plat.models_dir == plat.ollama_dir / "models"


# ---------------------------------------------------------------------------
# MacOSPlatform
# ---------------------------------------------------------------------------

class TestMacOSPlatform:
    @pytest.fixture
    def plat(self):
        return ps.MacOSPlatform()

    def test_config_dir(self, plat):
        assert plat.config_dir == Path.home() / ".config" / "appcli"

    def test_ollama_download_url(self, plat):
        url = plat.ollama_download_url()
        assert url and "darwin" in url

    def test_shortcut_path_none(self, plat):
        assert plat.shortcut_path is None


# ---------------------------------------------------------------------------
# WindowsPlatform
# ---------------------------------------------------------------------------

class TestWindowsPlatform:
    @pytest.fixture
    def plat(self):
        return ps.WindowsPlatform()

    def test_config_dir_from_env(self, plat, monkeypatch):
        monkeypatch.setenv("APPDATA", "C:\\Users\\Test\\AppData\\Roaming")
        assert "appcli" in str(plat.config_dir)

    def test_config_dir_fallback(self, plat, monkeypatch):
        monkeypatch.delenv("APPDATA", raising=False)
        assert plat.config_dir == Path.home() / "AppData" / "Roaming" / "appcli"

    def test_ollama_bin_name(self, plat):
        assert plat.ollama_bin_name == "ollama.exe"

    def test_is_executable_exe(self, plat, tmp_path):
        f = tmp_path / "ollama.exe"
        f.write_bytes(b"")
        assert plat.is_executable(f)

    def test_is_executable_non_exe(self, plat, tmp_path):
        f = tmp_path / "ollama"
        f.write_bytes(b"")
        assert not plat.is_executable(f)

    def test_set_executable_noop(self, plat, tmp_path):
        f = tmp_path / "file.exe"
        f.write_bytes(b"")
        plat.set_executable(f)  # debe no lanzar excepción

    def test_ollama_download_url_none(self, plat):
        assert plat.ollama_download_url() is None

    def test_ollama_install_hint(self, plat):
        assert "https://ollama.com" in plat.ollama_install_hint()

    def test_config_dir_display(self, plat, monkeypatch):
        monkeypatch.setenv("APPDATA", "C:\\Users\\Test\\AppData\\Roaming")
        assert "appcli" in plat.config_dir_display


# ---------------------------------------------------------------------------
# get_platform singleton
# ---------------------------------------------------------------------------

class TestGetPlatform:
    def test_returns_linux_on_linux(self):
        with patch("platform.system", return_value="Linux"):
            p = ps.get_platform()
        assert isinstance(p, ps.LinuxPlatform)

    def test_returns_macos_on_darwin(self):
        with patch("platform.system", return_value="Darwin"):
            p = ps.get_platform()
        assert isinstance(p, ps.MacOSPlatform)

    def test_returns_windows_on_windows(self):
        with patch("platform.system", return_value="Windows"):
            p = ps.get_platform()
        assert isinstance(p, ps.WindowsPlatform)

    def test_singleton(self):
        p1 = ps.get_platform()
        p2 = ps.get_platform()
        assert p1 is p2
