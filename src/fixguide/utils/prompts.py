"""Prompt loading and rendering with Jinja2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from jinja2 import Environment

_env: Environment | None = None
_templates: dict[str, dict[str, Any]] = {}


def get_prompt_env() -> Environment:
    """Get or create the cached Jinja2 prompt environment."""
    global _env
    if _env is None:
        _env = Environment(autoescape=False)
    return _env


def _load_prompt_yaml(name: str) -> dict[str, Any]:
    """Load and cache the raw prompt YAML file."""
    if name not in _templates:
        prompt_path = (
            Path(__file__).parent.parent.parent.parent / "config" / "prompts" / f"{name}.yaml"
        )
        with prompt_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _templates[name] = data
    return _templates[name]


def render_prompt(name: str, context: dict[str, Any]) -> dict[str, Any]:
    """Render a prompt template with context."""
    env = get_prompt_env()
    raw = _load_prompt_yaml(name)

    system_tmpl = env.from_string(raw.get("system", ""))
    user_tmpl = env.from_string(raw.get("user", ""))

    return {
        "system": system_tmpl.render(**context),
        "user": user_tmpl.render(**context),
    }
