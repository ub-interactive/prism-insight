#!/usr/bin/env python3
"""Legacy stock tracking script — upstream modules are not in this repository."""

import pytest

pytest.skip(
    "Depends on legacy stock_tracking_enhanced_agent not present in this repository",
    allow_module_level=True,
)
