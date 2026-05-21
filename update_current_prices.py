"""
Backward-compatible shim. Implementation: scripts.update_current_prices.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "update_current_prices.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.update_current_prices import *  # noqa: F403
