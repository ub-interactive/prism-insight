from mcp_agent.agents.agent import Agent

def create_price_volume_analysis_agent(company_name, company_code, reference_date, max_years_ago, max_years, language: str = "ko", prefetched_data: str = None):
    """Create stock price and trading volume analysis agent

    Args:
        company_name: Company name
        company_code: Stock code
        reference_date: Analysis reference date (YYYYMMDD)
        max_years_ago: Analysis start date (YYYYMMDD)
        max_years: Analysis period (years)
        language: Language code ("ko" or "en")
        prefetched_data: Pre-collected OHLCV data (optional)

    Returns:
        Agent: Stock price and trading volume analysis agent
    """

    instruction = f"""You are a stock technical analysis expert. You need to analyze the stock price and trading volume data of the given stock and write a technical analysis report.

                    ## Data to Collect
                    1. Stock Price/Volume Data: Use tool call(name: kospi_kosdaq-get_stock_ohlcv) to collect data from {max_years_ago} to {reference_date} (collection period (years): {max_years})

                    ## Analysis Elements
                    1. Stock Price Trend and Pattern Analysis (uptrend/downtrend/sideways, chart patterns)
                    2. Moving Average Analysis (short/medium/long-term moving average golden cross/dead cross)
                    3. Identification and explanation of major support and resistance levels
                    4. Trading Volume Analysis (relationship between volume change patterns and price movements)
                    5. **Technical Indicators - MUST CALCULATE from OHLCV data:**
                       - RSI (14-day): Calculate using closing prices. RS = Avg Gain / Avg Loss, RSI = 100 - (100 / (1 + RS)). Report exact value (e.g., RSI = 72.5)
                       - MACD: 12-day EMA - 26-day EMA, Signal line = 9-day EMA of MACD. Report MACD value and signal line value
                       - Bollinger Bands (20-day): Middle = 20-day SMA, Upper/Lower = Middle ± 2×Standard Deviation. Report current price position relative to bands
                    6. Short/medium-term technical outlook

                    ## Report Structure
                    1. Stock Price Data Overview and Summary - recent trends, key price levels, volatility
                    2. Trading Volume Analysis - volume patterns, correlation with price movements
                    3. Key Technical Indicators and Interpretation - moving averages, support/resistance levels, other indicators
                    4. Future Outlook from Technical Perspective - short/medium-term expected flow, price levels to watch

                    ## Writing Style
                    - Provide clear explanations that individual investors can understand
                    - Specify key figures and dates concretely
                    - Provide the meaning and general interpretation of technical signals
                    - Present conditional scenarios rather than definitive predictions
                    - Focus on key technical indicators and patterns and omit unnecessary details

                    ## Report Format
                    - Insert 2 newline characters at the start of the report (\\n\\n)
                    - Title: "### 1-1. Stock Price and Trading Volume Analysis"
                    - Sub-sections MUST use "#### Sub-section Title" format (markdown #### required)
                    - Emphasize important information in **bold**
                    - Present major data summaries in table format
                    - Present key support/resistance levels, trading points, and other important price levels as specific figures

                    ## Precautions
                    - You must make a tool call
                    - To prevent hallucination, include only content confirmed from actual data
                    - Express uncertain content with phrases like "there is a possibility", "it appears to be", etc.
                    - Write from an information provision perspective, not investment solicitation
                    - Use objective descriptions like "technically in a ~ situation" rather than strong buy/sell recommendations
                    - Never use the load_all_tickers tool!!

                    ## When Data is Insufficient
                    - If data is insufficient, clearly mention it and provide limited analysis with available data only
                    - Use explicit expressions like "Confirmation is difficult due to insufficient data on ~"

                    ## Output Format Precautions
                    - Do not include mentions of tool usage in the final report (e.g., "Calling tool..." or "I'll use..." etc.)
                    - Exclude explanations of tool calling processes or methods, include only collected data and analysis results
                    - Start the report naturally as if all data collection has already been completed
                    - Start directly with the analysis content without intent expressions like "I'll create...", "I'll analyze...", "Let me..."
                    - The report must always start with the title along with 2 newline characters ("\\n\\n")

                    Company: {company_name} ({company_code})
                    ##Analysis Date: {reference_date}(YYYYMMDD format)
                    """
    # Inject prefetched data if available
    if prefetched_data:
        # Replace data collection instructions with pre-collected data
        instruction = instruction.replace(
            f"## Data to Collect\n                        1. Stock Price/Volume Data: Use tool call(name: kospi_kosdaq-get_stock_ohlcv) to collect data from {max_years_ago} to {reference_date} (collection period (years): {max_years})",
            f"## Pre-collected Data (OHLCV)\nThe following data has been pre-collected. Use this data directly for your analysis - DO NOT make any tool calls for OHLCV data.\n\n{prefetched_data}"
        )
        # Also update precautions to not require tool calls
        instruction = instruction.replace("- 반드시 tool call을 해야 합니다", "- 사전 수집된 데이터를 기반으로 분석합니다")
        instruction = instruction.replace("- You must make a tool call", "- Analyze based on the pre-collected data provided above")

    return Agent(
        name="price_volume_analysis_agent",
        instruction=instruction,
        server_names=[] if prefetched_data else ["kospi_kosdaq"]
    )


def create_investor_trading_analysis_agent(company_name, company_code, reference_date, max_years_ago, max_years, language: str = "ko", prefetched_data: str = None):
    """Create investor trading trend analysis agent

    Args:
        company_name: Company name
        company_code: Stock code
        reference_date: Analysis reference date (YYYYMMDD)
        max_years_ago: Analysis start date (YYYYMMDD)
        max_years: Analysis period (years)
        language: Language code ("ko" or "en")
        prefetched_data: Pre-collected investor trading volume data (optional)

    Returns:
        Agent: Investor trading trend analysis agent
    """

    instruction = f"""You are an expert in analyzing investor-specific trading data in the stock market. You need to analyze the trading data by investor type (institutional/foreign/individual) of the given stock and write an investor trend report.

                    ## Data to Collect
                    1. Trading Data by Investor Type: Use tool call(name: kospi_kosdaq-get_stock_trading_volume) to collect data from {max_years_ago} to {reference_date} (collection period (years): {max_years})

                    ## Analysis Elements
                    1. Analysis of trading patterns by investor type (institutional/foreign/individual)
                    2. Trend of net buying/net selling by major investor groups
                    3. Correlation between trading patterns by investor type and stock price movements
                    4. Identification of intensive buying/selling periods by specific investor groups
                    5. Recent changes in investor trends and future outlook

                    ## Report Structure
                    1. Overview of Trading by Investor Type - Summary of trading trends by major investor groups
                    2. Institutional Investor Analysis - Trading patterns, key time points, impact on stock price
                    3. Foreign Investor Analysis - Trading patterns, key time points, impact on stock price
                    4. Individual Investor Analysis - Trading patterns, key time points, impact on stock price
                    5. Comprehensive Analysis and Implications - Impact of investor trends on stock price and future outlook

                    ## Writing Style
                    - Provide clear explanations that individual investors can understand
                    - Specify key time points and data concretely
                    - Provide the meaning and general interpretation of investor patterns
                    - Present conditional scenarios rather than definitive predictions
                    - Focus on key patterns and data and omit unnecessary details

                    ## Report Format
                    - Insert 2 newline characters at the start of the report (\\n\\n)
                    - Title: "### 1-2. Investor Trading Trend Analysis"
                    - Sub-sections MUST use "#### Sub-section Title" format (markdown #### required)
                    - Emphasize important information in **bold**
                    - Present major data summaries in table format
                    - Present key trading patterns and time points as specific dates and figures

                    ## Precautions
                    - You must make a tool call
                    - To prevent hallucination, include only content confirmed from actual data
                    - Express uncertain content with phrases like "there is a possibility", "it appears to be", etc.
                    - Write from an information provision perspective, not investment solicitation
                    - Avoid biased interpretations that suggest trading by a specific investor group is always correct
                    - Never use the load_all_tickers tool!!

                    ## When Data is Insufficient
                    - If data is insufficient, clearly mention it and provide limited analysis with available data only
                    - Use explicit expressions like "Confirmation is difficult due to insufficient data on ~"

                    ## Output Format Precautions
                    - Do not include mentions of tool usage in the final report (e.g., "Calling tool..." or "I'll use..." etc.)
                    - Exclude explanations of tool calling processes or methods, include only collected data and analysis results
                    - Start the report naturally as if all data collection has already been completed
                    - Start directly with the analysis content without intent expressions like "I'll create...", "I'll analyze...", "Let me..."
                    - The report must always start with the title along with 2 newline characters ("\\n\\n")

                    Company: {company_name} ({company_code})
                    ##Analysis Date: {reference_date}(YYYYMMDD format)
                    """
    # Inject prefetched data if available
    if prefetched_data:
        instruction = instruction.replace(
            f"## Data to Collect\n                        1. Trading Data by Investor Type: Use tool call(name: kospi_kosdaq-get_stock_trading_volume) to collect data from {max_years_ago} to {reference_date} (collection period (years): {max_years})",
            f"## Pre-collected Data (Investor Trading Volume)\nThe following data has been pre-collected. Use this data directly for your analysis - DO NOT make any tool calls for trading volume data.\n\n{prefetched_data}"
        )
        instruction = instruction.replace("- 반드시 tool call을 해야 합니다", "- 사전 수집된 데이터를 기반으로 분석합니다")
        instruction = instruction.replace("- You must make a tool call", "- Analyze based on the pre-collected data provided above")

    return Agent(
        name="investor_trading_analysis_agent",
        instruction=instruction,
        server_names=[] if prefetched_data else ["kospi_kosdaq"]
    )
