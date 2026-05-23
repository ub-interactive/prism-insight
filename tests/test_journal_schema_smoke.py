#!/usr/bin/env python3
"""US journal schema smoke tests (thin coverage for journal DDL + compression stats)."""

import os
import sqlite3
import tempfile
from unittest.mock import MagicMock

import pytest

from stock_tracking_agent import StockTrackingAgent


@pytest.mark.asyncio
async def test_journal_tables_created_with_enable_journal():
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = tmp.name
    tmp.close()
    try:
        agent = StockTrackingAgent(db_path=path, enable_journal=True)
        agent.trading_agent = MagicMock()
        await agent.initialize()
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute(
            """SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN
            ('trading_journal','trading_principles','trading_intuitions')"""
        )
        assert cur.fetchone()[0] == 3
        cur.execute("PRAGMA table_info(trading_intuitions)")
        cols = {r[1] for r in cur.fetchall()}
        assert "scope" in cols
        assert "market" in cols
        conn.close()
        agent.conn.close()
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_compression_stats_shape_with_enable_journal():
    tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
    path = tmp.name
    tmp.close()
    try:
        agent = StockTrackingAgent(db_path=path, enable_journal=True)
        agent.trading_agent = MagicMock()
        await agent.initialize()

        stats = agent.get_compression_stats()
        assert "entries_by_layer" in stats
        ebl = stats["entries_by_layer"]
        assert ebl.get("layer1_detailed") == 0
        assert "active_intuitions" in stats
        assert "active_principles" in stats

        agent.conn.close()
    finally:
        os.unlink(path)
