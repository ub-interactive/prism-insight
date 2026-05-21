"""
Backward-compatible shim. Implementation: reporting.pdf_converter.
"""

import pathlib
import runpy

_IMPL = pathlib.Path(__file__).resolve().parent / "reporting" / "pdf_converter.py"


if __name__ == "__main__":
    runpy.run_path(str(_IMPL), run_name="__main__")
else:
    from reporting.pdf_converter import *  # noqa: F403
