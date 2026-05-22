#!/usr/bin/env python3
"""
Weekly Insight Report — Trading Summary, Sell Evaluation, Trigger Performance, AI Intuitions

Outputs the compiled digest to stdout. Use ``--dry-run`` explicitly when you want
to skip optional side effects wired by other tooling.

Usage:
    python weekly_insight_report.py
    python weekly_insight_report.py --dry-run                     # Explicit no-op labeling
"""
import argparse
import asyncio
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

_repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_repo))

from dotenv import load_dotenv
from trading import kis_auth as ka

from repo_paths import REPO_ROOT

load_dotenv()
logger = logging.getLogger(__name__)
DB_PATH = str(REPO_ROOT / "stock_tracking_db.sqlite")


def _safe_query(cursor, query: str, params=(), default=(0, 0)):
    """Execute query with error handling, return default on failure."""
    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result if result else default
    except sqlite3.Error as e:
        logger.warning(f"Query failed: {e}")
        return default


def _safe_query_all(cursor, query: str, params=()) -> list:
    """Execute query and return all results, empty list on failure."""
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logger.warning(f"Query failed: {e}")
        return []


def _format_percentage(value: float) -> str:
    """Format percentage with sign."""
    if value is None:
        return "N/A"
    return f"{value:+.1f}%"


def _sell_verdict(change_pct: float) -> str:
    """Determine sell evaluation verdict based on price change after selling."""
    if change_pct < -1:
        return "✅ 잘 팔았습니다"
    elif change_pct > 3:
        return "😅 더 기다릴 수 있었습니다"
    else:
        return "👌 적절한 매도"


def _get_primary_account_key(market: str) -> str | None:
    default_mode = str(ka.getEnv().get("default_mode", "demo")).strip().lower()
    svr = "vps" if default_mode == "demo" else "prod"
    try:
        return ka.resolve_account(svr=svr, market=market)["account_key"]
    except Exception as exc:
        logger.warning(f"Primary {market} account resolution failed: {exc}")
        return None


def _get_weekly_trades(cursor, week_start_str: str) -> str:
    """Get weekly trade summary for the US portfolio."""
    us_account_key = _get_primary_account_key("us")
    if not us_account_key:
        return "계좌 키 조회 실패 — kis_devlp.yaml 확인"

    us_sells = _safe_query_all(cursor, """
        SELECT ticker, company_name, buy_price, sell_price, profit_rate, holding_days
        FROM trading_history WHERE sell_date >= ? AND account_key = ? ORDER BY sell_date DESC
    """, (week_start_str, us_account_key))
    us_buys = _safe_query_all(cursor, """
        SELECT ticker, company_name, buy_price, buy_date, current_price
        FROM stock_holdings WHERE buy_date >= ? AND account_key = ?
    """, (week_start_str, us_account_key))

    if not (us_sells or us_buys):
        return "이번 주 매매 없음"

    lines = ["🇺🇸 미국시장"]
    for ticker, name, buy_price, _date, current_price in us_buys:
        if current_price and buy_price:
            pnl = (current_price - buy_price) / buy_price * 100
            lines.append(f"  매수: {ticker} ${buy_price:,.2f} → 현재 ${current_price:,.2f} ({pnl:+.1f}%)")
        else:
            lines.append(f"  매수: {ticker} ${buy_price:,.2f}")
    for ticker, name, _buy_p, sell_p, profit, days in us_sells:
        lines.append(f"  매도: {ticker} ${sell_p:,.2f} → {profit:+.1f}% ({days}일 보유)")

    return "\n".join(lines)


def _get_sell_evaluation(cursor, week_start_str: str) -> str | None:
    """Evaluate US sells by comparing sell price to current price.

    Returns None if no sells this week (section should be omitted).
    """
    us_account_key = _get_primary_account_key("us")
    if not us_account_key:
        return None

    us_sells = _safe_query_all(cursor, """
        SELECT ticker, company_name, sell_price
        FROM trading_history WHERE sell_date >= ? AND account_key = ?
    """, (week_start_str, us_account_key))

    if not us_sells:
        return None

    lines: list[str] = []

    try:
        import yfinance as yf
        tickers_list = [row[0] for row in us_sells]
        data = yf.download(tickers_list, period="1d", progress=False)

        for ticker, name, sell_price in us_sells:
            try:
                if not sell_price:
                    continue
                if len(tickers_list) == 1:
                    current_price = float(data['Close'].iloc[-1])
                else:
                    current_price = float(data['Close'][ticker].iloc[-1])
                change_pct = (current_price - sell_price) / sell_price * 100
                verdict = _sell_verdict(change_pct)
                lines.append(
                    f"  {ticker}: 매도가 ${sell_price:,.2f} → "
                    f"현재가 ${current_price:,.2f} ({change_pct:+.1f}%) {verdict}"
                )
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"US price lookup failed: {e}")

    return "\n".join(lines) if lines else None


def _get_ai_intuitions(cursor, week_start_str: str) -> str:
    """Get AI long-term learning intuitions section (US market)."""
    new_count = _safe_query(cursor, f"""
        SELECT COUNT(*) FROM trading_intuitions
        WHERE is_active=1 AND created_at >= '{week_start_str}'
    """, default=(0,))[0] or 0

    rows = _safe_query_all(cursor, """
        SELECT condition, insight, confidence
        FROM trading_intuitions WHERE is_active=1 AND (market IS NULL OR market != 'KR')
        ORDER BY confidence DESC LIMIT 5
    """)

    stats = _safe_query(cursor, """
        SELECT COUNT(*), AVG(confidence), AVG(success_rate)
        FROM trading_intuitions WHERE is_active=1
    """, default=(0, 0, 0))
    total_count = stats[0] or 0
    avg_conf = stats[1] or 0

    if total_count == 0:
        return "아직 데이터 축적 중입니다. 매매 기록이 쌓이면 AI가 패턴을 학습합니다."

    new_count_str = f"{new_count}개" if new_count > 0 else "없음"
    avg_conf_str = f"{avg_conf * 100:.0f}%" if avg_conf else "집계 중"
    lines = [
        f"이번 주 신규: {new_count_str} | 누적 활성 직관: {total_count}개 | 평균 신뢰도: {avg_conf_str}"
    ]

    if rows:
        lines.append("")
        lines.append("💡 주요 직관:")
        for i, (condition, insight, confidence) in enumerate(rows[:5], 1):
            conf_pct = (confidence or 0) * 100
            lines.append(f"  {i}. {condition} = {insight} (신뢰도 {conf_pct:.0f}%)")

    return "\n".join(lines)


async def generate_weekly_report(db_path: str = DB_PATH) -> str:
    """Generate weekly insight report message."""
    today = datetime.now()
    week_start = today - timedelta(days=7)
    week_start_str = week_start.strftime("%Y-%m-%d %H:%M:%S")

    start_display = week_start.strftime("%-m/%-d")
    end_display = today.strftime("%-m/%-d")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    trades_summary = _get_weekly_trades(cursor, week_start_str)
    sell_eval = _get_sell_evaluation(cursor, week_start_str)
    intuitions_section = _get_ai_intuitions(cursor, week_start_str)

    avoided_count, avoided_avg = 0, None
    missed_count, missed_best = 0, None
    best_trigger_name, best_trigger_rate = "데이터 없음", 0
    new_principles, total_principles = 0, 0

    try:
        query = """
            SELECT COUNT(*), AVG(return_30d * 100)
            FROM analysis_performance_tracker
            WHERE return_30d IS NOT NULL
              AND COALESCE(was_traded, 0) = 0
              AND return_30d < -0.05
        """
        count, avg = _safe_query(cursor, query)
        avoided_count = count or 0
        avoided_avg = avg

        query = """
            SELECT COUNT(*), MAX(return_30d * 100)
            FROM analysis_performance_tracker
            WHERE return_30d IS NOT NULL
              AND COALESCE(was_traded, 0) = 0
              AND return_30d > 0.10
        """
        count, max_return = _safe_query(cursor, query)
        missed_count = count or 0
        missed_best = max_return

        query = """
            SELECT
                trigger_type,
                SUM(CASE WHEN return_30d IS NOT NULL THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN return_30d > 0 THEN 1 ELSE 0 END) as wins
            FROM analysis_performance_tracker
            WHERE trigger_type IS NOT NULL
            GROUP BY trigger_type
            HAVING completed >= 3
            ORDER BY (wins * 1.0 / completed) DESC
            LIMIT 1
        """
        result = _safe_query(cursor, query, default=(None, 0, 0))
        if result[0]:
            best_trigger_name = result[0]
            completed, wins = result[1], result[2]
            best_trigger_rate = (wins / completed * 100) if completed > 0 else 0

        query = f"""
            SELECT COUNT(*)
            FROM trading_principles
            WHERE is_active=1 AND created_at >= '{week_start_str}'
        """
        new_principles = _safe_query(cursor, query, default=(0,))[0] or 0

        query = "SELECT COUNT(*) FROM trading_principles WHERE is_active=1"
        total_principles = _safe_query(cursor, query, default=(0,))[0] or 0

    except sqlite3.Error as e:
        logger.warning(f"Trigger performance query error: {e}")
    finally:
        conn.close()

    def _avoided_detail(count, avg):
        if count == 0:
            return "0건 — AI가 매수를 건너뛴 종목 중 하락한 종목 없음"
        return f"{count}건 (평균 {_format_percentage(avg)}) — 매수하지 않아 손실을 피한 종목"

    def _missed_detail(count, best):
        if count == 0:
            return "0건 — 놓친 상승 종목 없음"
        return f"{count}건 (최고 {_format_percentage(best)}) — 매수하지 않았으나 크게 오른 종목"

    if best_trigger_rate > 0:
        summary = f"'{best_trigger_name}' 트리거가 승률 {best_trigger_rate:.0f}%로 가장 안정적"
    else:
        summary = "데이터 축적 중 — 30일 추적 완료 후 인사이트 제공 예정"

    avoided_str = _avoided_detail(avoided_count, avoided_avg)
    missed_str = _missed_detail(missed_count, missed_best)
    trigger_str = (
        f"{best_trigger_name} (승률 {best_trigger_rate:.0f}%)"
        if best_trigger_rate > 0
        else "데이터 축적 중"
    )
    principles_str = f"{new_principles}개 추가 (총 {total_principles}개)"

    insights: list[str] = []
    if best_trigger_rate >= 60:
        insights.append("승률 60%+ 트리거가 있습니다. 해당 트리거 종목을 우선 검토하세요.")
    if missed_count >= 3:
        insights.append("놓친 기회가 3건 이상입니다. 매수 기준을 약간 완화하는 것을 고려해보세요.")
    if avoided_count >= 5:
        insights.append("회피한 손실이 5건 이상입니다. AI의 관망 판단이 잘 작동하고 있습니다.")
    if not insights:
        insights.append("이번 주는 큰 변동 없이 안정적으로 운영되었습니다.")

    insights_str = "\n".join(f"  → {i}" for i in insights)

    sell_eval_block = ""
    if sell_eval:
        sell_eval_block = f"""
🔍 매도 후 평가
━━━━━━━━━━━━━━━━━━━━
{sell_eval}
"""

    return f"""📋 PRISM 주간 인사이트 ({start_display} ~ {end_display})
이번 주 AI 매매 판단의 성과를 돌아봅니다.

📈 이번 주 매매 요약
━━━━━━━━━━━━━━━━━━━━
{trades_summary}
{sell_eval_block}
🇺🇸 미국시장 (트리거 성과)
━━━━━━━━━━━━━━━━━━━━
🛡️ 회피한 손실: {avoided_str}
❌ 놓친 기회: {missed_str}
📊 가장 정확한 트리거: {trigger_str}
📌 새 매매 원칙: {principles_str}

🧠 AI 장기 학습 인사이트
━━━━━━━━━━━━━━━━━━━━
{intuitions_section}

📌 이번 주 인사이트
{insights_str}

💡 핵심: {summary}

ℹ️ 용어 안내
• 트리거 = AI가 종목을 발견한 이유 (급등, 거래량 급증 등)
• 회피한 손실 = 매수하지 않았는데 30일 뒤 -5% 이상 하락한 종목
• 놓친 기회 = 매수하지 않았는데 30일 뒤 +10% 이상 상승한 종목
• 승률 = 해당 트리거로 분석한 종목 중 30일 후 수익이 난 비율
• 매매 원칙 = AI가 과거 매매 경험에서 스스로 학습한 규칙
• 직관 = AI가 반복 패턴에서 추출한 매매 원칙"""


def main():
    parser = argparse.ArgumentParser(description="Weekly Insight Report")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print digest only (default behavior; flag documents intent)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    async def _run():
        message = await generate_weekly_report()
        print(message)
        if args.dry_run:
            logger.info("Dry run requested — digest printed above.")

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
