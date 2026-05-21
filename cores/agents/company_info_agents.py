"""
US Company Information Analysis Agents

Agents for fundamental analysis of US companies.
Uses yfinance prefetched data for comprehensive financial analysis.

All financial data (valuation, income statement, balance sheet, cash flow,
analyst estimates, institutional holdings) is pre-collected via yfinance and
injected into agent instructions. No MCP server tools are needed when data
is fully prefetched.
"""

from mcp_agent.agents.agent import Agent
from typing import Dict


def create_company_status_agent(
    company_name: str,
    ticker: str,
    reference_date: str,
    urls: Dict[str, str],
    language: str = "ko",
    prefetched_data: dict = None
):
    """Create US company status analysis agent

    Args:
        company_name: Company name
        ticker: Stock ticker symbol
        reference_date: Analysis reference date (YYYYMMDD)
        urls: Dictionary of Yahoo Finance URLs
        language: Language code (default: "ko")

    Returns:
        Agent: Company status analysis agent
    """

    title_heading = (
        f"### 2-1. 기업 현황 분석: {company_name}"
        if language == "ko"
        else f"### 2-1. Company Status Analysis: {company_name}"
    )
    prose_rule = (
        "Write all narrative prose in formal polite Korean (합쇼체: ~입니다 / ~합니다). "
        "Do not use informal/plain endings (~한다 / ~된다)."
        if language == "ko"
        else "Write analytical narrative in clear professional English."
    )

    instruction = f"""You are a company status analyst for US-listed equities. Pull structured fundamentals from Yahoo Finance (Key Statistics / Financials / Analyst views) unless pre-collected data blocks were injected later.
When scraping pages with firecrawl_scrape use formats=["markdown"] and onlyMainContent=true.

## Data Collection Discipline

- Prefer tabular payloads over illustrative charts wherever possible — tables carry greater numeric fidelity
- Aim for granular, reproducible datapoints spanning valuation, profitability, liquidity, outlook, positioning

## Data to Collect

### 1. From Yahoo Finance Key Statistics Page (URL: {urls['key_statistics']}):
   - Valuation Measures: Market Cap, Enterprise Value, Trailing P/E, Forward P/E, PEG Ratio, Price/Sales, Price/Book, Enterprise Value/Revenue, Enterprise Value/EBITDA
   - Financial Highlights: Profit Margin, Operating Margin, Return on Assets, Return on Equity, Revenue, Net Income, Diluted EPS
   - Trading Information: Beta, 52-Week High/Low, 50-Day Moving Average, 200-Day Moving Average, Avg Vol (3 month), Shares Outstanding, Float, Short Ratio

### 2. From Yahoo Finance Financials Page (URL: {urls['financials']}):
   - Income Statement: Revenue, Operating Expense, Net Income (annual and quarterly)
   - Balance Sheet: Total Assets, Total Liabilities, Stockholders' Equity
   - Cash Flow: Operating Cash Flow, Investing Cash Flow, Financing Cash Flow, Free Cash Flow

### 3. From Yahoo Finance Analysis Page (URL: {urls['analysis']}):
   - Earnings Estimates: Current Qtr, Next Qtr, Current Year, Next Year estimates
   - Revenue Estimates: Current Qtr, Next Qtr, Current Year, Next Year estimates
   - EPS Trends: Current and past estimates
   - Analyst Recommendations: Buy/Hold/Sell ratings, Target Price

### 4. From yahoo_finance MCP Server:
   - Use tool call(name: yahoo_finance-get_stock_info) with ticker="{ticker}"
   - Use tool call(name: yahoo_finance-get_recommendations) with ticker="{ticker}", recommendation_type="recommendations"

## Analysis Direction (what to weave into the narrative backbone)
1. Company snapshot + differentiated business mechanics (keep tight — deeper narrative belongs to Overview agent downstream)
   - Competitive moat & addressable wedge vs peers
2. Multi-year financial trajectory (prioritize last ~4 FY reporting cycles if available end-to-end via Yahoo export)
   - Operating / net-margin evolution; quarterly volatility & seasonality; surprise vs consensus dynamics
3. Valuation scaffolding (trail + forward multiples) benchmarked historically + vs rough sector composites when inferable without hallucinating proprietary datasets
4. Balance-sheet / liquidity / leverage stress vignettes anchored to reported metrics
5. Street positioning: consensus price targets, dispersion, directional drift vs spot
6. Institutional float / accumulation clues from Yahoo-holder snapshots feeding into positioning overlay

## Report Structure (Markdown contract)
- Lead with TWO blank lines THEN the fixed title line verbatim (language-specific constraint below)
- Subsections deepen via markdown `####` depth (avoid mixing `#` / `##` inside this artifact)
- Table-wrap dense KPI panels; bullets summarize table → thesis linkages crisply
- All quoted monetary bands / accounting figures expressed in USD for cross-border comparability

**Fixed title line (verbatim):** {title_heading}

## Tone & Editorial Guardrails
- Balance institutional precision with discretionary-retail readability
- When ambiguous, annotate confidence states explicitly (“appears”, “possibly”, directional language)
- No personalized solicitation — articulate scenario scaffolding only
- {prose_rule}

## Operational Safeguards
- Only cite metrics surfaced from artefacts you actually scraped / retrieved / prefetched
- Avoid substantive overlap mission with sibling `company overview` — fundamentals > long-form corporate biography here

## Output Hygiene (post-tool stage)
- Never narrate crawler / MCP choreography inside final publication — imitate polished desk memo
- No conversational intent (“I'll…”, “Let's query…”). Begin cold analytical substance once heading anchors land

Issuer: `{company_name} ({ticker})`
Stamp: `{reference_date}` (YYYYMMDD)
"""

    # Inject prefetched data: replace firecrawl key-statistics/financials + yahoo_finance MCP with pre-collected data
    pf = prefetched_data or {}
    has_prefetch = bool(pf.get("stock_info"))
    has_analysis = bool(pf.get("analysis_estimates"))

    if has_prefetch and has_analysis:
        # Full prefetch - no firecrawl needed
        prefetch_block = f"""## Pre-collected Data (Company Status)
The following data has been pre-collected via yfinance. Use this data directly for analysis.
DO NOT scrape any Yahoo Finance pages. DO NOT call any MCP tools.

{pf['stock_info']}
{pf.get('recommendations', '')}

### Analysis Estimates Data

{pf.get('analysis_estimates', '')}

### Financial Statements Data

{pf.get('financial_statements', '')}
"""
        # Inject prefetch block into instruction
        start_marker = "## Data to Collect"
        end_marker = "## Analysis Direction"
        start_idx = instruction.find(start_marker)
        end_idx = instruction.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            instruction = instruction[:start_idx] + prefetch_block + "\n" + instruction[end_idx:]
    elif has_prefetch:
        # Partial prefetch - still need Analysis page firecrawl
        prefetch_block = f"""## Pre-collected Data (Company Status)
The following data has been pre-collected via yfinance. Use this data directly for analysis.
DO NOT scrape Key Statistics or Financials pages. DO NOT call yahoo_finance MCP tools.

{pf['stock_info']}
{pf.get('recommendations', '')}

## Additional Data to Collect

### 1. Yahoo Finance Analysis Page (URL: {urls['analysis']}):
   - Earnings Estimates: Current Qtr, Next Qtr, Current Year, Next Year estimates
   - Revenue Estimates: Current Qtr, Next Qtr, Current Year, Next Year estimates
   - EPS Trends: Current and past estimates
   - Analyst Recommendations: Buy/Hold/Sell ratings, Target Price
"""
        # Replace English data section
        start_marker = "## Data to Collect"
        end_marker = "## Analysis Direction"
        start_idx = instruction.find(start_marker)
        end_idx = instruction.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            instruction = instruction[:start_idx] + prefetch_block + "\n" + instruction[end_idx:]

    # Server selection based on prefetch status
    if has_prefetch and has_analysis:
        # Full prefetch - no MCP servers needed
        servers = []
    elif has_prefetch:
        # Partial prefetch - still need firecrawl for Analysis page
        servers = ["firecrawl"]
    else:
        # No prefetch - need firecrawl and yahoo_finance
        servers = ["firecrawl", "yahoo_finance"]

    return Agent(
        name="us_company_status_agent",
        instruction=instruction,
        server_names=servers
    )


def create_company_overview_agent(
    company_name: str,
    ticker: str,
    reference_date: str,
    urls: Dict[str, str],
    language: str = "ko",
    prefetched_data: dict = None
):
    """Create US company overview analysis agent

    Args:
        company_name: Company name
        ticker: Stock ticker symbol
        reference_date: Analysis reference date (YYYYMMDD)
        urls: Dictionary of Yahoo Finance URLs
        language: Language code (default: "ko")

    Returns:
        Agent: Company overview analysis agent
    """


    title_heading = (
        f"### 2-2. 기업 개요 분석: {company_name}"
        if language == "ko"
        else f"### 2-2. Company Overview Analysis: {company_name}"
    )
    prose_rule = (
        "Write all narrative prose in formal polite Korean (합쇼체: ~입니다 / ~합니다). "
        "Do not use informal/plain endings (~한다 / ~된다)."
        if language == "ko"
        else "Write analytical narrative in clear professional English."
    )

    instruction = f"""You are an equity-sector cartographer profiling US-listed issuers strictly from factual Yahoo artefacts (Profile/Holders overlays) unless yfinance blobs were prefetched downstream.
Operational posture: disciplined firecrawl invocations (`formats=["markdown"], onlyMainContent=true`) — minimise decorative chart imagery; tables > hero images for signal density.

## Data to Collect

### 1. From Yahoo Finance Profile Page (Access URL: {urls['profile']}):
   - Company Description: Business summary, sector, industry
   - Key Executives: Names, titles, compensation
   - Company Address and Contact
   - Number of Full-Time Employees

### 2. From Yahoo Finance Holders Page (Access URL: {urls['holders']}):
   - Major Holders: Insider ownership %, Institutional ownership %
   - Top Institutional Holders: Names, shares held, % of outstanding
   - Top Mutual Fund Holders

## Analysis Direction — narrative scaffolding
1. Firm genesis chronology · HQ geography · leadership bench depth
2. Segment / SKU / services map + directional revenue/geo mix cues (only when tabulated cleanly)
3. Operational scale proxies (employee counts, capex anecdotes if disclosed)
4. Positioning mosaic vs named peers WHEN Yahoo profile copy supports non-speculative rivalry framing
5. Stewardship primitives: board skeletal facts, insider alignment %, headline comp philosophy if tabular
6. Avoid duplicating the fundamental ratio drill-down reserved for Status agent — contextualize, don't compete

## Report Structure — markdown contract (non-negotiable)
- Exactly two newline characters BEFORE the mandated title `{title_heading}` anchors the dossier boundary
- All interior depth escalation uses `####` — never escalate to `# / ##` prematurely (downstream parsers assume shallow stack)
- Table-first summarization encouraged for KPI-style facts; bullets bridge qualitative implications
**Fixed title line (verbatim):** {title_heading}

## Style & neutrality posture
- {prose_rule}
- Accessible yet professional — hedge fund PM skimming shouldn't cringe at fluff, retail shouldn't choke on jargon
- Epistemic honesty: visibly qualify inference chains ("suggests", "consistent with")

## Operational guardrails / hallucination chokepoints
- If a datapoint absent from artefacts → explicitly mark data void instead of extrapolating
- No solicitation tone — illuminate trade-offs don't whisper entries

## Output hygiene
- FINAL surface must NEVER narrate crawler steps / MCP choreography — imitate polished evergreen profile memo
- No intent chatter prelude — plunge post-title straight into synthesized insight

Ticker context: `{company_name} ({ticker})`
Chrono anchor: `{reference_date}` (`YYYYMMDD`)
"""

    # Inject prefetched data: replace firecrawl profile/holders pages with pre-collected data
    pf = prefetched_data or {}
    has_prefetch = bool(pf.get("company_profile"))

    if has_prefetch:
        holder_data = pf.get('holder_info', '')
        segment_data = pf.get('segment_revenue', '')
        prefetch_block = f"""## Pre-collected Data (Company Overview)
The following data has been pre-collected via yfinance. Use this data directly for analysis.
DO NOT scrape Profile, Holders pages via firecrawl. DO NOT call any MCP tools.

{pf['company_profile']}
{f"### Institutional Holdings Data{chr(10)}{chr(10)}{holder_data}" if holder_data else ""}
{f"{chr(10)}{segment_data}" if segment_data else ""}
"""
        start_marker = "## Data to Collect"
        end_marker = "## Analysis Direction"
        start_idx = instruction.find(start_marker)
        end_idx = instruction.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            instruction = instruction[:start_idx] + prefetch_block + "\n" + instruction[end_idx:]

    # When prefetched: no MCP servers needed
    if has_prefetch:
        servers = []
    else:
        servers = ["firecrawl", "yahoo_finance"]

    return Agent(
        name="us_company_overview_agent",
        instruction=instruction,
        server_names=servers
    )
