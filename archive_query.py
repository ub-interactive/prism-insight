"""
Backward-compatible shim. Implementation: integrations.archive_query.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "integrations" / "archive_query.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from integrations.archive_query import *  # noqa: F403
