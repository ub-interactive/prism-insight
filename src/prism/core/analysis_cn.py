"""
CN A-share Stock Analysis Module

Generate comprehensive stock analysis reports for Chinese A-shares.
Uses akshare-backed data prefetch and CN-specific agents.
"""
import asyncio
import re
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from mcp_agent.app import MCPApp

from prism.paths import MCP_CONFIG_PATH
from prism.core.agents.cn_directory import get_cn_agent_directory
from prism.core.data.cn_client import CNDataClient
from prism.core.data.cn_prefetch import prefetch_cn_analysis_data
from prism.core.market.cn_ticker import normalize
from prism.core.market_calendar_cn import get_cn_reference_date
from prism.core.shared.report_generation import (
    generate_investment_strategy,
    generate_market_report,
    generate_report,
    generate_summary,
    get_disclaimer,
)
from prism.core.shared.footnotes import annotate_financial_terms
from prism.core.shared.utils import clean_markdown
from prism.core.visualization.cn_chart import (
    get_cn_holder_chart_html,
    get_cn_price_chart_html,
    get_cn_technical_chart_html,
)

# Market analysis cache storage (global variable)
_cn_market_analysis_cache = {}


async def analyze_cn_stock(
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
        reference_date = get_cn_reference_date()

    async with app.run() as parallel_app:
        logger = parallel_app.logger
        logger.info(
            f"Starting: {company_name}({display_code}) CN analysis - reference date: {reference_date}"
        )

        section_reports = {}

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
            section_reports["news_analysis"] = (
                "_News analysis requires Perplexity API key. "
                "Technical and fundamental analysis are provided normally._"
            )
            logger.info("Skipping news_analysis (Perplexity API not configured)")
        base_sections = akshare_sections + ["news_analysis"]

        try:
            prefetched = prefetch_cn_analysis_data(code, reference_date)
            logger.info(
                f"Prefetched CN data for {display_code}: "
                f"{list(prefetched.keys()) if prefetched else 'none'}"
            )
        except Exception as e:
            logger.error(f"CN data prefetch failed for {display_code}: {e}")
            raise

        agents = get_cn_agent_directory(
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

        async def process_akshare_sections():
            """Process akshare-dependent sections sequentially."""
            results = {}
            for section in akshare_sections:
                if section in agents:
                    logger.info(f"Processing {section} for {company_name}...")
                    try:
                        agent = agents[section]
                        if section == "market_index_analysis":
                            if "report" in _cn_market_analysis_cache:
                                logger.info("Using cached CN market analysis")
                                report = _cn_market_analysis_cache["report"]
                            else:
                                logger.info("Generating new CN market analysis")
                                report = await generate_market_report(
                                    agent, section, reference_date, logger, language
                                )
                                _cn_market_analysis_cache["report"] = report
                        else:
                            report = await generate_report(
                                agent,
                                section,
                                company_name,
                                display_code,
                                reference_date,
                                logger,
                                language,
                            )
                        results[section] = report
                        await asyncio.sleep(3)
                    except Exception as e:
                        logger.error(f"Error processing {section}: {e}")
                        results[section] = f"Analysis failed: {section}"
            return results

        async def process_parallel_section(section):
            """Process a non-akshare section with its own MCPApp context."""
            if section not in agents:
                return section, None

            section_app = MCPApp(
                name=f"cn_stock_analysis_{section}",
                settings=str(MCP_CONFIG_PATH),
            )
            async with section_app.run() as section_context:
                section_logger = section_context.logger
                section_logger.info(f"Processing {section} for {company_name}...")
                try:
                    agent = agents[section]
                    report = await generate_report(
                        agent,
                        section,
                        company_name,
                        display_code,
                        reference_date,
                        section_logger,
                        language,
                    )
                    return section, report
                except Exception as e:
                    section_logger.error(f"Error processing {section}: {e}")
                    return section, f"Analysis failed: {section}"

        parallel_tasks = [process_parallel_section(s) for s in parallel_sections]
        akshare_task = process_akshare_sections()

        all_results = await asyncio.gather(akshare_task, *parallel_tasks)

        akshare_results = all_results[0]
        section_reports.update(akshare_results)

        for result in all_results[1:]:
            if result and result[1] is not None:
                section_reports[result[0]] = result[1]

        combined_reports = ""
        for section in base_sections:
            if section in section_reports:
                combined_reports += f"\n\n--- {section.upper()} ---\n\n"
                combined_reports += section_reports[section]

        try:
            logger.info(f"Processing investment_strategy for {company_name}...")
            investment_strategy = await generate_investment_strategy(
                section_reports,
                combined_reports,
                company_name,
                display_code,
                reference_date,
                logger,
                language,
            )
            section_reports["investment_strategy"] = investment_strategy.lstrip("\n")
            logger.info(
                f"Completed investment_strategy - {len(investment_strategy)} characters"
            )
        except Exception as e:
            logger.error(f"Error processing investment_strategy: {e}")
            section_reports["investment_strategy"] = "Investment strategy analysis failed"

        try:
            logger.info(f"Processing summary for {company_name}...")
            summary = await generate_summary(
                section_reports,
                company_name,
                display_code,
                reference_date,
                logger,
                language,
            )
            summary = summary.lstrip("\n")
            summary = re.sub(
                r"^#\s*"
                + re.escape(company_name)
                + r"\s*\("
                + re.escape(display_code)
                + r"\)[^\n]*\n+",
                "",
                summary,
                flags=re.IGNORECASE,
            )
            summary = re.sub(
                r"^\*{0,2}Publication Date\*{0,2}\s*:\s*[^\n]+\n+",
                "",
                summary,
                flags=re.IGNORECASE,
            )
            summary = re.sub(r"^-{3,}\s*\n+", "", summary)
            section_reports["summary"] = summary.lstrip("\n")
            logger.info(f"Completed summary - {len(summary)} characters")
        except Exception as e:
            logger.error(f"Error processing summary: {e}")
            section_reports["summary"] = "Summary generation failed"

        price_chart_html = ""
        holder_chart_html = ""
        technical_chart_html = ""

        try:
            ref_dt = datetime.strptime(reference_date, "%Y%m%d")
            end_date = reference_date
            start_date = (ref_dt - timedelta(days=365)).strftime("%Y%m%d")

            client = CNDataClient()
            hist = client.get_ohlcv(code, start_date, end_date)

            if hist is not None and not hist.empty:
                price_chart_html = get_cn_price_chart_html(
                    code, company_name, hist, width=900, dpi=80
                )
                if price_chart_html:
                    logger.info(f"Generated price chart for {display_code}")
                else:
                    logger.warning(f"Failed to generate price chart for {display_code}")

                technical_chart_html = get_cn_technical_chart_html(
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
            holder_chart_html = get_cn_holder_chart_html(
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

        final_report = clean_markdown(final_report)
        final_report = await annotate_financial_terms(final_report, language, logger)

        if language and language.lower() != "en":
            from prism.core.shared.translation import translate_report

            final_report = await translate_report(final_report, language)

        logger.info(
            f"Final report generated: {company_name}({display_code}) - "
            f"{len(final_report)} characters"
        )

        return final_report


def clear_cn_market_cache():
    """Clear the CN market analysis cache."""
    global _cn_market_analysis_cache
    _cn_market_analysis_cache = {}
