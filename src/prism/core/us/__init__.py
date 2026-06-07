"""US market analysis pipeline."""

from importlib import import_module
from typing import Any


def __getattr__(name: str) -> Any:
    if name == "analysis":
        return import_module("prism.core.us.analysis")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
