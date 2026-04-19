"""Gestión de la configuración de usuario (~/.config/appcli/config.json)."""

import json
import os
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "appcli"
_CONFIG_FILE = _CONFIG_DIR / "config.json"
_DEFAULTS: dict = {
    "base_model":        "qwen2.5:1.5b",
    "active_backend":    "ollama",
    "ollama_model":      "ifc-assistant",
    "claude_model":      "claude-sonnet-4-6",
    "openai_model":      "gpt-4o-mini",
}


def load() -> dict:
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **data}
        except Exception:
            pass
    return dict(_DEFAULTS)


def inject_env(cfg: dict | None = None) -> None:
    """Inyecta las API keys guardadas en config.json como variables de entorno."""
    if cfg is None:
        cfg = load()
    if cfg.get("anthropic_api_key"):
        os.environ.setdefault("ANTHROPIC_API_KEY", cfg["anthropic_api_key"])
    if cfg.get("openai_api_key"):
        os.environ.setdefault("OPENAI_API_KEY", cfg["openai_api_key"])


def save(data: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    current = load()
    current.update(data)
    _CONFIG_FILE.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
