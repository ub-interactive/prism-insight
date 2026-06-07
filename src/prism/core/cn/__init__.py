"""CN A-share analysis pipeline."""

from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    if name == "analysis":
        return import_module("prism.core.cn.analysis")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
