#!/usr/bin/env python3
"""Legacy YouTube crawler tests — upstream module is not in this repository."""

import pytest

pytest.skip(
    "Depends on youtube_event_fund_crawler module not present in this repository",
    allow_module_level=True,
)
