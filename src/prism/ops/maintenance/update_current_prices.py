#!/usr/bin/env python3
"""
Weekly cron script: update long-term price history for all archived tickers.

Crontab (run Monday 04:00 KST — after auto_insight at 03:00):
    0 4 * * 1 cd /root/prism-insight && python update_current_prices.py >> logs/price_update.log 2>&1

Options:
    --ticker TICKER      Update only this ticker
    --market us          Update only US market (default: us)
    --dry-run            Show what would be updated, no DB writes
    --concurrency N      Parallel fetch limit (default 2 for prod server)
"""

import argparse
import logging
import sys
from pathlib import Path

_repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_repo / "src"))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update PRISM archive price history")
    parser.add_argument("--ticker", default=None, help="Update only this ticker")
    parser.add_argument("--market", choices=["us"], default="us",
                        help="Update only US market")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be updated without writing to DB")
    parser.add_argument("--concurrency", type=int, default=2,
                        help="Parallel fetch limit (default 2 for 1-core server)")
    args = parser.parse_args()

    logger.info(
        "Archive price updater is disabled in US-only runtime. "
        "No action taken."
    )


if __name__ == "__main__":
    main()
