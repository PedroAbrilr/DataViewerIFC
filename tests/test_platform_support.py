"""Tests para la capa de abstracción de plataforma."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import dataviewerifc.platform_support as ps


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
        assert plat.config_dir == Path.home() / ".config" / "dataviewerifc"

    def test_data_dir(self, plat):
        assert plat.data_dir == Path.home() / ".local" / "share" / "dataviewerifc"

    def test_shortcut_path(self, plat):
        expected = Path.home() / ".local" / "share" / "applications" / "dataviewerifc.desktop"
        assert plat.shortcut_path == expected


# ---------------------------------------------------------------------------
# MacOSPlatform
# ---------------------------------------------------------------------------

class TestMacOSPlatform:
    @pytest.fixture
    def plat(self):
        return ps.MacOSPlatform()

    def test_config_dir(self, plat):
        assert plat.config_dir == Path.home() / ".config" / "dataviewerifc"

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
        assert "dataviewerifc" in str(plat.config_dir)

    def test_config_dir_fallback(self, plat, monkeypatch):
        monkeypatch.delenv("APPDATA", raising=False)
        assert plat.config_dir == Path.home() / "AppData" / "Roaming" / "dataviewerifc"

    def test_config_dir_display(self, plat, monkeypatch):
        monkeypatch.setenv("APPDATA", "C:\\Users\\Test\\AppData\\Roaming")
        assert "dataviewerifc" in plat.config_dir_display


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
