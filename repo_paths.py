"""
Canonical repository root for resolving reports, logs, SQLite, and configs.

Imports use `repo_paths.REPO_ROOT` instead of Path(__file__).parent so code
still resolves correctly when living under scripts/, reporting/, integrations/.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
