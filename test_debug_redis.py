"""
Backward-compatible shim. Implementation: scripts.test_debug_redis.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "test_debug_redis.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
