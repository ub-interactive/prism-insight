#!/usr/bin/env python3
"""
PRISM-INSIGHT Demo Script

Generate a single AI-powered stock analysis report (PDF).
No brokerage integration in this script—only the analysis and PDF export.

Usage:
    python -m prism.ops.shared.dev.demo                    # Analyze Apple (AAPL)
    python -m prism.ops.shared.dev.demo MSFT               # Analyze Microsoft
    python -m prism.ops.shared.dev.demo NVDA "NVIDIA Corp" # Analyze with custom company name
    python -m prism.ops.shared.dev.demo 600519 --market cn --language zh
"""
import asyncio
import argparse
import sys
import subprocess
import time
from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

_repo = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_repo / "src"))
from prism.paths import REPO_ROOT

project_root = REPO_ROOT
load_dotenv(project_root / ".env")

from prism.core import us, cn


def check_perplexity_configured() -> bool:
    """True when PERPLEXITY_API_KEY is set (.env or process environment)."""
    key = (os.getenv("PERPLEXITY_API_KEY") or "").strip()
    if not key or key.upper() == "YOUR_API_KEY":
        return False
    placeholders_lower = {"", "your-api-key", "example key"}
    return key.lower() not in placeholders_lower


def get_company_name(ticker: str) -> str:
    """Get company name from ticker using yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get("longName") or info.get("shortName") or ticker
    except Exception:
        return ticker


def get_cn_company_name(code: str) -> str:
    """Get company name from A-share code using akshare."""
    from prism.core.cn.data import DataClient

    return DataClient().get_company_name(code)


async def generate_report(
    ticker: str,
    company_name: str,
    language: str = "en",
    market: str = "us",
) -> tuple:
    """
    Generate a stock analysis report.

    Args:
        ticker: Stock ticker symbol (US) or 6-digit A-share code (CN)
        company_name: Company name
        language: Language code ("en", "zh", etc.)
        market: Market selector ("us" or "cn")

    Returns:
        tuple: (markdown_path, pdf_path)
    """
    include_news = check_perplexity_configured()

    print(f"\n{'='*60}")
    print("  PRISM-INSIGHT AI Stock Analysis")
    print(f"  Market: {market.upper()}")
    print(f"  Ticker: {ticker}")
    print(f"  Company: {company_name}")
    language_labels = {
        "en": "English",
        "zh": "Chinese",
        "ko": "Korean",
        "ja": "Japanese",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
    }
    print(f"  Language: {language_labels.get(language.lower(), language.upper())}")
    if not include_news:
        print("  Note: News analysis skipped (Perplexity API not configured)")
    print(f"{'='*60}\n")

    print("[1/3] Generating AI analysis report...")
    print("      This may take 3-5 minutes. AI agents are analyzing:")
    print("      - Price & volume trends")
    print("      - Institutional holdings")
    print("      - Financial fundamentals")
    if include_news:
        print("      - Recent news & sentiment")
    print("      - Market conditions")
    print("      - Investment strategy\n")

    start_time = time.time()

    if market == "cn":
        from prism.core.cn import market as cn_market
        from prism.core.cn import market_calendar
        from prism.reporting.report_generator import save_cn_pdf_report, save_cn_report

        ticker_info = cn_market.ticker.normalize(ticker)
        reference_date = market_calendar.get_reference_date()
        report_content = await cn.analysis.analyze_stock(
            code=ticker_info.code,
            company_name=company_name,
            exchange=ticker_info.exchange,
            reference_date=reference_date,
            language=language,
            include_news=include_news,
        )
        md_path = save_cn_report(ticker_info.code, company_name, report_content)
        pdf_path = save_cn_pdf_report(ticker_info.code, company_name, md_path)
    else:
        from prism.reporting.report_generator import save_us_pdf_report, save_us_report

        reference_date = datetime.now().strftime("%Y%m%d")
        report_content = await us.analysis.analyze_stock(
            ticker=ticker,
            company_name=company_name,
            reference_date=reference_date,
            language=language,
            include_news=include_news,
        )
        md_path = save_us_report(ticker, company_name, report_content)
        pdf_path = save_us_pdf_report(ticker, company_name, md_path)

    analysis_time = time.time() - start_time
    print(f"\n[2/3] Analysis complete! ({analysis_time:.1f} seconds)")
    print(f"      Report length: {len(report_content):,} characters")

    print("[3/3] Report files saved.")

    return md_path, pdf_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered stock analysis report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m prism.ops.shared.dev.demo                      # Analyze Apple (AAPL)
  python -m prism.ops.shared.dev.demo MSFT                 # Analyze Microsoft
  python -m prism.ops.shared.dev.demo NVDA "NVIDIA Corp"   # Analyze with custom name
  python -m prism.ops.shared.dev.demo AAPL --language en   # English report
  python -m prism.ops.shared.dev.demo 600519 --market cn --language zh
  python -m prism.ops.shared.dev.demo 000001 --market cn --language en
        """,
    )
    parser.add_argument(
        "ticker",
        nargs="?",
        default="AAPL",
        help="US ticker symbol or CN 6-digit A-share code (default: AAPL)",
    )
    parser.add_argument(
        "company_name",
        nargs="?",
        default=None,
        help="Company name (auto-detected if not provided)",
    )
    parser.add_argument(
        "--market",
        "-m",
        choices=["us", "cn"],
        default="us",
        help="Market: us (default) or cn (A-shares)",
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default="en",
        help="Report language (e.g. en, zh, ko, ja, es, fr, de) (default: en)",
    )

    args = parser.parse_args()

    if args.market == "cn":
        from prism.core.cn.market.ticker import CNTickerError, normalize

        try:
            ticker_info = normalize(args.ticker)
        except CNTickerError as exc:
            print(f"Error: {exc}")
            sys.exit(1)

        ticker = ticker_info.code
        if args.company_name:
            company_name = args.company_name
        else:
            print(f"Looking up company name for {ticker}...")
            company_name = get_cn_company_name(ticker)
            print(f"Found: {company_name}")
    else:
        ticker = args.ticker.upper()
        if args.company_name:
            company_name = args.company_name
        else:
            print(f"Looking up company name for {ticker}...")
            company_name = get_company_name(ticker)
            print(f"Found: {company_name}")

    try:
        md_path, pdf_path = asyncio.run(
            generate_report(ticker, company_name, args.language, args.market)
        )

        print(f"\n{'='*60}")
        print("  Report Generated Successfully!")
        print(f"{'='*60}")
        print(f"\n  Markdown: {md_path}")
        print(f"  PDF:      {pdf_path}")
        print("\n  Open the PDF to view your AI-generated analysis report.")
        print(f"\n{'='*60}")

        if sys.platform == "darwin":
            print("\nOpening PDF...")
            subprocess.run(["open", str(pdf_path)], check=False)

    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
