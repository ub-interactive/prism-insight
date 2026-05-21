"""
Backward-compatible shim. Implementation: scripts.performance_tracker_batch.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "performance_tracker_batch.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.performance_tracker_batch import *  # noqa: F403
