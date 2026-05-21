"""Agent directory for the US-only pipeline."""

from datetime import datetime, timedelta
from typing import Dict, List

from cores.agents.company_info_agents import (
    create_company_overview_agent,
    create_company_status_agent,
)
from cores.agents.market_index_agents import create_market_index_analysis_agent
from cores.agents.news_strategy_agents import create_news_analysis_agent
from cores.agents.stock_price_agents import (
    create_institutional_holdings_analysis_agent,
    create_price_volume_analysis_agent,
)


def get_data_urls(ticker: str) -> Dict[str, str]:
    return {
        "profile": f"https://finance.yahoo.com/quote/{ticker}/profile",
        "key_statistics": f"https://finance.yahoo.com/quote/{ticker}/key-statistics",
        "financials": f"https://finance.yahoo.com/quote/{ticker}/financials",
        "analysis": f"https://finance.yahoo.com/quote/{ticker}/analysis",
        "holders": f"https://finance.yahoo.com/quote/{ticker}/holders",
        "news": f"https://finance.yahoo.com/quote/{ticker}/news",
        "sec_filings": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-&dateb=&owner=include&count=40",
    }


def get_agent_directory(
    company_name: str,
    ticker: str,
    reference_date: str,
    base_sections: List[str],
    language: str = "en",
    prefetched_data: dict | None = None,
):
    urls = get_data_urls(ticker)
    ref_date = datetime.strptime(reference_date, "%Y%m%d")
    max_years = 1
    max_years_ago = (ref_date - timedelta(days=365 * max_years)).strftime("%Y%m%d")

    pf = prefetched_data or {}
    market_indices = pf.get("market_indices", {})
    combined_indices = "\n\n".join(market_indices.values()) if market_indices else None

    agent_creators = {
        "price_volume_analysis": lambda: create_price_volume_analysis_agent(
            company_name, ticker, reference_date, max_years_ago, max_years, language,
            prefetched_data=pf.get("stock_ohlcv"),
        ),
        "institutional_holdings_analysis": lambda: create_institutional_holdings_analysis_agent(
            company_name, ticker, reference_date, max_years_ago, max_years, language,
            prefetched_data=pf.get("holder_info"),
        ),
        "company_status": lambda: create_company_status_agent(
            company_name,
            ticker,
            reference_date,
            urls,
            language,
            prefetched_data={
                "stock_info": pf.get("stock_info", ""),
                "recommendations": pf.get("recommendations", ""),
                "analysis_estimates": pf.get("analysis_estimates", ""),
                "financial_statements": pf.get("financial_statements", ""),
            }
            if pf.get("stock_info")
            else None,
        ),
        "company_overview": lambda: create_company_overview_agent(
            company_name,
            ticker,
            reference_date,
            urls,
            language,
            prefetched_data={
                "company_profile": pf.get("company_profile", ""),
                "holder_info": pf.get("holder_info", ""),
                "segment_revenue": pf.get("segment_revenue", ""),
            }
            if pf.get("company_profile")
            else None,
        ),
        "news_analysis": lambda: create_news_analysis_agent(
            company_name,
            ticker,
            reference_date,
            language,
            prefetched_social_sentiment=pf.get("social_sentiment"),
        ),
        "market_index_analysis": lambda: create_market_index_analysis_agent(
            reference_date, max_years_ago, max_years, language,
            prefetched_indices=combined_indices,
        ),
    }

    agents = {}
    for section in base_sections:
        if section in agent_creators:
            agents[section] = agent_creators[section]()
    return agents
