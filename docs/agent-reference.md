# AI Agent System - PRISM-INSIGHT

> **Note**: Detailed AI agent reference. Overview: [CURSOR.md](../CURSOR.md) and [AGENTS.md](../AGENTS.md).
>
---

## Specialized Agents

Orchestration order and filenames are authoritative in [`CURSOR.md`](../CURSOR.md). Sections below supplement that with narrative detail.

### Analysis Team (6 Agents) - GPT-5 Based

<img src="images/aiagent/technical_analyst.jpeg" alt="Technical Analyst" width="150" align="right"/>

**1. Technical Analyst** (`create_price_volume_analysis_agent`)
- **File**: `src/prism/core/agents/stock_price_agents.py`
- **Purpose**: Stock price and volume technical analysis
- **Analyzes**: Trends, moving averages, support/resistance, RSI, MACD, Bollinger Bands
- **Output**: Technical analysis section of report

<br clear="both"/>

<img src="images/aiagent/tranding_flow_analyst.jpeg" alt="Trading Flow Analyst" width="150" align="right"/>

**2. Trading Flow Analyst** (`create_investor_trading_analysis_agent`)
- **File**: `src/prism/core/agents/stock_price_agents.py`
- **Purpose**: Investor trading pattern analysis
- **Analyzes**: Institutional/foreign/individual trading flows, volume patterns
- **Output**: Trading flow section

<br clear="both"/>

<img src="images/aiagent/financial_analyst.jpeg" alt="Financial Analyst" width="150" align="right"/>

**3. Financial Analyst** (`create_company_status_agent`)
- **File**: `src/prism/core/agents/company_info_agents.py`
- **Purpose**: Financial metrics and valuation
- **Analyzes**: PER, PBR, ROE, debt ratio, target prices, consensus
- **Output**: Company status section

<br clear="both"/>

<img src="images/aiagent/industry_analyst.jpeg" alt="Industry Analyst" width="150" align="right"/>

**4. Industry Analyst** (`create_company_overview_agent`)
- **File**: `src/prism/core/agents/company_info_agents.py`
- **Purpose**: Business model and competitive position
- **Analyzes**: Business portfolio, market share, competitors, R&D, growth drivers
- **Output**: Company overview section

<br clear="both"/>

<img src="images/aiagent/information_analyst.jpeg" alt="Information Analyst" width="150" align="right"/>

**5. Information Analyst** (`create_news_analysis_agent`)
- **File**: `src/prism/core/agents/news_strategy_agents.py`
- **Purpose**: News and catalyst identification
- **Analyzes**: Recent news, disclosures, industry trends, political/economic issues
- **Output**: News analysis section

<br clear="both"/>

<img src="images/aiagent/market_analyst.jpeg" alt="Market Analyst" width="150" align="right"/>

**6. Market Analyst** (`create_market_index_analysis_agent`)
- **File**: `src/prism/core/agents/market_index_agents.py`
- **Purpose**: Market and macro environment
- **Analyzes**: S&P 500/NASDAQ indices, macro indicators, global correlations
- **Output**: Market analysis section
- **Note**: Results are cached to reduce API calls

<br clear="both"/>

### Strategy Team (1 Agent) - GPT-5 Based

<img src="images/aiagent/investment_strategist.jpeg" alt="Investment Strategist" width="150" align="right"/>

**7. Investment Strategist** (`create_investment_strategy_agent`)
- **File**: `src/prism/core/agents/news_strategy_agents.py`
- **Purpose**: Synthesize all analyses into actionable strategy
- **Integrates**: All 6 analysis reports
- **Output**: Investment strategy with recommendations for different investor types

<br clear="both"/>

### Auxiliary messaging workflows (retired)

Optional assistants that rewrote summaries for auxiliary distribution rails are not bundled in this repo.
Use your own notifier or the optional Firebase Bridge; FCM payloads use ``report_link`` / ``pdf_report_link``
for any deep/asset links supplied by callers.

### Trading Simulation Team (3 Agents) - GPT-5 Based

> **Note**: All agents now use GPT-5 (gpt-5) as the default model. GPT-5 output formatting requires additional cleanup in `cores/utils.py` (tool artifacts, headers).

<img src="images/aiagent/buy_specialist.jpeg" alt="Buy Specialist" width="150" align="right"/>

**9-1. Buy Specialist** (`create_trading_scenario_agent`)
- **File**: `src/prism/core/agents/trading_agents.py`
- **Purpose**: Buy decision-making and entry strategy
- **Evaluates**: Valuation, momentum, portfolio constraints
- **Market-Adaptive Criteria**:
  - Bull Market: Min score 6, Risk/Reward ≥ 1.5, Stop loss ≤ 10%
  - Bear/Sideways: Min score 7, Risk/Reward ≥ 2.0, Stop loss ≤ 7%
- **Output**: JSON trading scenario with entry/exit strategy

<br clear="both"/>

<img src="images/aiagent/sell_specialist.jpeg" alt="Sell Specialist" width="150" align="right"/>

**9-2. Sell Specialist** (`create_sell_decision_agent`)
- **File**: `src/prism/core/agents/trading_agents.py`
- **Purpose**: Monitor holdings and determine sell timing
- **Monitors**: Stop-loss, profit targets, technical trends, market conditions
- **Output**: JSON sell decision with confidence score

<br clear="both"/>

**9-3. Trading Journal Agent** (Optional)
- **File**: `src/prism/core/agents/trading_journal_agent.py` (invoked from `stock_tracking_agent.py` when enabled)
- **Purpose**: Retrospective trade analysis and long-term memory accumulation
- **Features**:
  - Buy/sell context comparison and lesson extraction
  - Hierarchical memory compression (detailed → summary → intuition)
  - Buy score adjustment based on past experience
- **Activation**: Set `ENABLE_TRADING_JOURNAL=true` in `.env`
- **Details**: [TRADING_JOURNAL.md](TRADING_JOURNAL.md)

<br clear="both"/>

---

## Agent Collaboration Pattern

```python
# Pattern in cores/analysis.py
async def analyze_stock(company_name, company_code, reference_date, language="en"):
    # 1. Get agent directory
    agents = get_agent_directory(company_name, company_code, reference_date,
                                  base_sections, language)

    # 2. Sequential execution (rate limit friendly)
    section_reports = {}
    for section in base_sections:
        if section in agents:
            agent = agents[section]

            # Special handling for market analysis (use cache)
            if section == "market_index_analysis":
                report = get_cached_or_generate_market_analysis(...)
            else:
                report = await generate_report(agent, section, ...)

            section_reports[section] = report

    # 3. Generate investment strategy (integrates all reports)
    strategy = await generate_investment_strategy(
        agents["investment_strategy"],
        section_reports,
        ...
    )

    return {
        "sections": section_reports,
        "strategy": strategy
    }
```

---

## Creating New Agents

**Template Pattern**:

```python
# File: src/prism/core/agents/your_agent.py
from mcp_agent import Agent

def create_your_agent(company_name, company_code, reference_date, language="en"):
    """
    Create your custom agent.

    Args:
        company_name: Company name
        company_code: Stock code
        reference_date: Analysis date (YYYY-MM-DD)
        language: Report language (English only: ``en``)

    Returns:
        Agent instance
    """
    _ = language
    instruction = """
    You are a specialized analyst focusing on [YOUR DOMAIN].

    Analyze the stock data and provide:
    1. [Specific point 1]
    2. [Specific point 2]

    Be concise and data-driven.
    """

    return Agent(
        instruction=instruction,
        description=f"Custom Agent for {company_name}",
        # Add MCP tools if needed
        mcp_servers=["yahoo_finance", "firecrawl", "perplexity"],
    )

# Register in src/prism/core/agents/__init__.py
def get_agent_directory(...):
    agents = {
        # ... existing agents
        "your_section_name": lambda: create_your_agent(...),
    }
    return agents
```

---

*See also: [CURSOR.md](../CURSOR.md) | [tasks-reference.md](tasks-reference.md) | [troubleshooting.md](troubleshooting.md)*
