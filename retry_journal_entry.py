"""
Backward-compatible shim. Implementation: scripts.retry_journal_entry.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "scripts" / "retry_journal_entry.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from scripts.retry_journal_entry import *  # noqa: F403
