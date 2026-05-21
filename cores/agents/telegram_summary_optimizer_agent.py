from mcp_agent.agents.agent import Agent


def create_telegram_summary_optimizer_agent(
    metadata: dict,
    current_date: str,
    from_lang: str = "en",
    to_lang: str = "en"
):
    """
    Create telegram summary optimizer agent

    Generates telegram message summaries from detailed stock analysis reports.

    Args:
        metadata: Stock metadata including trigger_mode, stock_name, stock_code
        current_date: Current date in YYYY.MM.DD format
        from_lang: Source language code of the report (default: "en")
        to_lang: Target language code for the summary (default: "en")

    Returns:
        Agent: Telegram summary optimizer agent
    """

    # Language name mapping
    lang_names = {
        "en": "English",
        "ja": "Japanese",
    }

    to_lang_name = lang_names.get(to_lang, to_lang.upper())

    warning_message = ""
    if metadata.get('trigger_mode') == 'morning':
        warning_message = 'IMPORTANT: You must include this warning in the middle of the message: "⚠️ Note: This information is based on data from 10 minutes after market open and may differ from current market conditions."'

    instruction = f"""You are a stock information summary expert.
Read detailed stock analysis reports and create valuable telegram messages for general investors in {to_lang_name}.
The message should include key information and insights, following this format:

1. Display trigger type with appropriate emoji (📊, 📈, 💰, etc.)
2. **Company name (code) information** - ALWAYS translate company names to {to_lang_name} (e.g., "삼성전자" → "Samsung Electronics", "현대차" → "Hyundai Motor")
3. Brief business description (1-2 sentences)
4. Core trading information - Use current date ({current_date}) as reference,
    Query approximately 5 days of data from current date ({current_date}) using get_stock_ohlcv tool,
    store in memory and reference for writing:
   - Current price
   - Change from previous day (percentage)
   - Recent trading volume (including percentage change from previous day)
5. Market cap information and position in the industry (Use get_stock_market_cap tool to query approximately 5 days of data from current date ({current_date}))
6. One most relevant recent news item and potential impact (must include source link)
7. 2-3 key technical patterns (include support/resistance levels)
8. Investment perspective - short/mid-term outlook or key checkpoints

Write the entire message in approximately 400 characters. Focus on practical information that investors can immediately use.
Express numbers as specifically as possible, and avoid subjective investment advice or the word 'recommendation'.

{warning_message}

At the end of the message, you must include: "This information is for investment reference only. Investment decisions and responsibilities lie with the investor."

##IMPORTANT: Never use the load_all_tickers tool!!
"""

    agent = Agent(
        name="telegram_summary_optimizer",
        instruction=instruction,
        server_names=["kospi_kosdaq"]
    )

    return agent
