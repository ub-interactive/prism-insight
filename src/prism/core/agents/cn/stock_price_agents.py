from mcp_agent.agents.agent import Agent


def create_price_volume_analysis_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_data: str | None = None,
) -> Agent:
    data_block = (
        f"## Pre-collected Data (OHLCV)\n{prefetched_data}\n"
        if prefetched_data
        else "## Data\nUse provided context only."
    )
    instruction = f"""You are a China A-share technical analyst. Analyze {company_name} ({code}.{exchange}) using CNY prices.

{data_block}

## Analysis Elements
1. Price trend and patterns (uptrend/downtrend/sideways)
2. Moving averages (5/10/20/60-day — A-share conventions)
3. Support and resistance in CNY
4. Volume analysis (换手率, 成交额)
5. RSI(14), MACD, Bollinger Bands from OHLCV
6. A-share context: limit-up/limit-down rules, T+1 settlement

## Report Structure
- Start with \\n\\n### 1-1. Price and Volume Analysis
- Sub-sections use #### headings
- All prices in CNY

Company: {company_name} ({code}.{exchange})
Analysis date: {reference_date}
"""
    return Agent(
        name="cn_price_volume_analysis_agent",
        instruction=instruction,
        server_names=[],
    )


def create_institutional_holdings_analysis_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_data: str | None = None,
) -> Agent:
    data_block = (
        f"## Pre-collected Holder Data\n{prefetched_data}\n"
        if prefetched_data
        else ""
    )
    instruction = f"""You are a China A-share ownership analyst for {company_name} ({code}.{exchange}).

{data_block}

Analyze:
1. Top 10 shareholders (十大股东) concentration
2. Fund holdings (基金持仓) trends
3. Northbound Stock Connect flow (北向资金) if data present
4. Implications for float and governance

## Report Structure
- Start with \\n\\n### 1-2. Institutional and Major Holder Analysis
- Sub-sections use #### headings

Analysis date: {reference_date}
"""
    return Agent(
        name="cn_institutional_holdings_analysis_agent",
        instruction=instruction,
        server_names=[],
    )
