"""
Model configuration helpers for mcp_agent.config.yaml.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict

import yaml

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "mcp_agent.config.yaml"


@lru_cache(maxsize=1)
def _read_config() -> Dict:
    """Load mcp_agent.config.yaml once and cache result."""
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.debug("mcp_agent.config.yaml not found at %s", _CONFIG_PATH)
        return {}
    except Exception as e:
        logger.warning("Failed reading mcp_agent.config.yaml: %s", e)
        return {}


def get_configured_model(model_key: str, default_model: str) -> str:
    """Return model override from openai.models.<model_key>, else default."""
    openai_cfg = _read_config().get("openai", {})
    if not isinstance(openai_cfg, dict):
        return default_model

    model_map = openai_cfg.get("models", {})
    if not isinstance(model_map, dict):
        return default_model

    value = model_map.get(model_key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default_model


def get_optional_reasoning_effort(
    model_name: str,
    preferred_effort: str = "none",
) -> Dict[str, str]:
    """
    Return reasoning_effort only for model families that reliably support it.

    DeepSeek-compatible safety: omit reasoning_effort for non-OpenAI model names
    to avoid provider-side validation failures (e.g. reasoning_effort="none").
    """
    normalized = (model_name or "").strip().lower()
    if not normalized:
        return {}

    supports_reasoning_effort = normalized.startswith(("gpt-", "o1", "o3", "o4"))
    if supports_reasoning_effort:
        return {"reasoning_effort": preferred_effort}
    return {}
