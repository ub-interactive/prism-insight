"""Backward-compatible CLI shim → prism.ops.batches.pending_order_batch."""

import runpy
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root / "src"))
runpy.run_module("prism.ops.batches.pending_order_batch", run_name="__main__")
