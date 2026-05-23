from mcp_agent.agents.agent import Agent


def create_macro_intelligence_agent(reference_date, language="en", prefetched_data: dict = None):
    """Create macro intelligence agent for US market

    The agent receives pre-computed regime and index data from programmatic prefetch,
    and only calls perplexity for qualitative analysis (sector trends, risk events).

    Args:
        reference_date: Analysis reference date (YYYYMMDD)
        language: Legacy language argument retained for callers.
        prefetched_data: Dict with computed_regime, sp500_ohlcv_md, nasdaq_ohlcv_md, vix_ohlcv_md

    Returns:
        Agent: US macro intelligence agent
    """

    _ = language
    # Build context from prefetched data (language-agnostic)
    regime_context = ""
    index_data_context = ""

    if prefetched_data:
        computed = prefetched_data.get("computed_regime", {})
        if computed:
            regime = computed.get("market_regime", "sideways")
            confidence = computed.get("regime_confidence", 0.5)
            simple_ma = computed.get("simple_ma_regime", "sideways")
            idx = computed.get("index_summary", {})

            regime_context = f"""
## Pre-Computed Market Regime (from actual index data)

The following regime was computed programmatically from S&P 500 / VIX price data:
- **market_regime**: {regime}
- **regime_confidence**: {confidence}
- **simple_ma_regime**: {simple_ma}
- **S&P 500 20d trend**: {idx.get('sp500_20d_trend', 'N/A')}
- **S&P 500 vs 20d MA**: {idx.get('sp500_vs_20d_ma', 'N/A')}
- **S&P 500 4-week change**: {idx.get('sp500_4w_change_pct', 'N/A')}%
- **S&P 500 current**: {idx.get('sp500_current', 'N/A')}
- **S&P 500 20d MA**: {idx.get('sp500_20d_ma', 'N/A')}
- **NASDAQ 20d trend**: {idx.get('nasdaq_20d_trend', 'N/A')}
- **VIX current**: {idx.get('vix_current', 'N/A')}
- **VIX level**: {idx.get('vix_level', 'N/A')}

You MUST use these pre-computed values for market_regime, regime_confidence, simple_ma_regime, and index_summary.
You may adjust regime_confidence (±0.1) based on perplexity analysis, but DO NOT change market_regime unless
perplexity data provides overwhelming contradictory evidence.
"""

        sp500_md = prefetched_data.get("sp500_ohlcv_md", "")
        nasdaq_md = prefetched_data.get("nasdaq_ohlcv_md", "")
        vix_md = prefetched_data.get("vix_ohlcv_md", "")
        if sp500_md or nasdaq_md or vix_md:
            index_data_context = "\n## Pre-fetched Index Data\n\n"
            if sp500_md:
                index_data_context += sp500_md + "\n"
            if nasdaq_md:
                index_data_context += nasdaq_md + "\n"
            if vix_md:
                index_data_context += vix_md + "\n"

    _default_regime = prefetched_data.get('computed_regime', {}).get('market_regime', 'sideways') if prefetched_data else 'sideways'
    _default_confidence = prefetched_data.get('computed_regime', {}).get('regime_confidence', 0.5) if prefetched_data else 0.5
    _default_simple_ma = prefetched_data.get('computed_regime', {}).get('simple_ma_regime', 'sideways') if prefetched_data else 'sideways'
    _index_summary_json = _format_us_index_summary(prefetched_data)

    report_prose_guidance = """## report_prose Guidelines

Write the `report_prose` field as a professional 3–5 paragraph narrative in formal English covering:
1. Current market regime and its rationale
2. Leading sectors and why they are outperforming
3. Key risk events and their potential market impact
4. Recommended posture for risk-aware observers given the regime (informational framing; not individualized advice).

This prose is inserted verbatim into downstream stock-analysis reports."""

    instruction = f"""You are a US stock market macro intelligence analyst.
Follow the instructions below to collect data, then output ONLY valid JSON. Do not include any text outside the JSON.

Analysis date: {reference_date} (YYYYMMDD format)
{regime_context}
{index_data_context}
## Tool Call to Execute

### Perplexity macro search (1 call only)
Use the perplexity_ask tool once with query (English):
"{reference_date} US stock market macro trends, sector rotation, leading lagging sectors, risk events, geopolitical risks comprehensive analysis"

---

## Your Task

Based on perplexity AND the pre-computed index/regime artefacts above:
1. Keep market_regime, simple_ma_regime, and index_summary aligned with programmatic values unless overwhelming contradiction emerges (if you must override regime, cite exact contradicting datapoints inside regime_rationale only — still risky; default is deferral).
2. Identify leading vs lagging sectors grounded in perplexity text.
3. Surface risk-event objects + beneficiary thematic bridges.
4. Populate regime_rationale (1–2 sentences) anchored to BOTH programmatic regime and perplexity story.
5. Populate report_prose following the English guidelines below.

---

## Sector Taxonomy (US - yfinance standard names)

leading_sectors / lagging_sectors objects must cite sector buckets using:
Technology, Healthcare, Financial Services, Consumer Cyclical, Consumer Defensive,
Energy, Industrials, Basic Materials, Real Estate, Utilities, Communication Services

Industry subclusters (Semiconductors, Software…) may appear inside reason strings.

---

## Output JSON Schema

```json
{{{{
  "analysis_date": "YYYYMMDD",
  "market": "US",
  "market_regime": "{_default_regime}",
  "regime_confidence": {_default_confidence},
  "regime_rationale": "Brief explanation tying programmatic regime + perplexity cues",
  "simple_ma_regime": "{_default_simple_ma}",
  "index_summary": {_index_summary_json},
  "leading_sectors": [
    {{"sector": "Semiconductors", "reason": "...", "confidence": 0.8}}
  ],
  "lagging_sectors": [
    {{"sector": "Real Estate", "reason": "...", "confidence": 0.6}}
  ],
  "risk_events": [
    {{"event": "...", "impact": "negative", "severity": "high", "affected_sectors": ["Semiconductors"]}}
  ],
  "beneficiary_themes": [
    {{"theme": "...", "beneficiary_sectors": ["Software"], "duration": "medium_term"}}
  ],
  "report_prose": "Three to five paragraphs of formal English per guidelines below."
}}}}
```

{report_prose_guidance}

## Important Notes

- Run perplexity_ask BEFORE assembling JSON answers.
- Output MUST be compact JSON ONLY — forbid markdown wrappers / commentary wrappers.
- leading_sectors capped at five entries sorting confidence descending.
- lagging_sectors capped at five entries.
- Anti-hallucination: speculative claims must soften with uncertainty language when evidence thin.
"""

    return Agent(
        name="us_macro_intelligence_agent",
        instruction=instruction,
        server_names=["perplexity"]
    )


def _format_us_index_summary(prefetched_data: dict) -> str:
    """Format index_summary for JSON schema example."""
    if not prefetched_data:
        return '{"sp500_20d_trend": "sideways", "sp500_vs_20d_ma": "above", "sp500_4w_change_pct": 0.0, "nasdaq_20d_trend": "sideways", "vix_current": 0.0, "vix_level": "moderate"}'

    computed = prefetched_data.get("computed_regime", {})
    idx = computed.get("index_summary", {})
    if not idx:
        return '{"sp500_20d_trend": "sideways", "sp500_vs_20d_ma": "above", "sp500_4w_change_pct": 0.0, "nasdaq_20d_trend": "sideways", "vix_current": 0.0, "vix_level": "moderate"}'

    import json
    output = {
        "sp500_20d_trend": idx.get("sp500_20d_trend", "sideways"),
        "sp500_vs_20d_ma": idx.get("sp500_vs_20d_ma", "above"),
        "sp500_4w_change_pct": idx.get("sp500_4w_change_pct", 0.0),
        "nasdaq_20d_trend": idx.get("nasdaq_20d_trend", "sideways"),
        "vix_current": idx.get("vix_current", 0.0),
        "vix_level": idx.get("vix_level", "moderate"),
    }
    return json.dumps(output, ensure_ascii=False)
