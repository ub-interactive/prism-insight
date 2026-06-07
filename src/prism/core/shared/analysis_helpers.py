"""Shared orchestration helpers for US and CN stock analysis pipelines."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from mcp_agent.app import MCPApp

from prism.core.shared.footnotes import annotate_financial_terms
from prism.core.shared.report_generation import (
    generate_investment_strategy,
    generate_market_report,
    generate_report,
    generate_summary,
)
from prism.core.shared.utils import clean_markdown
from prism.paths import MCP_CONFIG_PATH

SEQUENTIAL_DATA_SECTIONS = [
    "price_volume_analysis",
    "institutional_holdings_analysis",
    "company_status",
    "company_overview",
    "market_index_analysis",
]


def clean_summary_text(summary: str, *, company_name: str, display_symbol: str) -> str:
    """Remove duplicate title/date lines the summary agent may emit."""
    summary = summary.lstrip("\n")
    summary = re.sub(
        r"^#\s*" + re.escape(company_name) + r"\s*\(" + re.escape(display_symbol) + r"\)[^\n]*\n+",
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
    return summary.lstrip("\n")


async def collect_hybrid_sections(
    logger: Any,
    *,
    agents: dict,
    sequential: list[str],
    parallel: list[str],
    company_name: str,
    display_symbol: str,
    reference_date: str,
    language: str,
    market_cache: dict,
    app_prefix: str,
    base_sections: list[str],
) -> dict[str, str]:
    """Run sequential data sections and parallel news sections; return section_reports."""
    section_reports: dict[str, str] = {}

    async def process_sequential_sections() -> dict[str, str]:
        results: dict[str, str] = {}
        for section in sequential:
            if section not in agents:
                continue
            logger.info(f"Processing {section} for {company_name}...")
            try:
                agent = agents[section]
                if section == "market_index_analysis":
                    if "report" in market_cache:
                        logger.info("Using cached market analysis")
                        report = market_cache["report"]
                    else:
                        logger.info("Generating new market analysis")
                        report = await generate_market_report(
                            agent, section, reference_date, logger, language
                        )
                        market_cache["report"] = report
                else:
                    report = await generate_report(
                        agent,
                        section,
                        company_name,
                        display_symbol,
                        reference_date,
                        logger,
                        language,
                    )
                results[section] = report
                await asyncio.sleep(3)
            except Exception as exc:
                logger.error(f"Error processing {section}: {exc}")
                results[section] = f"Analysis failed: {section}"
        return results

    async def process_parallel_section(section: str):
        if section not in agents:
            return section, None
        section_app = MCPApp(name=f"{app_prefix}_{section}", settings=str(MCP_CONFIG_PATH))
        async with section_app.run() as section_context:
            section_logger = section_context.logger
            section_logger.info(f"Processing {section} for {company_name}...")
            try:
                agent = agents[section]
                report = await generate_report(
                    agent,
                    section,
                    company_name,
                    display_symbol,
                    reference_date,
                    section_logger,
                    language,
                )
                return section, report
            except Exception as exc:
                section_logger.error(f"Error processing {section}: {exc}")
                return section, f"Analysis failed: {section}"

    parallel_tasks = [process_parallel_section(s) for s in parallel]
    sequential_task = process_sequential_sections()
    all_results = await asyncio.gather(sequential_task, *parallel_tasks)

    section_reports.update(all_results[0])
    for result in all_results[1:]:
        if result and result[1] is not None:
            section_reports[result[0]] = result[1]

    return section_reports


async def add_strategy_and_summary(
    logger: Any,
    section_reports: dict[str, str],
    *,
    company_name: str,
    display_symbol: str,
    reference_date: str,
    language: str,
    base_sections: list[str] | None = None,
) -> dict[str, str]:
    """Add investment_strategy and summary to section_reports."""
    sections = list(base_sections or SEQUENTIAL_DATA_SECTIONS)
    if "news_analysis" not in sections:
        sections = sections + ["news_analysis"]

    combined_reports = ""
    for section in sections:
        if section in section_reports:
            combined_reports += f"\n\n--- {section.upper()} ---\n\n"
            combined_reports += section_reports[section]

    try:
        logger.info(f"Processing investment_strategy for {company_name}...")
        investment_strategy = await generate_investment_strategy(
            section_reports,
            combined_reports,
            company_name,
            display_symbol,
            reference_date,
            logger,
            language,
        )
        section_reports["investment_strategy"] = investment_strategy.lstrip("\n")
    except Exception as exc:
        logger.error(f"Error processing investment_strategy: {exc}")
        section_reports["investment_strategy"] = "Investment strategy analysis failed"

    try:
        logger.info(f"Processing summary for {company_name}...")
        summary = await generate_summary(
            section_reports,
            company_name,
            display_symbol,
            reference_date,
            logger,
            language,
        )
        section_reports["summary"] = clean_summary_text(
            summary,
            company_name=company_name,
            display_symbol=display_symbol,
        )
    except Exception as exc:
        logger.error(f"Error processing summary: {exc}")
        section_reports["summary"] = "Summary generation failed"

    return section_reports


async def finalize_markdown(
    logger: Any,
    markdown: str,
    *,
    language: str,
    market: str,
) -> str:
    """Clean markdown, annotate footnotes, optionally translate."""
    del market  # reserved for market-specific finalize hooks later
    markdown = clean_markdown(markdown)
    markdown = await annotate_financial_terms(markdown, language, logger)
    if language and language.lower() != "en":
        from prism.core.shared.translation import translate_report

        markdown = await translate_report(markdown, language)
    return markdown
