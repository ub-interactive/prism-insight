# Common Tasks - PRISM-INSIGHT

> **Note**: Task playbooks. Overview: [CURSOR.md](../CURSOR.md) · [AGENTS.md](../AGENTS.md).

---

## Task 1: Adding a New AI Agent

```python
# 1. Create agent file
# File: src/prism/core/agents/your_agent.py

from mcp_agent import Agent

def create_your_agent(company_name, company_code, reference_date, language="en"):
    _ = language
    instruction = """Your English instruction..."""

    return Agent(
        instruction=instruction,
        description=f"Your Agent for {company_name}",
        mcp_servers=["yahoo_finance"],  # Add required MCP servers
    )

# 2. Register in src/prism/core/agents/__init__.py
from .your_agent import create_your_agent

def get_agent_directory(...):
    agents = {
        # ... existing agents
        "your_section": lambda: create_your_agent(...),
    }
    return agents

# 3. Add to base_sections in src/prism/core/analysis.py
base_sections = [
    "price_volume_analysis",
    # ... existing sections
    "your_section",  # Add your section
]

# 4. Add section template in src/prism/core/report_generation.py
section_templates = {
    # ... existing templates
    "your_section": """
## Your Section Title

{content}
""",
}
```

---

## Task 2: Modifying Surge Detection Criteria

```python
# File: trigger_batch.py

def detect_surge_stocks(mode="morning"):
    # Modify thresholds
    VOLUME_THRESHOLD = 2.0  # Change: Volume surge ratio
    GAP_THRESHOLD = 3.0     # Change: Price gap percentage
    MIN_MARKET_CAP = 1000   # Change: Minimum market cap (billion KRW)

    # Add custom filters
    filtered_stocks = df[
        (df['volume_ratio'] >= VOLUME_THRESHOLD) &
        (df['gap_percent'] >= GAP_THRESHOLD) &
        (df['market_cap'] >= MIN_MARKET_CAP) &
        (df['your_custom_condition'])  # Add custom condition
    ]

    return filtered_stocks
```

---

## Task 3: Adding Multi-Language Support

1. Extend templates in `src/prism/core/config/language.py` (or whichever localized template helper your section uses).

2. Run the orchestrator with an explicit `--language` flag:

```bash
python -m prism.ops.pipelines.stock_analysis_orchestrator --mode morning --language en
```

3. If you localize weekly digests, adapt your notifier / Firebase bridge payloads instead of coupling to a proprietary chat SDK.


---

## Task 4: Modifying Trading Strategy

```python
# File: src/prism/core/agents/trading_agents.py

def create_trading_scenario_agent(...):
    instruction = """
    Trading Scenario Generation Instructions:

    BUY SCORE CRITERIA (Modify these):
    - Valuation (PER, PBR vs peers): 0-3 points
    - Technical Momentum: 0-3 points
    - News Catalyst: 0-2 points
    - Market Environment: 0-2 points
    - TOTAL: 10 points (buy threshold: 6+)

    RISK MANAGEMENT (Modify these):
    - Stop Loss: -5% to -7% (change percentage)
    - Target Price: +10% to +30% (change percentage)
    - Risk/Reward Ratio: Min 2:1 (change ratio)

    PORTFOLIO CONSTRAINTS (Modify these):
    - Max positions: 10 (change number)
    - Max same sector: 3 (change number)
    - Sector concentration: 30% (change percentage)
    """
    return Agent(instruction=instruction, ...)

# Apply changes
# 1. Modify instruction text
# 2. Update stock_tracking_agent.py if needed
# 3. Test with quick_test.py
```

---

## Task 5: Customizing Report Format

```python
# File: src/prism/core/report_generation.py

# 1. Modify report template
REPORT_TEMPLATE = """
# {company_name} ({company_code}) Investment Analysis Report

**Analysis Date**: {reference_date}
**Analyst**: PRISM-INSIGHT AI Agent System
**Language**: {language}

---

## Your Custom Section

{custom_content}

---

{sections}

---

## Investment Strategy

{investment_strategy}

---

**Disclaimer**: {disclaimer}
"""

# 2. Add custom sections
def generate_full_report(section_reports, investment_strategy, ...):
    custom_content = generate_custom_section(...)

    report = REPORT_TEMPLATE.format(
        company_name=company_name,
        custom_content=custom_content,
        sections=format_sections(section_reports),
        investment_strategy=investment_strategy,
        ...
    )
    return report
```

---

## Task 6: Adding New MCP Server

```bash
# 1. Install MCP server
npm install -g your-mcp-server
# or
pip install your-mcp-server
```

```yaml
# 2. Add to mcp_agent.config.yaml
mcp:
  servers:
    your_server: npx your-mcp-server
    # or
    your_server: python3 -m your_mcp_server
```

```bash
# 3. Put vendor keys in `.env` (never commit):
# FIRECRAWL_API_KEY=...
# PERPLEXITY_API_KEY=...
```

```python
# 4. Use in agent
def create_your_agent(...):
    return Agent(
        instruction="...",
        mcp_servers=["your_server"],  # Add your server
    )
```


---

## Task 7: Trading Memory Compression & Cleanup

```bash
# Weekly memory compression with cleanup (recommended for cron)
python compress_trading_memory.py

# Preview changes without executing
python compress_trading_memory.py --dry-run

# Skip cleanup phase (compression only)
python compress_trading_memory.py --skip-cleanup

# Custom cleanup thresholds
python compress_trading_memory.py \
    --max-principles 30 \
    --max-intuitions 30 \
    --stale-days 60 \
    --archive-days 180
```

**Cleanup thresholds:**
- `max-principles`: 50 (default) - Maximum active principles
- `max-intuitions`: 50 (default) - Maximum active intuitions
- `stale-days`: 90 (default) - Deactivate unvalidated items
- `archive-days`: 365 (default) - Delete old Layer 3 journals


---

## Task 8: Lessons to Principles Migration

```bash
# Migrate trading_journal lessons to trading_principles table

# Preview migration
python tools/migrate_lessons_to_principles.py --dry-run

# Execute migration
python tools/migrate_lessons_to_principles.py
```

**What it does:**
- Extracts high-priority lessons as universal principles
- Links principles to source journal entries
- Sets appropriate scope (universal/sector/market)

---

*See also: [CURSOR.md](../CURSOR.md) | [agent-reference.md](agent-reference.md) | [troubleshooting.md](troubleshooting.md)*
