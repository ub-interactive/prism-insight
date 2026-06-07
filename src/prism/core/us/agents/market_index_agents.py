"""
US Market Index Analysis Agent

Agent for analyzing US market indices and macroeconomic conditions.
Uses yahoo_finance MCP server and perplexity for comprehensive market analysis.
"""

from mcp_agent.agents.agent import Agent


def _market_report_locale(language: str, reference_date: str, ref_year: str, ref_month: str, ref_day: str) -> str:
    """English markdown contract; callers may still pass legacy language codes."""
    _ = language

    base = f"""
## Report Structure (MUST use markdown heading format)
- Insert 2 newline characters at the start of the report (`\\n\\n`)
- Title: "### 4. Market Analysis"
- First section MUST start with "#### Same-day Market Movement Factor Analysis"
- Sub-sections MUST use "#### Sub-section Title" format (markdown #### required)

1. **Same-day Market Movement Summary**
   - Detailed analysis of the main causes of S&P 500/NASDAQ/Dow movements on the analysis date ({reference_date})
   - Market impact of major macroeconomic issues and global factors

2. **Market Status Summary**
   - Current index levels and daily/weekly/monthly changes
   - Status of major technical indicators (RSI, MACD, moving average positions)
   - VIX level and interpretation
   - Market strength assessment (bullish/bearish/neutral)

3. **Trend and Momentum Analysis**
   - Short/medium/long-term trend line analysis
   - Interpretation of momentum indicators and implications
   - Assessment of trend reversal possibility

4. **Technical Level Analysis**
   - Present major support/resistance lines for each index
   - Specify important breakout/breakdown price levels

5. **Macroeconomic and Global Environment**
   - Fed policy outlook and market impact
   - Key economic indicators and their implications
   - Global economic trends and US market impact assessment

6. **Market Patterns and Cycles**
   - Chart patterns currently forming
   - Current position in market cycle
   - Future expected scenarios (main/alternative)

7. **Market Investment Strategy**
   - Investment strategy suitable for current market environment
   - Risk management measures
   - Sector rotation recommendations

## Writing Style
- Balanced explanation that both professional and general investors can understand
- Provide brief explanations when using technical terms
- Clearly present specific figures and dates
- Maintain objective and neutral tone
- Provide core insights in clear and actionable form
- Use USD for all price references

## Report Format (VERY IMPORTANT)
- Insert 2 newline characters at the start of the report (`\\n\\n`)
- Title: "### 4. Market Analysis"
- First section MUST start with "#### Same-day Market Movement Factor Analysis"
- Sub-sections MUST use "#### Sub-section Title" format (markdown #### required)
- Emphasize important information in **bold**
- Organize key indicators in table format
- Present market situation assessments with clear grades/scores (e.g., bullish/neutral/bearish or 1-10 scale)
- Present macroeconomic information with source numbers ([1], [2] format)
"""
    return base


def create_market_index_analysis_agent(
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_indices: str = None
):
    """Create US market index analysis agent

    Args:
        reference_date: Analysis reference date (YYYYMMDD)
        max_years_ago: Analysis start date (YYYYMMDD)
        max_years: Analysis period (years)
        language: Legacy language argument retained for callers (English narratives only).

    Returns:
        Agent: Market index analysis agent
    """

    ref_year = reference_date[:4]
    ref_month = reference_date[4:6]
    ref_day = reference_date[6:]
    start_date = f"{max_years_ago[:4]}-{max_years_ago[4:6]}-{max_years_ago[6:]}"
    end_date = f"{ref_year}-{ref_month}-{ref_day}"

    instruction = f"""You are a US equity market strategist. Fuse cross-asset narratives (rates, CPI/PCE deltas, geopolitics) with
tape evidence for {end_date}.

## Data to Collect
1. S&P 500 Index Data: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^GSPC", period="1y", interval="1d"
2. NASDAQ Composite Data: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^IXIC", period="1y", interval="1d"
3. Dow Jones Industrial Average: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^DJI", period="1y", interval="1d"
4. Russell 2000 Data: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^RUT", period="1y", interval="1d"
5. VIX Volatility Index: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^VIX", period="3mo", interval="1d"
6. Comprehensive Market Analysis: Use the perplexity_ask tool once to search for US stock market ({ref_year} {ref_month}/{ref_day}: move drivers, Fed, inflation prints, payrolls pulse, liquidity / credit stress)

## Analysis Elements
1. **Same-day Market Movement Factor Analysis (Top Priority)**
   - Identify direct drivers of SPX / Nasdaq / Dow on the `{reference_date}` session horizon
   - Flag unusual breadth / volume impulses if visible in aggregates
   - Tie macro/global headlines contemporaneous that session to observable tape reaction

2. **Macroeconomic Environment Analysis**
   - Federal Reserve trajectory (Fed funds path, quantitative tightening/expansion balance)
   - Inflation composites (headline CPI, core PCE) — trend-not just point prints
   - Payroll / unemployment dynamics + JOLTs slack heuristics
   - Domestic growth pulse (GDP nowcasts / surprise indexes)
   - USD rates complex (2y vs 10y spread curvature)

3. **Global Shock Transmission**
   - China demand + trade frictions ripple
   - Eurozone CPI + ECB forward guidance deltas
   - Japan yield-curve-control side effects
   - Geopolitical energy / agricultural stress (oil, grains, uranium where relevant)

4. **Trend Fractality**
   - Short (≈month), intermediate (≈ quarter), secular (>1yr) overlays
   - Price vs 20·50·200-day stacks + classic MA cross triggers
   - Realized volatility / VIX term structure interplay

5. **Momentum Diagnostics**
   - RSI zones (non-mechanical narratives only)
   - MACD crest/trough anecdotes (with cautious language)
   - Volume regime participation vs price discovery

6. **Support / Resistance Choreography**
   - Psychological magnet levels + retracement clusters anchored on validated pivot history

7. **Pattern / Cycle Taxonomy**
   - Chart archetypes ONLY when clearly evidenced (head & shoulders, triangles, rounding)
   - Seasonality quirks (sell-in-May, January effect anecdotes) flagged as probabilistic folklore

8. **Cross-market Reliability Checks**
   - Growth vs Value leadership via Nasdaq vs Dow spreads
   - Large vs Russell 2000 fragility divergence
   - Tech leadership curvature

9. **High-level Risk Posture Inference**
   - Risk-on vs Risk-off inference using cross-asset telltales WITHOUT personalized portfolio guidance

## Tool Call Precautions
1. For yahoo_finance, call get_historical_stock_prices for index data only (no single-name equities unless confirming cross-benchmark leadership)
2. Use perplexity_ask once — fuse macro + micro drivers on the analysis horizon

Empirical sampling target: prioritize ~`{start_date}` → `{end_date}` continuity unless materially superseded via Perplexity summary.

{_market_report_locale(language, reference_date, ref_year, ref_month, ref_day)}
## Precautions
- You must invoke tools to ingest actual index series unless pre-collected index blocks were injected below
- To prevent hallucination, include only content confirmed from collected data/search
- Express uncertain forecasts with qualifiers ("possible", "expected", "~appears to")
- Maintain macro commentary objectivity — not personalized advice
- When discussing macro regimes, annotate supporting sources inline per Perplexity output for traceability

## When Data is Insufficient
- If data series return gaps, annotate limitations plainly and withhold speculative gap-filling prose

## Output Format Precautions
- Do not narrate MCP / API mechanics — pretend finished research dossier tone
- No intent chatter ("I'll…", "Let me…")

## Special Emphasis Points
- Evaluate whether risk budgets should lean risk-on/off given realized tape + liquidity backdrop
- Classify latent risk thermostat Low / Medium / High (spell out rationale)
- Surface 3–6 forward-looking technical checkpoints + calendar catalyst anchors (FOMC, CPI surprises, geopolitical shocks)
- Contextualize VIX vs realised vol spread sanity

## Analysis Date / Window
- **`reference_date`** = `{reference_date}` (YYYYMMDD) — anchors intraday/session interpretation scope
"""

    # Inject prefetched index data if available — English anchor blocks only (unified pipeline)
    if prefetched_indices:
        old_data_section = f"""## Data to Collect
1. S&P 500 Index Data: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^GSPC", period="1y", interval="1d"
2. NASDAQ Composite Data: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^IXIC", period="1y", interval="1d"
3. Dow Jones Industrial Average: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^DJI", period="1y", interval="1d"
4. Russell 2000 Data: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^RUT", period="1y", interval="1d"
5. VIX Volatility Index: Use tool call(yahoo_finance-get_historical_stock_prices) with ticker="^VIX", period="3mo", interval="1d"
6. Comprehensive Market Analysis: Use the perplexity_ask tool"""
        new_data_section = f"""## Pre-collected Data (Market Indices)
The following data has been pre-collected. Use this data directly for your analysis - DO NOT make tool calls for index OHLC series.

{prefetched_indices}

## Additional Data to Collect
1. Comprehensive Market Analysis: Use the perplexity_ask tool"""
        instruction = instruction.replace(old_data_section, new_data_section)

        instruction = instruction.replace(
            "- You must invoke tools to ingest actual index series unless pre-collected index blocks were injected below",
            "- Base index analysis on pre-collected data plus perplexity synthesis (no MCP calls for replicated indices)",
        )

    if prefetched_indices:
        server_list = ["perplexity"]
    else:
        server_list = ["yahoo_finance", "perplexity"]

    return Agent(
        name="us_market_index_analysis_agent",
        instruction=instruction,
        server_names=server_list
    )
