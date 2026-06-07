"""
US Stock Price Analysis Agents

Agents for technical analysis and institutional holdings analysis of US stocks.
Uses yahoo_finance MCP server for data (Alex2Yang97/yahoo-finance-mcp).
"""

from mcp_agent.agents.agent import Agent


_PRICE_VOLUME_REPORT_BLOCK = """
## Report Structure (MUST use markdown heading format)
### 1-1. Price and Volume Analysis
#### Stock Price Data Overview and Summary
- recent trends, key price levels, volatility
#### Trading Volume Analysis
- volume patterns, correlation with price movements
#### Key Technical Indicators and Interpretation
- moving averages, support/resistance levels, other indicators
#### Future Outlook from Technical Perspective
- short/medium-term expected flow, price levels to watch

## Writing Style
- Provide clear explanations that individual investors can understand
- Specify key figures and dates concretely
- Provide the meaning and general interpretation of technical signals
- Present conditional scenarios rather than definitive predictions
- Focus on key technical indicators and patterns and omit unnecessary details
- Use USD for all price references

## Report Format (VERY IMPORTANT)
- Insert 2 newline characters at the start of the report (\\n\\n)
- Title: "### 1-1. Price and Volume Analysis"
- Sub-sections MUST use "#### Sub-section Title" format (markdown #### required)
- Emphasize important information in **bold**
- Present major data summaries in table format
- Present key support/resistance levels, trading points, and other important price levels as specific figures in USD
"""


def _price_volume_report_locale(language: str) -> str:
    """Markdown structure is English-only; callers may still pass legacy language codes."""
    _ = language
    return _PRICE_VOLUME_REPORT_BLOCK


_INSTITUTIONAL_REPORT_BLOCK = """
## Report Structure (MUST use markdown heading format)
### 1-2. Institutional Ownership Analysis
#### Overview of Institutional Ownership
- Summary of ownership breakdown
#### Major Institutional Holders Analysis
- Top 10 holders, position sizes, recent changes
#### Mutual Fund and ETF Holdings
- Key fund positions
#### Ownership Trend Analysis
- Recent quarterly changes
#### Implications and Outlook
- What institutional activity suggests about the stock

## Writing Style
- Provide clear explanations that individual investors can understand
- Specify key percentages and institution names concretely
- Provide the meaning and general interpretation of institutional patterns
- Present conditional scenarios rather than definitive predictions
- Focus on significant ownership changes and patterns

## Report Format (VERY IMPORTANT)
- Insert 2 newline characters at the start of the report (\\n\\n)
- Title: "### 1-2. Institutional Ownership Analysis"
- Sub-sections MUST use "#### Sub-section Title" format (markdown #### required)
- Emphasize important information in **bold**
- Present major data summaries in table format
- Present key ownership percentages and holder names with specific figures
"""


def _institutional_report_locale(language: str) -> str:
    _ = language
    return _INSTITUTIONAL_REPORT_BLOCK


def create_price_volume_analysis_agent(
    company_name: str,
    ticker: str,
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_data: str = None
):
    """Create US stock price and trading volume analysis agent

    Args:
        company_name: Company name (e.g., "Apple Inc.")
        ticker: Stock ticker symbol (e.g., "AAPL")
        reference_date: Analysis reference date (YYYYMMDD)
        max_years_ago: Analysis start date (YYYYMMDD)
        max_years: Analysis period (years)
        language: Language code for legacy callers (English-only narratives).

    Returns:
        Agent: Stock price and trading volume analysis agent
    """

    instruction = f"""You are a US stock technical analysis expert. Analyze the given stock's price and volume data and write a technical analysis report.

## Data to Collect
1. Stock Price/Volume Data: Use tool call(name: yahoo_finance-get_historical_stock_prices) to collect data
   - Parameters: ticker="{ticker}", period="1y", interval="1d"

## Analysis Elements
1. Stock Price Trend and Pattern Analysis (uptrend/downtrend/sideways, chart patterns)
2. Moving Average Analysis (short/medium/long-term moving average golden cross/dead cross)
   - 20-day, 50-day, 200-day moving averages (US market standard)
3. Identification and explanation of major support and resistance levels
4. Trading Volume Analysis (relationship between volume change patterns and price movements)
5. **Technical Indicators - MUST CALCULATE from OHLCV data:**
   - RSI (14-day): Calculate using closing prices. RS = Avg Gain / Avg Loss, RSI = 100 - (100 / (1 + RS)). Report exact value (e.g., RSI = 72.5)
   - MACD: 12-day EMA - 26-day EMA, Signal line = 9-day EMA of MACD. Report MACD value and signal line value
   - Bollinger Bands (20-day): Middle = 20-day SMA, Upper/Lower = Middle ± 2×Standard Deviation. Report current price position relative to bands
6. Short/medium-term technical outlook
{_price_volume_report_locale(language)}
## Precautions
- You must make a tool call (unless replaced below when pre-collected OHLCV is provided)
- To prevent hallucination, include only content confirmed from actual data
- Express uncertain content with phrases like "there is a possibility", "it appears to be", etc.
- Write from an information provision perspective, not investment solicitation
- Use objective descriptions like "technically in a ~ situation" rather than strong buy/sell recommendations

## When Data is Insufficient
- If data is insufficient, clearly mention it and provide limited analysis with available data only
- Use explicit expressions like "Confirmation is difficult due to insufficient data on ~"

## Output Format Precautions
- Do not include mentions of tool usage in the final report (e.g., "Calling tool..." or "I'll use..." etc.)
- Exclude explanations of tool calling processes or methods, include only collected data and analysis results
- Start the report naturally as if all data collection has already been completed
- Start directly with the analysis content without intent expressions like "I'll create...", "I'll analyze...", "Let me..."
- The report must always start with the title along with 2 newline characters ("\\n\\n")

Company: {company_name} ({ticker})
## Analysis Date: {reference_date}(YYYYMMDD format)
"""

    # Inject prefetched data if available
    if prefetched_data:
        instruction = instruction.replace(
            "## Data to Collect\n1. Stock Price/Volume Data: Use tool call(name: yahoo_finance-get_historical_stock_prices) to collect data\n   - Parameters: ticker=\"" + ticker + "\", period=\"1y\", interval=\"1d\"",
            f"## Pre-collected Data (OHLCV)\nThe following data has been pre-collected. Use this data directly for your analysis - DO NOT make any tool calls for OHLCV data.\n\n{prefetched_data}"
        )
        instruction = instruction.replace(
            "- You must make a tool call (unless replaced below when pre-collected OHLCV is provided)",
            "- Analyze based on the pre-collected data provided above (do not call tools for OHLCV)",
        )

    return Agent(
        name="us_price_volume_analysis_agent",
        instruction=instruction,
        server_names=[] if prefetched_data else ["yahoo_finance"]
    )


def create_institutional_holdings_analysis_agent(
    company_name: str,
    ticker: str,
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_data: str = None
):
    """Create US institutional holdings analysis agent

    In the US market, we analyze institutional ownership instead of Korean
    investor types (institutional/foreign/individual).

    Args:
        company_name: Company name
        ticker: Stock ticker symbol
        reference_date: Analysis reference date (YYYYMMDD)
        max_years_ago: Analysis start date (YYYYMMDD)
        max_years: Analysis period (years)
        language: Language code for legacy callers (English-only narratives).

    Returns:
        Agent: Institutional holdings analysis agent
    """

    instruction = f"""You are an expert in analyzing institutional ownership data in the US stock market. Analyze the institutional holdings data of the given stock and write an institutional ownership report.

## Data to Collect
1. Major Holders Data: Use tool call(name: yahoo_finance-get_holder_info) to collect major holders data
   - Parameters: ticker="{ticker}", holder_type="major_holders"
2. Institutional Holdings Data: Use tool call(name: yahoo_finance-get_holder_info) to collect institutional holder data
   - Parameters: ticker="{ticker}", holder_type="institutional_holders"
3. Mutual Fund Holdings: Use tool call(name: yahoo_finance-get_holder_info) to collect mutual fund holder data
   - Parameters: ticker="{ticker}", holder_type="mutualfund_holders"

## Analysis Elements
1. Institutional Ownership Percentage Analysis
   - Total institutional ownership %
   - Comparison with sector/industry average
2. Top Institutional Holders Analysis
   - Major institutions holding the stock (e.g., Vanguard, BlackRock, State Street)
   - Recent position changes by major holders
3. Mutual Fund Holdings
   - Top mutual funds holding the stock
   - Fund types (index funds, actively managed, etc.)
4. Ownership Trend Analysis
   - Quarterly changes in institutional ownership
   - Net buying/selling patterns
5. Smart Money Signals
   - Hedge fund activity
   - Insider ownership changes (if available)
{_institutional_report_locale(language)}
## Precautions
- You must make a tool call (unless replaced below when pre-collected holder data is provided)
- To prevent hallucination, include only content confirmed from actual data
- Express uncertain content with phrases like "there is a possibility", "it appears to be", etc.
- Write from an information provision perspective, not investment solicitation
- Avoid biased interpretations that suggest institutional buying/selling is always correct

## When Data is Insufficient
- If data is insufficient, clearly mention it and provide limited analysis with available data only
- Use explicit expressions like "Confirmation is difficult due to insufficient data on ~"

## Output Format Precautions
- Do not include mentions of tool usage in the final report (e.g., "Calling tool..." or "I'll use..." etc.)
- Exclude explanations of tool calling processes or methods, include only collected data and analysis results
- Start the report naturally as if all data collection has already been completed
- Start directly with the analysis content without intent expressions like "I'll create...", "I'll analyze...", "Let me..."
- The report must always start with the title along with 2 newline characters ("\\n\\n")

Company: {company_name} ({ticker})
## Analysis Date: {reference_date}(YYYYMMDD format)
"""

    # Inject prefetched data if available
    if prefetched_data:
        instruction = instruction.replace(
            "## Data to Collect\n1. Major Holders Data: Use tool call(name: yahoo_finance-get_holder_info) to collect major holders data\n   - Parameters: ticker=\"" + ticker + "\", holder_type=\"major_holders\"\n2. Institutional Holdings Data: Use tool call(name: yahoo_finance-get_holder_info) to collect institutional holder data\n   - Parameters: ticker=\"" + ticker + "\", holder_type=\"institutional_holders\"\n3. Mutual Fund Holdings: Use tool call(name: yahoo_finance-get_holder_info) to collect mutual fund holder data\n   - Parameters: ticker=\"" + ticker + "\", holder_type=\"mutualfund_holders\"",
            f"## Pre-collected Data (Institutional Holdings)\nThe following data has been pre-collected. Use this data directly for your analysis - DO NOT make any tool calls for holder data.\n\n{prefetched_data}"
        )
        instruction = instruction.replace(
            "- You must make a tool call (unless replaced below when pre-collected holder data is provided)",
            "- Analyze based on the pre-collected data provided above (do not call tools for holder data)",
        )

    return Agent(
        name="us_institutional_holdings_analysis_agent",
        instruction=instruction,
        server_names=[] if prefetched_data else ["yahoo_finance"]
    )
