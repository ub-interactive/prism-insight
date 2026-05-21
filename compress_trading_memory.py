"""
Backward-compatible shim. Implementation: scripts.compress_trading_memory.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "compress_trading_memory.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.compress_trading_memory import *  # noqa: F403
