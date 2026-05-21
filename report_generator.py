"""
Backward-compatible shim. Implementation: reporting.report_generator.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "reporting" / "report_generator.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from reporting.report_generator import *  # noqa: F403
