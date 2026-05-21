#!/usr/bin/env python3
"""
US-only portfolio reporter for Telegram.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

from trading import kis_auth as ka
from trading.stock_trading import USStockTrading
from telegram_bot_agent import TelegramBotAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
load_dotenv(dotenv_path=str(PROJECT_ROOT / ".env"))

CONFIG_FILE = SCRIPT_DIR / "config" / "kis_devlp.yaml"
with open(CONFIG_FILE, encoding="utf-8") as f:
    _cfg = yaml.safe_load(f)


class PortfolioTelegramReporter:
    def __init__(self, telegram_token: str = None, chat_id: str = None, trading_mode: str = None):
        self.telegram_token = telegram_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHANNEL_ID")
        if not self.telegram_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID are required.")
        self.trading_mode = trading_mode if trading_mode is not None else _cfg["default_mode"]
        self.telegram_bot = TelegramBotAgent(token=self.telegram_token)

    def _get_primary_account_config(self) -> Optional[Dict[str, Any]]:
        svr = "vps" if self.trading_mode == "demo" else "prod"
        try:
            return ka.resolve_account(svr=svr, product="01", market="us")
        except ValueError:
            return None

    @staticmethod
    def _fmt_usd(amount: float) -> str:
        return f"${amount:,.2f}" if amount else "$0.00"

    @staticmethod
    def _fmt_pct(rate: float) -> str:
        return f"{rate:+.2f}%" if rate else "0.00%"

    def create_portfolio_message(self, portfolio: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
        now = datetime.datetime.now().strftime("%m/%d %H:%M")
        mode_emoji = "🧪" if self.trading_mode == "demo" else "💰"
        mode_text = "모의투자" if self.trading_mode == "demo" else "실전투자"

        lines = [
            f"📊 US 포트폴리오 리포트 {mode_emoji}",
            f"🕐 {now} | {mode_text}",
            "",
            "🇺🇸 *미국주식 계좌*",
        ]

        if summary:
            total_eval = summary.get("total_eval_amount", 0)
            total_profit = summary.get("total_profit_amount", 0)
            total_profit_rate = summary.get("total_profit_rate", 0)
            usd_cash = summary.get("usd_cash", 0)
            lines.extend(
                [
                    f"📊 보유주식: `{self._fmt_usd(total_eval)}`",
                    f"📈 평가손익: `{self._fmt_usd(total_profit)}` ({self._fmt_pct(total_profit_rate)})",
                    f"💵 USD 현금: `{self._fmt_usd(usd_cash)}`",
                ]
            )
        else:
            lines.append("❌ 계좌 정보를 가져올 수 없습니다")

        lines.extend(["", "━━━━━━━━━━━━━━━━━━━━"])

        if not portfolio:
            lines.append("🇺🇸 *보유종목*: 없음")
            return "\n".join(lines)

        lines.append(f"🇺🇸 *보유종목* ({len(portfolio)}개)")
        for i, stock in enumerate(portfolio, 1):
            ticker = stock.get("ticker", "???")
            stock_name = stock.get("stock_name", "Unknown")
            quantity = stock.get("quantity", 0)
            profit_amount = stock.get("profit_amount", 0)
            profit_rate = stock.get("profit_rate", 0)
            eval_amount = stock.get("eval_amount", 0)
            avg_price = stock.get("avg_price", 0)
            exchange = stock.get("exchange", "")
            status_emoji = "⬆️" if profit_rate > 0 else ("⬇️" if profit_rate < 0 else "➖")
            exchange_tag = f"[{exchange}]" if exchange else ""

            lines.extend(
                [
                    "",
                    f"*{i}. {ticker}* {exchange_tag} {status_emoji}",
                    f"  {stock_name[:28]}{'...' if len(stock_name) > 28 else ''}",
                    f"  평가: `{self._fmt_usd(eval_amount)}`",
                    f"  단가: `{self._fmt_usd(avg_price)}` ({quantity}주)",
                    f"  손익: `{self._fmt_usd(profit_amount)}` | {self._fmt_pct(profit_rate)}",
                ]
            )

        return "\n".join(lines)

    async def get_trading_data(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        account = self._get_primary_account_config()
        if not account:
            logger.warning("US account not configured.")
            return [], {}
        try:
            trader = USStockTrading(
                mode=self.trading_mode,
                account_name=account["name"],
                product_code=account["product"],
            )
            portfolio = trader.get_portfolio() or []
            summary = trader.get_account_summary() or {}
            return portfolio, summary
        except Exception as exc:
            logger.error(f"Failed to fetch US portfolio: {exc}")
            return [], {}

    async def send_portfolio_report(self) -> bool:
        portfolio, summary = await self.get_trading_data()
        message = self.create_portfolio_message(portfolio, summary)
        return await self.telegram_bot.send_message(self.chat_id, message)


async def main():
    reporter = PortfolioTelegramReporter()
    success = await reporter.send_portfolio_report()
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
