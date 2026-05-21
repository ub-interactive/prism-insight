"""
Backward-compatible shim. Implementation: scripts.pending_order_batch.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "pending_order_batch.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.pending_order_batch import *  # noqa: F403
