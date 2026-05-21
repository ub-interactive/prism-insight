"""
Backward-compatible shim. Implementation: scripts.trigger_batch.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "trigger_batch.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.trigger_batch import *  # noqa: F403
