"""Backward-compatible CLI shim → prism.ops.pipelines.stock_tracking_agent."""

import runpy
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root / "src"))
runpy.run_module("prism.ops.pipelines.stock_tracking_agent", run_name="__main__")
