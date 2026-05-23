"""Canonical repository paths for PRISM-INSIGHT."""

from pathlib import Path

# src/prism/paths.py -> src/ is one level up; repo root is two levels up
SRC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SRC_ROOT.parent
CONFIG_DIR = SRC_ROOT / "config"
MCP_CONFIG_PATH = CONFIG_DIR / "mcp_agent.config.yaml"
DEPLOY_DIR = REPO_ROOT / "deploy"
VENDOR_DIR = SRC_ROOT / "vendor"
VAR_ROOT = SRC_ROOT / "var"
REPORTS_DIR = VAR_ROOT / "reports"
PDF_REPORTS_DIR = VAR_ROOT / "pdf_reports"
HTML_REPORTS_DIR = VAR_ROOT / "html_reports"
LOGS_DIR = VAR_ROOT / "logs"
TRIGGER_RESULTS_DIR = VAR_ROOT / "trigger_results"
TRADING_DIR = SRC_ROOT / "prism" / "trading"
TRADING_CONFIG_DIR = TRADING_DIR / "config"
