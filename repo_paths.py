"""Backward-compatible shim. Canonical paths: prism.paths."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_src = _root / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from prism.paths import (  # noqa: E402
    CONFIG_DIR,
    HTML_REPORTS_DIR,
    LOGS_DIR,
    PDF_REPORTS_DIR,
    REPORTS_DIR,
    REPO_ROOT,
    TRIGGER_RESULTS_DIR,
    VAR_ROOT,
)

__all__ = [
    "CONFIG_DIR",
    "HTML_REPORTS_DIR",
    "LOGS_DIR",
    "PDF_REPORTS_DIR",
    "REPORTS_DIR",
    "REPO_ROOT",
    "TRIGGER_RESULTS_DIR",
    "VAR_ROOT",
]
