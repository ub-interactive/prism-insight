"""
Backward-compatible shim. Implementation: scripts.weekly_insight_report.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "weekly_insight_report.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.weekly_insight_report import *  # noqa: F403
