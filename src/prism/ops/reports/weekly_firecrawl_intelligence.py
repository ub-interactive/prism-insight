#!/usr/bin/env python3
"""
Weekly Firecrawl Intelligence Report — AI-powered market research via Firecrawl Agent

Generates US market intelligence and prints the digest to stdout.

Usage:
    python weekly_firecrawl_intelligence.py                              # Generate and print
    python weekly_firecrawl_intelligence.py --dry-run                    # Same as default (documents intent)

Crontab example (optional):
# 0 11 * * 0 cd /root/prism-insight && /root/.pyenv/shims/python weekly_firecrawl_intelligence.py >> /root/prism-insight/logs/weekly_firecrawl_intelligence.log 2>&1
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

_repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_repo / "src"))

load_dotenv()
logger = logging.getLogger(__name__)

_DISCLAIMER = "\n\n⚠️ 본 내용은 투자 참고용이며, 투자 판단의 책임은 본인에게 있습니다."


async def _generate_us_report() -> str:
    """Generate US market intelligence report via Firecrawl search + Claude."""
    from prism.reporting.report_generator import generate_firecrawl_search_response

    today_str = datetime.now().strftime("%Y년 %m월 %d일")

    search_query = f"US stock market weekly recap S&P 500 NASDAQ {today_str}"
    analysis_prompt = (
        f"오늘 날짜는 {today_str}입니다.\n"
        "위 검색 결과를 바탕으로 이번 주 미국 주식시장 주간 인텔리전스 리포트를 작성해줘.\n\n"
        "포함 내용:\n"
        "1. 이번 주 S&P500/NASDAQ 주요 흐름 요약\n"
        "2. 가장 주목받은 섹터 3개와 대표 종목\n"
        "3. 연준(Fed) 관련 동향 및 금리 전망\n"
        "4. 다음 주 주요 일정 (FOMC, 실적 발표 등)\n"
        "5. 개인투자자를 위한 전략 제안\n\n"
        "한국어로, 모바일 요약 형태로 이모지 포함하여 작성. 4000자 이내."
    )

    result = await generate_firecrawl_search_response(search_query, analysis_prompt, limit=10)
    if not result:
        logger.error("Failed to generate US intelligence report")
        return ""
    return result


async def generate_weekly_intelligence() -> str:
    """Generate weekly US intelligence report."""
    today = datetime.now()
    date_display = today.strftime("%-m/%-d")

    us_report = await _generate_us_report()

    sections = [f"🔥 PRISM 주간 Firecrawl 인텔리전스 ({date_display})"]

    if us_report:
        sections.append(f"\n🇺🇸 미국시장 인텔리전스\n━━━━━━━━━━━━━━━━━━━━\n{us_report}")

    if not us_report:
        sections.append("\n⚠️ Firecrawl 리포트 생성에 실패했습니다. 로그를 확인해주세요.")

    sections.append(_DISCLAIMER)

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Weekly Firecrawl Intelligence Report")
    parser.add_argument("--dry-run", action="store_true",
                        help="Documents intent — weekly digest prints to stdout only")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    async def _run():
        message = await generate_weekly_intelligence()
        print(message)
        if args.dry_run:
            logger.info("Dry run requested — digest printed above.")

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error(f"Failed to generate intelligence report: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
