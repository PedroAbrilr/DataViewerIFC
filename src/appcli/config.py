"""Gestión de la configuración de usuario (~/.config/appcli/config.json)."""

import json
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "appcli"
_CONFIG_FILE = _CONFIG_DIR / "config.json"
_DEFAULTS: dict = {"base_model": "qwen2.5:1.5b"}


def load() -> dict:
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **data}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save(data: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    current = load()
    current.update(data)
    _CONFIG_FILE.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
