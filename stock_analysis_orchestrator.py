"""
Backward-compatible shim. Implementation: scripts.stock_analysis_orchestrator.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "stock_analysis_orchestrator.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.stock_analysis_orchestrator import *  # noqa: F403
