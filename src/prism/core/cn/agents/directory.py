from datetime import datetime, timedelta
from typing import List

from prism.core.cn.agents.company_info_agents import (
    create_company_overview_agent,
    create_company_status_agent,
)
from prism.core.cn.agents.market_index_agents import create_market_index_analysis_agent
from prism.core.cn.agents.news_agents import create_news_analysis_agent
from prism.core.cn.agents.stock_price_agents import (
    create_institutional_holdings_analysis_agent,
    create_price_volume_analysis_agent,
)


def get_agent_directory(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    base_sections: List[str],
    language: str = "en",
    prefetched_data: dict | None = None,
):
    pf = prefetched_data or {}
    ref_date = datetime.strptime(reference_date, "%Y%m%d")
    max_years = 1
    max_years_ago = (ref_date - timedelta(days=365 * max_years)).strftime("%Y%m%d")
    market_indices = pf.get("market_indices", {})
    combined_indices = "\n\n".join(market_indices.values()) if market_indices else None

    creators = {
        "price_volume_analysis": lambda: create_price_volume_analysis_agent(
            company_name, code, exchange, reference_date, max_years_ago, max_years, language,
            prefetched_data=pf.get("stock_ohlcv"),
        ),
        "institutional_holdings_analysis": lambda: create_institutional_holdings_analysis_agent(
            company_name, code, exchange, reference_date, max_years_ago, max_years, language,
            prefetched_data=pf.get("holder_info"),
        ),
        "company_status": lambda: create_company_status_agent(
            company_name, code, exchange, reference_date, language,
            prefetched_data={
                "stock_info": pf.get("stock_info", ""),
                "financial_statements": pf.get("financial_statements", ""),
            },
        ),
        "company_overview": lambda: create_company_overview_agent(
            company_name, code, exchange, reference_date, language,
            prefetched_data={"company_profile": pf.get("company_profile", "")},
        ),
        "news_analysis": lambda: create_news_analysis_agent(
            company_name, code, exchange, reference_date, language,
        ),
        "market_index_analysis": lambda: create_market_index_analysis_agent(
            reference_date, max_years_ago, max_years, language,
            prefetched_indices=combined_indices,
        ),
    }

    return {s: creators[s]() for s in base_sections if s in creators}
