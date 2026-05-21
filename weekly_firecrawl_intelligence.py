"""
Backward-compatible shim. Implementation: scripts.weekly_firecrawl_intelligence.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "weekly_firecrawl_intelligence.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.weekly_firecrawl_intelligence import *  # noqa: F403
