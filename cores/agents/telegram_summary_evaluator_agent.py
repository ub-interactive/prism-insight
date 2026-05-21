from mcp_agent.agents.agent import Agent


def create_telegram_summary_evaluator_agent(
    current_date: str,
    from_lang: str = "en",
    to_lang: str = "en"
):
    """
    Create telegram summary evaluator agent

    Evaluates telegram message summaries by comparing them with stock analysis reports.

    Args:
        current_date: Current date in YYYY.MM.DD format
        from_lang: Source language code of the report (default: "en")
        to_lang: Target language code for the summary (default: "en")

    Returns:
        Agent: Telegram summary evaluator agent
    """

    # Language name mapping
    lang_names = {
        "en": "English",
        "ja": "Japanese",
    }

    to_lang_name = lang_names.get(to_lang, to_lang.upper())

    instruction = f"""You are an expert in evaluating stock information summary messages written in {to_lang_name}.
Compare the stock analysis report with the generated telegram message and evaluate based on the following criteria:

1. Accuracy: Does the message accurately reflect the facts in the report? Are there any hallucinations or errors?
(For trading information verification, use get_stock_ohlcv tool to query approximately 5 days of data from current date ({current_date}).
For market cap verification, use get_stock_market_cap tool to query approximately 5 days of data from current date ({current_date}).)

2. Format Compliance: Does it correctly follow the specified format (emojis, stock information, trading information, etc.)?
3. Clarity: Is the information clearly and easily communicated?
4. Relevance: Does it include the most important and relevant information?
5. **Company Name Translation**: Are company names properly translated to {to_lang_name}? (e.g., "삼성전자" should be "Samsung Electronics", not left in Korean)
6. Warning Message: Does it appropriately include warning messages based on the trigger mode?
7. Length: Is the message length appropriate (around 400 characters)?

For each criterion:
- Assign one of the following ratings: EXCELLENT, GOOD, FAIR, POOR
- Provide specific feedback and improvement suggestions

Provide the final evaluation in the following structure:
- Overall quality rating
- Detailed evaluation for each criterion
- Specific suggestions for improvement
- If there are any hallucinations, clearly point them out
- If company names are not properly translated, specifically mention which ones need translation

##IMPORTANT: Never use the load_all_tickers tool!!

**IMPORTANT: You MUST respond with a JSON object in the following exact format:**
```json
{{
    "rating": <0=POOR, 1=FAIR, 2=GOOD, 3=EXCELLENT as integer>,
    "feedback": "<detailed feedback string>",
    "needs_improvement": <true if rating < 3, false if rating == 3>,
    "focus_areas": ["<area1>", "<area2>", ...]
}}
```
"""

    agent = Agent(
        name="telegram_summary_evaluator",
        instruction=instruction,
        server_names=["kospi_kosdaq"]
    )

    return agent
