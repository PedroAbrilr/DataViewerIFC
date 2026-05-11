"""Tests unitarios para config y disponibilidad de backends."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from dataviewerifc import config
from dataviewerifc.ai.backends import ClaudeBackend, OllamaBackend, OpenAIBackend


# ------------------------------------------------------------------
# config.load
# ------------------------------------------------------------------

def test_load_defaults_sin_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_CONFIG_FILE", tmp_path / "config.json")
    cfg = config.load()
    assert cfg["active_backend"] == "ollama"
    assert cfg["ollama_base_model"] == ""
    assert cfg["claude_model"] == "claude-sonnet-4-6"
    assert cfg["openai_model"] == "gpt-4o-mini"


def test_load_mezcla_con_defaults(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text(json.dumps({"active_backend": "claude"}), encoding="utf-8")
    monkeypatch.setattr(config, "_CONFIG_FILE", cfg_file)
    cfg = config.load()
    assert cfg["active_backend"] == "claude"
    assert cfg["ollama_base_model"] == ""  # default intacto


def test_load_archivo_corrupto(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    cfg_file.write_text("no es json", encoding="utf-8")
    monkeypatch.setattr(config, "_CONFIG_FILE", cfg_file)
    cfg = config.load()
    assert cfg["active_backend"] == "ollama"


# ------------------------------------------------------------------
# config.save
# ------------------------------------------------------------------

def test_save_crea_archivo(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr(config, "_CONFIG_FILE", cfg_file)
    monkeypatch.setattr(config, "_CONFIG_DIR", tmp_path)
    config.save({"active_backend": "openai"})
    assert cfg_file.exists()
    data = json.loads(cfg_file.read_text())
    assert data["active_backend"] == "openai"


# ------------------------------------------------------------------
# config.inject_env
# ------------------------------------------------------------------

def test_inject_env_inyecta_claves(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config.inject_env({
        "anthropic_api_key": "sk-ant-test",
        "openai_api_key": "sk-oai-test",
    })
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test"
    assert os.environ["OPENAI_API_KEY"] == "sk-oai-test"


def test_inject_env_no_sobreescribe_existente(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-original")
    config.inject_env({"anthropic_api_key": "clave-nueva"})
    assert os.environ["ANTHROPIC_API_KEY"] == "clave-original"


def test_inject_env_ignora_claves_vacias(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config.inject_env({"anthropic_api_key": ""})
    assert "ANTHROPIC_API_KEY" not in os.environ


# ------------------------------------------------------------------
# OllamaBackend
# ------------------------------------------------------------------

def test_ollama_display_name():
    b = OllamaBackend(model="ifc-assistant")
    assert "ifc-assistant" in b.display_name


def test_ollama_current_model():
    b = OllamaBackend(model="ifc-assistant")
    assert b.current_model == "ifc-assistant"


def test_ollama_is_available_siempre_true():
    # OllamaBackend no comprueba conectividad en is_available; usa el default de AIBackend
    b = OllamaBackend(model="ifc-assistant")
    ok, msg = b.is_available()
    assert ok is True
    assert msg == ""


# ------------------------------------------------------------------
# ClaudeBackend
# ------------------------------------------------------------------

def test_claude_display_name():
    b = ClaudeBackend(model="claude-sonnet-4-6")
    assert "claude-sonnet-4-6" in b.display_name


def test_claude_is_available_sin_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    b = ClaudeBackend(model="claude-sonnet-4-6")
    ok, msg = b.is_available()
    assert ok is False
    assert "ANTHROPIC_API_KEY" in msg


def test_claude_is_available_con_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    b = ClaudeBackend(model="claude-sonnet-4-6")
    with patch.dict("sys.modules", {"anthropic": MagicMock()}):
        ok, _ = b.is_available()
    assert ok is True


# ------------------------------------------------------------------
# OpenAIBackend
# ------------------------------------------------------------------

def test_openai_display_name():
    b = OpenAIBackend(model="gpt-4o-mini")
    assert "gpt-4o-mini" in b.display_name


def test_openai_is_available_sin_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    b = OpenAIBackend(model="gpt-4o-mini")
    ok, msg = b.is_available()
    assert ok is False
    assert "OPENAI_API_KEY" in msg


def test_claude_is_available_sin_paquete(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    b = ClaudeBackend(model="claude-sonnet-4-6")
    with patch.dict("sys.modules", {"anthropic": None}):
        ok, msg = b.is_available()
    assert ok is False
    assert "anthropic" in msg.lower()


def test_openai_is_available_sin_paquete(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oai-test")
    b = OpenAIBackend(model="gpt-4o-mini")
    with patch.dict("sys.modules", {"openai": None}):
        ok, msg = b.is_available()
    assert ok is False
    assert "openai" in msg.lower()


def test_openai_is_available_con_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-oai-test")
    b = OpenAIBackend(model="gpt-4o-mini")
    with patch.dict("sys.modules", {"openai": MagicMock()}):
        ok, _ = b.is_available()
    assert ok is True
