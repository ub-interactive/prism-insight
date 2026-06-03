# Trading Journal System

The Trading Journal System is a framework where an AI reviews completed trades, hierarchically compresses memory over time, and accumulates long-term trading intuition.

## Overview

### Core Concepts

```
Trade Completed → Review & Analysis → Save Journal → Time Passes → Memory Compression → Intuition Extraction
```

- **Trading Journal**: Analyzes buy/sell context at the end of each trade and extracts actionable lessons.
- **Memory Compression**: Step-by-step summary of older journals to optimize storage space and retrieval efficiency.
- **Trading Intuitions**: Rules extracted from recurring patterns, used to inform future buy decisions.

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Stock Tracking Agent                         │
│                    (stock_tracking_agent.py)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌───────────────────┐    ┌──────────────┐ │
│  │ Sell Executed │───>│ write_trading_    │───>│trading_journal│ │
│  │              │    │ journal()         │    │    Table     │ │
│  └──────────────┘    └───────────────────┘    └──────────────┘ │
│         │                    │                       │          │
│         │                    ▼                       │          │
│         │           ┌───────────────────┐            │          │
│         │           │ trading_journal_  │            │          │
│         │           │ agent.py          │            │          │
│         │           │ (AI Review)       │            │          │
│         │           └───────────────────┘            │          │
│         │                                            │          │
│         │    ┌───────────────────────────────────────┘          │
│         │    │                                                  │
│         ▼    ▼                                                  │
│  ┌──────────────────┐    ┌───────────────────┐                 │
│  │ compress_old_    │───>│ memory_compressor_│                 │
│  │ journal_entries()│    │ agent.py          │                 │
│  └──────────────────┘    │ (AI Compression)  │                 │
│         │                └───────────────────┘                 │
│         │                        │                              │
│         ▼                        ▼                              │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ Compressed   │         │trading_      │                     │
│  │ Journals     │         │intuitions    │                     │
│  │ (Layer 2,3)  │         │   Table      │                     │
│  └──────────────┘         └──────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Trading Journal Agent (`src/prism/core/agents/trading_journal_agent.py`)

Invoked immediately after a sell execution to perform a retrospective trade review.

#### Main Functions
- Comparative analysis of the buy vs. sell market contexts.
- Evaluation of trade timing quality (buy score vs. exit timing).
- Extraction of actionable lessons.
- Assignment of pattern tags for future query retrieval.

#### Response Format
```json
{
    "situation_analysis": {
        "buy_context_summary": "Summary of market/stock situation when buying",
        "sell_context_summary": "Summary of market/stock situation when selling",
        "key_changes": ["Key Change 1", "Key Change 2"]
    },
    "judgment_evaluation": {
        "buy_quality": "Appropriate / Inappropriate / Neutral",
        "sell_quality": "Appropriate / Premature / Delayed / Neutral",
        "missed_signals": ["Missed Signals"],
        "overreacted_signals": ["Overreacted Signals"]
    },
    "lessons": [
        {
            "condition": "Under this condition...",
            "action": "We should act like this...",
            "reason": "Because...",
            "priority": "high / medium / low"
        }
    ],
    "pattern_tags": ["post_surge_adjustment", "delayed_stop_loss"],
    "one_line_summary": "One-line summary of the trade",
    "confidence_score": 0.8
}
```

#### Example Pattern Tags

| Category | Example Tags |
|---------|----------|
| Market Context | `bull_market_entry`, `bear_market_stop_loss`, `sideways_market_hold` |
| Stock Patterns | `pullback_after_surge`, `box_breakout`, `volume_drop`, `support_line_rebound` |
| Misjudgments | `delayed_stop_loss`, `premature_profit_take`, `news_overreliance`, `panic_sell` |
| Successful Moves | `trend_following`, `dip_buy`, `rule_compliance`, `correct_sizing` |

### 2. Memory Compressor Agent (`src/prism/core/agents/memory_compressor_agent.py`)

Hierarchically compresses historical journals as time progresses to manage context limits.

#### Memory Layers

| Layer | Age Range | Content |
|-------|-----------|---------|
| Layer 1 | 0 - 7 days | Detailed original logs (unchanged) |
| Layer 2 | 8 - 30 days | Formatted summary: `"{Sector} + {Trigger} → {Action} → {Result}"` |
| Layer 3 | 31+ days | Abstracted intuition: `"{Condition} = {Principle}"` + statistics |

#### Layer 2 Summary Example
```
"Semiconductors Surge + Volume Drop → Profit Taken → Return +5%"
"Biotech Theme + Overheated News → No Buy → Avoided Correction"
```

#### Layer 3 Intuition Example
```
"3 consecutive days of volume drop = Trend reversal signal (Accuracy 72%, n=18)"
"5% rise within 2 days after surge = Overheating warning (Accuracy 65%, n=12)"
```

### 3. Compression Script (`compress_trading_memory.py`)

A command-line script to run the hierarchical memory compression.

#### Usage

```bash
# Standard execution
python compress_trading_memory.py

# Dry-run (verify without committing changes)
python compress_trading_memory.py --dry-run

# Custom age thresholds
python compress_trading_memory.py --layer1-age 7 --layer2-age 30

# Force execution (ignore minimum entries requirement)
python compress_trading_memory.py --force
```

#### CLI Arguments

| Option | Default | Description |
|------|--------|------|
| `--db-path` | `var/stock_tracking_db.sqlite` | SQLite database path |
| `--layer1-age` | 7 | Threshold days to compress Layer 1 to 2 |
| `--layer2-age` | 30 | Threshold days to compress Layer 2 to 3 |
| `--min-entries` | 3 | Minimum entries required to trigger compression |
| `--dry-run` | - | Verify changes without saving to database |
| `--force` | - | Ignore the minimum entries threshold |
| `--language` | en | Language configuration for the agent (en/ko) |

#### Cron Configuration (Recommended)

```bash
# Executed every Sunday at 3:00 AM
0 3 * * 0 cd /path/to/prism-insight && python compress_trading_memory.py >> logs/compression.log 2>&1
```

## Database Schema

### `trading_journal` Table

```sql
CREATE TABLE trading_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Basic Trade Info
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    trade_type TEXT NOT NULL,  -- 'buy' or 'sell'

    -- Buy Context
    buy_price REAL,
    buy_date TEXT,
    buy_scenario TEXT,         -- JSON: Buy Scenario
    buy_market_context TEXT,   -- JSON: Market Context at Buy

    -- Sell Context
    sell_price REAL,
    sell_reason TEXT,
    profit_rate REAL,
    holding_days INTEGER,

    -- AI Review Results
    situation_analysis TEXT,   -- JSON: Situation Analysis
    judgment_evaluation TEXT,  -- JSON: Judgment Evaluation
    lessons TEXT,              -- JSON: List of Lessons
    pattern_tags TEXT,         -- JSON: Pattern Tags
    one_line_summary TEXT,     -- Short summary string
    confidence_score REAL,     -- Confidence score (0 to 1)

    -- Compression Metadata
    compression_layer INTEGER DEFAULT 1,  -- 1: Detailed, 2: Summary, 3: Intuition
    compressed_summary TEXT,   -- Summarized string for Layer 2+

    -- Timestamps
    created_at TEXT NOT NULL,
    last_compressed_at TEXT
);

-- Indexes
CREATE INDEX idx_journal_ticker ON trading_journal(ticker);
CREATE INDEX idx_journal_pattern ON trading_journal(pattern_tags);
CREATE INDEX idx_journal_date ON trading_journal(trade_date);
```

### `trading_intuitions` Table

```sql
CREATE TABLE trading_intuitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Categorization
    category TEXT NOT NULL,    -- sector, market, pattern, rule
    subcategory TEXT,          -- Sub-classification (e.g. Technology)

    -- Intuition Data
    condition TEXT NOT NULL,   -- Condition: "Under these circumstances..."
    insight TEXT NOT NULL,     -- Insight: "We should do this..."
    confidence REAL,           -- Confidence score (0 to 1)

    -- Historical Support
    supporting_trades INTEGER, -- Number of supporting trades
    success_rate REAL,         -- Historical success rate
    source_journal_ids TEXT,   -- JSON: Source journal IDs

    -- Status
    created_at TEXT NOT NULL,
    last_validated_at TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE INDEX idx_intuitions_category ON trading_intuitions(category);
```

## Practical Mappings

### 1. Retrieve Historical Lessons at Entry

```python
# Automatically invoked inside stock_tracking_agent.py
context = agent._get_relevant_journal_context(
    ticker="AAPL",
    sector="Technology"
)

adjustment, reasons = agent._get_score_adjustment_from_context(
    ticker="AAPL",
    sector="Technology"
)

# Example output values:
# adjustment = -0.5  (Subtract score due to consecutive historical losses)
# reasons = ["Same ticker: 3 consecutive losses (-8%, -9%, -10%)"]
```

### 2. Monitor Compression Stats

```python
stats = agent.get_compression_stats()
# {
#     "entries_by_layer": {
#         "layer1_detailed": 15,
#         "layer2_summarized": 45,
#         "layer3_compressed": 120
#     },
#     "active_intuitions": 28,
#     "oldest_uncompressed": "2026-01-15",
#     "avg_intuition_confidence": 0.72,
#     "avg_intuition_success_rate": 0.68
# }
```

### 3. Query Active Intuitions

```python
# Fetch top 5 active insights for tech sector
agent.cursor.execute("""
    SELECT condition, insight, confidence, success_rate
    FROM trading_intuitions
    WHERE subcategory = 'Technology' AND is_active = 1
    ORDER BY confidence DESC
    LIMIT 5
""")
```

## Verification

```bash
# Execute unit tests
pytest tests/test_trading_journal.py -v

# Run integration checks
python tests/test_trading_journal.py
```

## Performance Tracker Feedback Loop (Self-Improving Trading)

The primary value of the Trading Journal is creating a **self-improving feedback loop** where past trade outcomes automatically refine future buy/sell scoring decisions.

### Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Self-Improving Trading Cycle                      │
│                                                                      │
│   ① Buy Decision                      ② Sell Completed               │
│   ┌──────────┐                      ┌──────────┐                    │
│   │ LLM      │  ──── Holding ────>  │ AI       │                    │
│   │ evaluates│                      │ Review   │                    │
│   │ buy_score│                      └────┬─────┘                    │
│   └────┬─────┘                           │                           │
│        ▲                                 ▼                           │
│        │                          ③ Store & Compress                 │
│        │                          ┌──────────────┐                   │
│        │                          │ Layer 1 (Det)│                   │
│        │                          │ Layer 2 (Sum)│                   │
│        │                          │ Layer 3 (Int)│                   │
│        │                          └──────┬───────┘                   │
│        │                                 │                           │
│        │         ④ Feedback Path         │                           │
│        │         ┌───────────────────────┘                           │
│        │         ▼                                                   │
│        │  ┌─────────────────┐                                        │
│        │  │ Performance     │                                        │
│        │  │ Tracker         │                                        │
│        │  │ (Stats)         │                                        │
│        │  └────────┬────────┘                                        │
│        │           │                                                 │
│        │           ▼                                                 │
│        │  ┌─────────────────┐                                        │
│        │  │ Journal Context │                                        │
│        │  │ + Score Adj.    │                                        │
│        └──│ → LLM Prompt    │                                        │
│           └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Feeding Stats Back to Decisions

The Performance Tracker (`us_analysis_performance_tracker` table) tracks the 7/14/30-day outcomes of analyzed stocks. This information is injected into the buy prompt:

```python
# 1. Journal Manager queries win rate statistics for specific triggers
stats = journal_manager._get_performance_tracker_stats(trigger_type="intraday_surge")
# Output: {"win_rate": 0.72, "total": 15, "avg_30d": 0.032}

# 2. Format context details
context = journal_manager.get_context_for_ticker(ticker, sector, trigger_type)
# Output: "This trigger (intraday_surge): Win rate 72% (n=15), 30d avg return +3.2%"

# 3. Request score adjustment advice
adjustment, reasons = journal_manager.get_score_adjustment(ticker, sector, trigger_type)
# Output: (2, ["trigger win rate 72% above 65% threshold"])

# 4. Inject variables inside prompt context in _extract_trading_scenario
prompt = f"""
### Current Portfolio Status:
{portfolio_info}
### Trading Value Analysis:
{rank_change_msg}
{score_adjustment_info}    # Score Adjustments
{journal_context}          # Win rate & past trade experiences

### Report Content:
{report_content}
"""
```

### Memory Hierarchy Mapping to Prompts

Layer 1/2/3 represent **storage structures**. Before being injected into LLM prompts, they are processed into contextual representations:

```
Layer 1 (Detailed Journal) ──Compress──> Layer 2 (Summary) ──Compress──> Layer 3 (Intuition)
       │                                     │                              │
       ▼                                     ▼                              ▼
  Same Stock History                 Universal Principles           Trading Intuitions
  (History on same ticker)           (General principles)           (Recognized patterns)
       │                                     │                              │
       └──────────────────────────────┬──────┴──────────────────────────────┘
                                      ▼
                           Consolidated context string
                                      ▼
                        "### Past Trading Experience Reference"
                              Injected to LLM prompt
```

- **Same Stock History**: Fetches the last 3 trades on the same ticker directly from Layer 1.
- **Universal Principles**: Generates rules extracted from Layer 2 to Layer 3 transitions (where scope is 'universal').
- **Trading Intuitions**: Collects active rules matching the target sector or trigger in Layer 3.

### Prompt Injections Breakdown

| Item | Source | Purpose | Decision Influence |
|------|--------|---------|--------------------|
| **Trigger Win Rate** | Performance Tracker | Historic accuracy of the trigger type | High win rate increases score |
| **Trigger Ranking** | Performance Tracker | Top 5 triggers performance ranking | Relative comparison reference |
| **Score Adjustment** | Performance Tracker + Journal | Suggested score modifier (-3 to +3) | LLM reference (optional) |
| **Same Stock History** | Layer 1 (Short-term) | Outlines last 3 trades on this ticker | Avoids repeating similar exit/timing mistakes |
| **Universal Principles** | Layer 2→3 (Mid to Long-term) | Top 5 validated rules (`supporting_trades >= 2`) | Standard decision support checks |
| **Trading Intuitions** | Layer 3 (Long-term) | Abstracted conditions → insights | References contextual intuition patterns |

### Expected Output Tuning

| Trigger Win Rate | Information for LLM | Expected Action |
|------------|----------------|-----------|
| >65% (Strong Trigger) | "Win rate 72% (n=15)" | Promotes BUY decision |
| 35% - 65% (Normal) | "Win rate 48% (n=20)" | Neutral decision (LLM evaluates manually) |
| <35% (Weak Trigger) | "Win rate 28% (n=8)" | Demotes BUY decision |
| n < 3 (Low Data) | (Omitted from prompt) | No influence |

## References

| Paper / Resource | Feature Influence |
|------|----------|
| [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413) (2025) | Layer 1→2→3 memory compression, key information extraction |
| [Human-inspired Episodic Memory for Infinite Context LLMs](https://arxiv.org/abs/2407.09450) (2024) | Trade review structure, episodic recall |
| [Memory in the Age of AI Agents: A Survey](https://arxiv.org/abs/2512.13564) (2025) | Core memory agent architecture and lifecycle |
