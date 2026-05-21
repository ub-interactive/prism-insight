"""
Backward-compatible shim. Implementation: scripts.check_market_day.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "check_market_day.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.check_market_day import *  # noqa: F403
