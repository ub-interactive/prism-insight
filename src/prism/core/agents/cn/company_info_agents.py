from mcp_agent.agents.agent import Agent


def create_company_status_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    language: str = "en",
    prefetched_data: dict | None = None,
) -> Agent:
    pf = prefetched_data or {}
    blocks = "\n\n".join(
        v for k, v in pf.items() if v and k in ("stock_info", "financial_statements")
    )
    instruction = f"""You are a China A-share financial analyst for {company_name} ({code}.{exchange}).

## Pre-collected Data
{blocks or "No financial data was prefetched. State clearly when metrics are unavailable; do not invent PER, PBR, ROE, revenue, profit, debt, or dividend figures."}

Analyze PER, PBR, ROE, revenue/profit trends, debt, dividends in CNY.
Analyze only metrics explicitly present in the pre-collected data; omit unavailable metrics rather than estimating.
All monetary values in CNY (人民币).

## Report Structure
- Start with \\n\\n before the title
- Sub-sections use #### headings
Report title: ### 2-1. Company Financial Status
Analysis date: {reference_date}
"""
    return Agent(name="cn_company_status_agent", instruction=instruction, server_names=[])


def create_company_overview_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    language: str = "en",
    prefetched_data: dict | None = None,
) -> Agent:
    pf = prefetched_data or {}
    profile = pf.get("company_profile", "")
    instruction = f"""You are a China A-share industry analyst for {company_name} ({code}.{exchange}).

## Pre-collected Profile
{profile or "No company profile was prefetched. State clearly when data is unavailable; do not invent business details, competitors, or segment revenue."}

Cover business model, competitive position, industry drivers, risks.
Only analyze facts present in the pre-collected profile; do not fill gaps with general knowledge.

## Report Structure
- Start with \\n\\n before the title
- Sub-sections use #### headings
Report title: ### 2-2. Company Overview
Analysis date: {reference_date}
"""
    return Agent(name="cn_company_overview_agent", instruction=instruction, server_names=[])
