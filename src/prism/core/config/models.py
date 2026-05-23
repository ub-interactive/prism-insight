"""
Model configuration helpers for mcp_agent.config.yaml.

OpenAI-chat models live under ``openai.models.<key>`` (see example YAML).
Anthropic Claude models live under ``anthropic.models.<key>`` with optional ``anthropic.default_model``.
Firecrawl Spark agent model: ``firecrawl.spark_agent_model`` (optional).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from functools import lru_cache

import yaml

from prism.paths import CONFIG_DIR

logger = logging.getLogger(__name__)

_CONFIG_PATH = CONFIG_DIR / "mcp_agent.config.yaml"

_DEFAULT_ARCHIVE_QUERY_MODELS = [
    "gpt-5.4-mini",
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-4.1-nano",
]

_DEFAULT_CHATGPT_PROXY_MAP: dict[str, str] = {
    "gpt-4o": "gpt-5.4-mini",
    "gpt-4o-mini": "gpt-5.4-mini",
    "gpt-4o-2024-08-06": "gpt-5.4-mini",
    "gpt-4-turbo": "gpt-5.4-mini",
    "gpt-4": "gpt-5.4-mini",
    "gpt-3.5-turbo": "gpt-5.4-mini",
    "o4-mini": "gpt-5.4-mini",
    "o3-mini": "gpt-5.4-mini",
}


@lru_cache(maxsize=1)
def _read_config() -> dict:
    """Load mcp_agent.config.yaml once and cache result."""
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.debug("mcp_agent.config.yaml not found at %s", _CONFIG_PATH)
        return {}
    except Exception as e:
        logger.warning("Failed reading mcp_agent.config.yaml: %s", e)
        return {}


def clear_model_config_cache() -> None:
    """Drop cached YAML (tests or reload after editing config)."""
    _read_config.cache_clear()


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


def get_configured_anthropic_model(model_key: str, default_model: str) -> str:
    """Resolve ``anthropic.models.<model_key>`` or ``anthropic.default_model``."""
    root = _read_config()
    block = root.get("anthropic")
    if not isinstance(block, Mapping):
        return default_model

    mmap = block.get("models")
    if isinstance(mmap, Mapping):
        value = mmap.get(model_key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    fallback = block.get("default_model")
    if isinstance(fallback, str) and fallback.strip():
        return fallback.strip()
    return default_model


def get_archive_query_allowed_models() -> list[str]:
    """Models permitted for archive CLI/API when ``openai.archive_query_allowed_models`` is set."""
    openai_cfg = _read_config().get("openai", {})
    if not isinstance(openai_cfg, Mapping):
        return list(_DEFAULT_ARCHIVE_QUERY_MODELS)

    raw = openai_cfg.get("archive_query_allowed_models")
    if isinstance(raw, list):
        cleaned = [str(x).strip() for x in raw if isinstance(x, (str, int, float)) and str(x).strip()]
        if cleaned:
            return cleaned
    return list(_DEFAULT_ARCHIVE_QUERY_MODELS)


def get_chatgpt_proxy_codex_model_map() -> dict[str, str]:
    """
    Maps legacy ChatGPT client model IDs to Codex/Responses gateway models.

    ``openai.chatgpt_proxy_fallback_model`` replaces all built-in defaults when set,
    then ``openai.chatgpt_proxy_model_map`` applies per-key overrides.
    """
    openai_cfg = _read_config().get("openai", {})
    if not isinstance(openai_cfg, Mapping):
        return dict(_DEFAULT_CHATGPT_PROXY_MAP)

    merged: dict[str, str] = dict(_DEFAULT_CHATGPT_PROXY_MAP)
    global_fb = openai_cfg.get("chatgpt_proxy_fallback_model")
    if isinstance(global_fb, str) and global_fb.strip():
        fb = global_fb.strip()
        merged = {k: fb for k in merged}

    overrides = openai_cfg.get("chatgpt_proxy_model_map")
    if isinstance(overrides, Mapping):
        for key, val in overrides.items():
            if isinstance(key, str) and isinstance(val, str) and val.strip():
                merged[key] = val.strip()
    return merged


def get_chatgpt_proxy_request_default_model() -> str:
    """Default ``model`` when the incoming Chat Completions body omits it."""
    openai_cfg = _read_config().get("openai", {})
    if not isinstance(openai_cfg, Mapping):
        return "gpt-4o"
    raw = openai_cfg.get("chatgpt_proxy_request_default_model")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "gpt-4o"


def get_configured_firecrawl_spark_model(default_model: str = "spark-1-mini") -> str:
    """
    Spark model ID for Firecrawl's ``app.agent()`` (``firecrawl_client.firecrawl_agent``).

    Reads ``firecrawl.spark_agent_model`` from ``mcp_agent.config.yaml``.
    """
    block = _read_config().get("firecrawl")
    if not isinstance(block, Mapping):
        return default_model
    raw = block.get("spark_agent_model")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return default_model


def get_optional_reasoning_effort(
    model_name: str,
    preferred_effort: str = "none",
) -> dict[str, str]:
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
