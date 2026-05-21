"""Shared pytest fixtures for PRISM-INSIGHT tests."""

import sqlite3

import pytest

from tracking.db_schema import create_all_tables, create_indexes


@pytest.fixture
def tmp_db(tmp_path):
    """Yield a temporary SQLite database with all PRISM tables created."""
    db_path = tmp_path / "stock_tracking_db.sqlite"
    conn = sqlite3.connect(str(db_path))
    create_all_tables(conn)
    create_indexes(conn)
    yield conn
    conn.close()


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a path string for a temporary SQLite database with schema applied."""
    db_path = tmp_path / "stock_tracking_db.sqlite"
    conn = sqlite3.connect(str(db_path))
    create_all_tables(conn)
    create_indexes(conn)
    conn.close()
    return str(db_path)
