"""
Backward-compatible shim. Implementation: integrations.archive_api.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "integrations" / "archive_api.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from integrations.archive_api import *  # noqa: F403
