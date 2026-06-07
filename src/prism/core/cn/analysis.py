"""
CN A-share Stock Analysis Module

Generate comprehensive stock analysis reports for Chinese A-shares.
Uses akshare-backed data prefetch and CN-specific agents.
"""
import asyncio
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from mcp_agent.app import MCPApp

from prism.paths import MCP_CONFIG_PATH
from prism.core.cn.agents.directory import get_agent_directory
from prism.core.cn.data.client import DataClient
from prism.core.cn.data.prefetch import prefetch_analysis_data
from prism.core.cn.market.ticker import normalize
from prism.core.cn.market_calendar import get_reference_date
from prism.core.shared import analysis_helpers as shared
from prism.core.shared.report_generation import get_disclaimer
from prism.core.cn.visualization.chart import (
    get_holder_chart_html,
    get_price_chart_html,
    get_technical_chart_html,
)

# Market analysis cache storage (global variable)
_market_analysis_cache = {}


async def analyze_stock(
    code: str,
    company_name: str,
    exchange: str,
    reference_date: str | None = None,
    language: str = "en",
    include_news: bool = True,
) -> str:
    """
    Generate comprehensive stock analysis report for a CN A-share.

    Args:
        code: 6-digit A-share code (e.g. "600519", "000001")
        company_name: Company name (e.g. "Kweichow Moutai")
        exchange: Exchange label ("SH" or "SZ"); normalized exchange is preferred
        reference_date: Analysis reference date (YYYYMMDD format)
        language: Legacy language code forwarded across synthesis helpers.
        include_news: Whether to include news analysis (requires Perplexity API)

    Returns:
        str: Generated final report markdown text
    """
    app = MCPApp(name="cn_stock_analysis", settings=str(MCP_CONFIG_PATH))

    ticker = normalize(code)
    code = ticker.code
    exchange = ticker.exchange
    display_code = f"{ticker.code}.{ticker.exchange}"

    if reference_date is None:
        reference_date = get_reference_date()

    async with app.run() as parallel_app:
        logger = parallel_app.logger
        logger.info(
            f"Starting: {company_name}({display_code}) CN analysis - reference date: {reference_date}"
        )

        akshare_sections = [
            "price_volume_analysis",
            "institutional_holdings_analysis",
            "company_status",
            "company_overview",
            "market_index_analysis",
        ]
        parallel_sections = []
        if include_news:
            parallel_sections.append("news_analysis")
        else:
            logger.info("Skipping news_analysis (Perplexity API not configured)")
        base_sections = akshare_sections + ["news_analysis"]

        try:
            prefetched = prefetch_analysis_data(code, reference_date)
            logger.info(
                f"Prefetched CN data for {display_code}: "
                f"{list(prefetched.keys()) if prefetched else 'none'}"
            )
        except Exception as e:
            logger.error(f"CN data prefetch failed for {display_code}: {e}")
            raise

        agents = get_agent_directory(
            company_name,
            code,
            exchange,
            reference_date,
            base_sections,
            language,
            prefetched_data=prefetched,
        )

        logger.info(f"Running CN analysis in HYBRID mode for {company_name}...")
        logger.info(f"  - akshare sections (sequential): {akshare_sections}")
        logger.info(f"  - parallel sections: {parallel_sections}")

        section_reports = await shared.collect_hybrid_sections(
            logger,
            agents=agents,
            sequential=akshare_sections,
            parallel=parallel_sections,
            company_name=company_name,
            display_symbol=display_code,
            reference_date=reference_date,
            language=language,
            market_cache=_market_analysis_cache,
            app_prefix="cn_stock_analysis",
            base_sections=base_sections,
        )
        if not include_news:
            section_reports["news_analysis"] = (
                "_News analysis requires Perplexity API key. "
                "Technical and fundamental analysis are provided normally._"
            )

        section_reports = await shared.add_strategy_and_summary(
            logger,
            section_reports,
            company_name=company_name,
            display_symbol=display_code,
            reference_date=reference_date,
            language=language,
            base_sections=base_sections,
        )

        price_chart_html = ""
        holder_chart_html = ""
        technical_chart_html = ""

        try:
            ref_dt = datetime.strptime(reference_date, "%Y%m%d")
            end_date = reference_date
            start_date = (ref_dt - timedelta(days=365)).strftime("%Y%m%d")

            client = DataClient()
            hist = client.get_ohlcv(code, start_date, end_date)

            if hist is not None and not hist.empty:
                price_chart_html = get_price_chart_html(
                    code, company_name, hist, width=900, dpi=80
                )
                if price_chart_html:
                    logger.info(f"Generated price chart for {display_code}")
                else:
                    logger.warning(f"Failed to generate price chart for {display_code}")

                technical_chart_html = get_technical_chart_html(
                    code, company_name, hist, width=900, dpi=80
                )
                if technical_chart_html:
                    logger.info(
                        f"Generated technical indicators chart for {display_code}"
                    )
                else:
                    logger.warning(
                        f"Failed to generate technical indicators chart for {display_code}"
                    )
            else:
                logger.warning(f"No OHLCV data for charts: {display_code}")

            holders = client.get_top_holders(code)
            holder_chart_html = get_holder_chart_html(
                code, company_name, holders, width=900, dpi=80
            )
            if holder_chart_html:
                logger.info(f"Generated holder chart for {display_code}")
            else:
                logger.warning(f"Failed to generate holder chart for {display_code}")

        except Exception as e:
            logger.warning(f"Chart generation skipped: {e}")

        formatted_date = f"{reference_date[:4]}.{reference_date[4:6]}.{reference_date[6:]}"

        price_chart_section = ""
        if price_chart_html:
            price_chart_section = f"\n\n#### Price Chart\n\n{price_chart_html}\n"

        holder_chart_section = ""
        if holder_chart_html:
            holder_chart_section = f"\n\n#### Major Holder Chart\n\n{holder_chart_html}\n"

        technical_chart_section = ""
        if technical_chart_html:
            technical_chart_section = (
                f"\n\n#### Technical Indicators (RSI & MACD)\n\n{technical_chart_html}\n"
            )

        final_report = f"""# {company_name} ({display_code}) Analysis Report

**Publication Date:** {formatted_date}

---

{section_reports.get("summary", "## Executive Summary - Summary not available")}

---

## 1. Technical Analysis

{section_reports.get("price_volume_analysis", "Analysis not available")}
{price_chart_section}
{section_reports.get("institutional_holdings_analysis", "Analysis not available")}
{holder_chart_section}
---

## 2. Fundamental Analysis

{section_reports.get("company_status", "Analysis not available")}

{section_reports.get("company_overview", "Analysis not available")}

---

## 3. Recent Major News Summary

{section_reports.get("news_analysis", "Analysis not available")}

---

## 4. Market Analysis

{section_reports.get("market_index_analysis", "Analysis not available")}
{technical_chart_section}
---

## 5. Investment Strategy and Opinion

{section_reports.get("investment_strategy", "Strategy not available")}

---

{get_disclaimer(language)}
"""

        final_report = await shared.finalize_markdown(
            logger, final_report, language=language, market="cn"
        )

        logger.info(
            f"Final report generated: {company_name}({display_code}) - "
            f"{len(final_report)} characters"
        )

        return final_report


def clear_market_cache():
    """Clear the CN market analysis cache."""
    global _market_analysis_cache
    _market_analysis_cache = {}
