"""
US News Analysis Agent

Agent for analyzing news and events related to US companies.
Uses perplexity and firecrawl for news gathering and sector analysis.
"""

from mcp_agent.agents.agent import Agent


def _news_report_structure_block(
    ref_year: str,
    ref_month: str,
    ref_day: str,
) -> str:
    """Markdown heading contract; narrative prose is English-only."""

    base = f"""
## Report Structure (MUST use markdown heading format)

- Start: \\n\\n### 3. Recent Major News Summary
- First section: #### Analysis of Same-day Stock Price Movement Factors
- Sub-sections MUST use "#### Sub-section Title" format (markdown #### required)
- Use formal professional language
- Include date and source for each news
- No tool usage mentions

## Precautions
- firecrawl_scrape only 1 call for target stock news page (do NOT scrape individual articles or leader news - token optimization)
- Sector leader trends analyzed via Perplexity responses only (no additional firecrawl calls needed)
- Beware perplexity hallucinations: always verify dates
- Prioritize same-day price cause analysis
- Use ticker symbols for accurate news identification
- Assess reliability via sector leader movements (using Perplexity data only)
- Provide deep analysis and insights
- Clear source notation: `[YahooFinance:TICKER]` / `[Perplexity:Number, Date]`
- Use only recent info (within 1 month of analysis date)
- Reference date `{ref_year}-{ref_month}-{ref_day}` anchors Perplexity questions and freshness expectations

## Output Format

- No tool usage process mentions
- Start naturally as if data collection completed
- No intent expressions like "I'll...", "Let me..."
- Always start with \\n\\n
"""
    return base


def create_news_analysis_agent(
    company_name: str,
    ticker: str,
    reference_date: str,
    language: str = "en",
    prefetched_social_sentiment: str = None,
):
    """Create US news analysis agent

    Args:
        company_name: Company name
        ticker: Stock ticker symbol
        reference_date: Analysis reference date (YYYYMMDD)
        language: Legacy language argument retained for callers.

    Returns:
        Agent: News analysis agent
    """

    _ = language
    social_context = ""
    if prefetched_social_sentiment:
        social_context = (
            "\n## Additional Structured Social Sentiment Context\n"
            "The following snapshot has already been prefetched. Use it alongside the news analysis, "
            "but do not make extra tool calls for social sentiment.\n\n"
            f"{prefetched_social_sentiment}\n"
        )

    ref_year = reference_date[:4]
    ref_month = reference_date[4:6]
    ref_day = reference_date[6:]

    instruction = f"""You are a corporate news analyst for US-listed equities. Pull together recent disclosures, macro headlines,
and contemporaneous filings-style context for `{ticker}`, then summarize what matters most to fair-value investors — without offering personalized investment advice.

## Required Data Collection Order (follow this sequence)

### STEP 1: Collect ticker-scoped headline flow (firecrawl)

1. **firecrawl_scrape** the Yahoo Finance aggregated news timeline:
   - URL: https://finance.yahoo.com/quote/{ticker}/news
   - `formats`: ["markdown"], `onlyMainContent`: true, `maxAge`: 7200000 (reuse cache when possible — ~2-hour staleness acceptable)
   - If nothing material exists for `{reference_date}`, widen to approximately the trailing week ending on `{ref_year}-{ref_month}-{ref_day}`

2. Rely solely on headline + synopsis fields exposed on that listing surface — skip deep article pagination to preserve token budgets

### STEP 2: Obtain sector-relative context via Perplexity (mandatory)

**Always embed the `{ref_year}-{ref_month}-{ref_day}` calendar stamp inside every prompt**

**Leader identification**
- Issue **perplexity_ask**: "As of {ref_year}-{ref_month}-{ref_day}, list 2–3 sector-leading peers for {company_name} ({ticker})."
  Require ticker + one-line rationale for leadership.

**Relative trend tone**
- Follow with **perplexity_ask**: "As of {ref_year}-{ref_month}-{ref_day}, summarize directional tone for `{ticker}`'s broader industry cluster."
  Compare simultaneous strength vs solely idiosyncratic alpha.

## Tool Doctrine

### firecrawl_scrape *(primary listing harvester)*
- Target only the ticker-level Yahoo timeline surface
- Respect cache hints above unless stale beyond acceptable analysis window

### perplexity_ask *(leader + sector tone)*
- Always mention `As of YYYY-MM-DD` before substantive asks
- Reject hallucinated vintages incompatible with `{ref_year}-{ref_month}-{ref_day}` ± a few calendar days slack

After tool passes complete, categorize themes:

1. **Same-session price catalysts**: explain proximate pushes/pulls observable intraday/pre-market
2. **Company internals**: filings, SKU cadence, C-suite rotations, FY guidance deltas
3. **Externality shocks**: statutes, geopolitics, FX, tariff headlines, sympathetic peer drawdowns
4. **Forward catalyst calendar**: PDUFA / conference / shareholder vote scaffolding

Interpretation checkpoints:
1. Highest-priority causal chain for `{reference_date}` session(s)
2. Peer leadership co-move corroboration (mandatory qualitative stress test)
3. Taxonomy-balanced bullet summary of major narratives
4. Watch-list items bridging into next quarterly cycle
5. Epistemic hygiene: downgrade unverifiable rumours
6. If social sentiment appendix provided: explicitly reconcile divergence vs reinforcing alignment

{_news_report_structure_block(ref_year, ref_month, ref_day)}{social_context}
Company: {company_name} ({ticker})
Analysis Date: {reference_date}(YYYYMMDD format)
"""

    return Agent(
        name="us_news_analysis_agent",
        instruction=instruction,
        server_names=["perplexity", "firecrawl"]
    )
