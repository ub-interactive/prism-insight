# Trigger Batch Algorithms Document

> **Last Updated**: 2026-03-11
> **Version**: 4.0 (v2.5.3)
> **File**: `trigger_batch.py`
> **Purpose**: Auto-screening for breakout/momentum symbols + macro-linked hybrid selection

---

## Table of Contents

1. [Overview](#1-overview)
2. [Common Filters](#2-common-filters)
3. [Morning Triggers](#3-morning-triggers)
4. [Afternoon Triggers](#4-afternoon-triggers)
5. [Composite Score Calculation](#5-composite-score-calculation)
6. [Criteria by Trigger Type (v1.16.6)](#6-criteria-by-trigger-type-v1166)
7. [Agent Fit Score Calculation (v1.16.6)](#7-agent-fit-score-calculation-v1166)
8. [Hybrid Selection](#8-hybrid-selection)
9. [Top-down + Bottom-up Hybrid Selection (v2.5.3)](#9-top-down-plus-bottom-up-hybrid-selection-v253)
10. [Final Selection Logic (select_final_tickers)](#10-final-selection-logic-select_final_tickers)
11. [Usage](#11-usage)

---

## 1. Overview

### Purpose

`trigger_batch.py` runs every morning and afternoon to automatically screen for **watchlist candidates**. The selected symbols are then passed to the AI analysis pipeline (`stock_analysis_orchestrator.py`).

### Core Objectives (v2.5.3)

- Screen symbols to achieve an **annual average return of 15%**
- Ensure **complete consistency between `trigger_batch` and `trading_agent`**
- Operational under all market conditions (bull/bear/sideways markets)
- **Macroeconomic regime alignment**: Top-down (leading sectors) + Bottom-up (signals) hybrid selection

### Execution Flow

```
macro_intelligence_agent.py (Macro Analysis: regime, leading_sectors, sector_map)
    ↓
trigger_batch.py (Symbol Screening + Hybrid Top-down/Bottom-up Selection)
    ↓
stock_analysis_orchestrator.py (AI Analysis)
    ↓
stock_tracking_agent.py (Buy/Sell Decisions)
    ↓
trading/stock_trading.py (Actual Orders)
```

### Data Sources

- **yahoo_finance / sec_edgar**: US market and filing context
- **Snapshot Data**: OHLCV (Open, High, Low, Close, Volume, Trading Value)
- **Market Cap Data**: Market capitalization per symbol

---

## 2. Common Filters

These are basic filters applied to all triggers.

### 2.1 Absolute Criteria Filter (`apply_absolute_filters`)

| Filter | Criteria | Purpose |
|------|------|------|
| Min Trading Value | **10 billion KRW or more** (or $100M USD for US market) | Ensure liquidity (strengthened in v1.16.6) |
| Min Volume | At least 20% of the market average | Active trading symbols |

```python
def apply_absolute_filters(df, min_value=10000000000):  # 10 billion KRW
    filtered = df[df['Amount'] >= min_value]
    avg_volume = df['Volume'].mean()
    filtered = filtered[filtered['Volume'] >= avg_volume * 0.2]
    return filtered
```

### 2.2 Market Cap Filter (v1.16.6 Change)

| Filter | Criteria | Purpose |
|------|------|------|
| Min Market Cap | **500 billion KRW or more** | Ensure liquidity, institutional interest (increased in v1.16.6) |

```python
snap = snap[snap["시가총액"] >= 500000000000]  # 500 billion KRW
```

### 2.3 Price Change Rate Filter (v1.16.6 New)

| Filter | Criteria | Purpose |
|------|------|------|
| Max Price Change | **20% or less** | Exclude limit-up/overheated symbols |

```python
snap = snap[snap["전일대비등락률"] <= 20.0]
```

### 2.4 Low Liquidity Filter (`filter_low_liquidity`)

Exclude symbols in the bottom N% of trading volume (Default: 20%).

---

## 3. Morning Triggers

The morning batch runs **after the market opens** and selects a total of 3 symbols, one from each of the 3 triggers.

### 3.1 Top Volume Surge Symbols (`trigger_morning_volume_surge` / "Volume Surge Top")

**Purpose**: Capture symbols with a sudden surge in volume compared to the previous day.

#### Screening Conditions

| Condition | Criteria |
|------|------|
| Volume Increase Rate | 30% or more compared to the previous day |
| Price Trend | Current price is higher than open price |
| Trading Value | 10 billion KRW or more |
| Market Cap | 500 billion KRW or more |
| Price Change Rate | 20% or less |

#### Composite Score

```
Composite Score = Volume Increase Rate (60%) + Absolute Volume (40%)
```

---

### 3.2 Top Gap-Up Momentum Symbols (`trigger_morning_gap_up_momentum` / "Gap Up Momentum Top")

**Purpose**: Capture momentum symbols that start with a gap-up.

#### Screening Conditions

| Condition | Criteria |
|------|------|
| Gap-Up Rate | 1% or more compared to the previous day's close |
| Price Trend | Current price > Open price |
| Trading Value | 10 billion KRW or more |
| Market Cap | 500 billion KRW or more |
| Price Change Rate | 20% or less |

#### Composite Score

```
Composite Score = Gap-Up Rate (50%) + Intraday Price Change (30%) + Trading Value (20%)
```

---

### 3.3 Top Capital Inflow to Market Cap Ratio Symbols (`trigger_morning_value_to_cap_ratio` / "Value-to-Cap Ratio Top")

**Purpose**: Capture symbols with abnormally high trading value relative to their market capitalization.

#### Screening Conditions

| Condition | Criteria |
|------|------|
| Trading Value Ratio | Trading Value / Market Cap |
| Price Trend | Current price is higher than open price |
| Trading Value | 10 billion KRW or more |
| Market Cap | 500 billion KRW or more |
| Price Change Rate | 20% or less |

#### Composite Score

```
Composite Score = Trading Value Ratio (50%) + Absolute Trading Value (30%) + Intraday Price Change (20%)
```

---

## 4. Afternoon Triggers

The afternoon batch runs **after the market closes** and selects a total of 3 symbols, one from each of the 3 triggers.

### 4.1 Top Daily Gainers (`trigger_afternoon_daily_rise_top` / "Intraday Rise Top")

**Purpose**: Capture the strongest rising symbols of the day.

#### Screening Conditions

| Condition | Criteria |
|------|------|
| Price Change Rate | Between 3% and 20% |
| Trading Value | 10 billion KRW or more |
| Market Cap | 500 billion KRW or more |

#### Composite Score

```
Composite Score = Intraday Price Change (60%) + Trading Value (40%)
```

---

### 4.2 Top Closing Strength Symbols (`trigger_afternoon_closing_strength` / "Closing Strength Top")

**Purpose**: Capture symbols that close near their session highs (strong close).

#### Screening Conditions

| Condition | Criteria |
|------|------|
| Closing Strength | (Close - Low) / (High - Low) |
| Volume Increase | Volume increase compared to the previous day |
| Price Trend | Close price is higher than open price |
| Trading Value | 10 billion KRW or more |
| Market Cap | 500 billion KRW or more |

#### Closing Strength Calculation

```python
ClosingStrength = (Close - Low) / (High - Low)
# Closer to 1 indicates a stronger close (Close ≈ High)
# Closer to 0 indicates a weaker close (Close ≈ Low)
```

#### Composite Score

```
Composite Score = Closing Strength (50%) + Volume Increase Rate (30%) + Trading Value (20%)
```

---

### 4.3 Top Flat Price Volume Surge Symbols (`trigger_afternoon_volume_surge_flat` / "Volume Surge Sideways")

**Purpose**: Capture symbols with surging trading volume but flat prices (suspected institutional accumulation).

#### Screening Conditions

| Condition | Criteria |
|------|------|
| Volume Increase Rate | 50% or more compared to the previous day |
| Price Trend | Price change within ±5% of previous day's close |
| Trading Value | 10 billion KRW or more |
| Market Cap | 500 billion KRW or more |

#### Composite Score

```
Composite Score = Volume Increase Rate (60%) + Trading Value (40%)
```

---

## 5. Composite Score Calculation

### Normalization Method

All indicators are normalized between 0 and 1:

```python
normalized = (value - min) / (max - min)
```

### Weight Application

```python
CompositeScore = Σ (normalized_indicator × weight)
```

---

## 6. Criteria by Trigger Type (v1.16.6)

These are the target risk-reward and stop-loss limit criteria per trigger type, synchronized with `trading_agents.py`.

```python
TRIGGER_CRITERIA = {
    "Volume Surge Top": {"rr_target": 1.2, "sl_max": 0.05},
    "Gap Up Momentum Top": {"rr_target": 1.2, "sl_max": 0.05},
    "Intraday Rise Top": {"rr_target": 1.2, "sl_max": 0.05},
    "Closing Strength Top": {"rr_target": 1.3, "sl_max": 0.05},
    "Value-to-Cap Ratio Top": {"rr_target": 1.3, "sl_max": 0.05},
    "Volume Surge Sideways": {"rr_target": 1.5, "sl_max": 0.07},
    "default": {"rr_target": 1.5, "sl_max": 0.07}
}
```

| Trigger Type | Risk-Reward Target | Max Stop-Loss |
|------------|-----------|--------|
| Volume Surge Top | 1.2+ | 5% |
| Gap Up Momentum Top | 1.2+ | 5% |
| Intraday Rise Top | 1.2+ | 5% |
| Closing Strength Top | 1.3+ | 5% |
| Value-to-Cap Ratio Top | 1.3+ | 5% |
| Volume Surge Sideways | 1.5+ | 7% |

---

## 7. Agent Fit Score Calculation (v1.16.6)

### Key Change: Fixed Stop-Loss Method

In v1.16.6, the stop-loss price calculation method was changed from a **10-day support line baseline** to a **fixed percentage relative to the current price**.

#### Reason for Change

```
[Previous Issues]
- Stop-loss price calculated based on the 10-day low → Resulted in 48%+ stop-loss range for high-flying symbols.
- Inconsistency with agent criteria (-5% to -7%) → Sharp drop in agent_fit_score → No trade entry.

[Solution]
- Fixed at Current Price × (1 - sl_max) → Always satisfies agent criteria.
```

### Current Calculation Method (v1.16.6)

```python
def calculate_agent_fit_metrics(ticker, current_price, trade_date, lookback_days=10, trigger_type=None):
    # Query trigger criteria
    criteria = TRIGGER_CRITERIA.get(trigger_type, TRIGGER_CRITERIA["default"])
    sl_max = criteria["sl_max"]  # 5% or 7%
    rr_target = criteria["rr_target"]  # 1.2 ~ 1.5

    # Key: Fixed stop-loss method
    stop_loss_price = current_price * (1 - sl_max)
    stop_loss_pct = sl_max  # Always 5% or 7%

    # Target price: 10-day resistance line (minimum +15% guaranteed)
    multi_day_df = get_multi_day_ohlcv(ticker, trade_date, lookback_days)
    target_price = multi_day_df["High"].max()

    # Mitigate remaining risk: Guarantee minimum +15% target
    min_target = current_price * 1.15
    if target_price < min_target:
        target_price = min_target

    # Calculate risk-reward ratio
    risk_reward_ratio = (target_price - current_price) / (current_price - stop_loss_price)

    # Agent score (simplified)
    rr_score = min(risk_reward_ratio / rr_target, 1.0)
    sl_score = 1.0  # Fixed stop-loss, so always full points

    agent_fit_score = rr_score * 0.6 + sl_score * 0.4
```

### Score Calculation Formulas

| Item | Formula | Description |
|------|------|------|
| Risk-Reward Score | `min(R:R / rr_target, 1.0)` | Full points when target is met |
| Stop-Loss Score | `1.0` (Fixed) | Always within criteria |
| Agent Score | `rr_score × 0.6 + sl_score × 0.4` | Weighted towards risk-reward |

### Effects

| Metric | v1.16.5 | v1.16.6 |
|------|---------|---------|
| Stop-Loss Range | 0% ~ 50%+ (Variable) | 5% ~ 7% (Fixed) |
| agent_fit_score | 0.03 ~ 0.9 | 0.7 ~ 1.0 |
| Agent Approval Rate | Low | Significantly improved |

---

## 8. Hybrid Selection

### Purpose

The previous composite score method selects "the most active symbols today," but they might not fit the agent's criteria. Hybrid selection selects symbols that align better with the agent's requirements.

### Final Score Calculation (v1.16.6)

```python
FinalScore = CompositeScore(Normalized) × 0.3 + AgentScore × 0.7
```

> The agent score weight has been increased from 60% to 70% in v1.16.6.

### Selection Flow

```
1. Select the top 10 candidates from each trigger.
2. Retrieve 10-day OHLCV data for each candidate.
3. Calculate the agent score (fixed stop-loss method).
4. Final Score = Composite Score (30%) + Agent Score (70%).
5. Select the top-ranked symbol by final score from each trigger.
```

### Impact Example

| Symbol | Composite Score | Agent Score | Final Score | Risk-Reward | Stop-Loss |
|------|---------|------------|---------|-------|-------|
| Hanwha Systems | 0.82 | 1.00 | **1.00** | 3.0 | 5.0% |
| Gigavis | 0.76 | 1.00 | **1.00** | 3.0 | 5.0% |
| SK Telecom | 0.14 | 1.00 | **1.00** | 2.1 | 7.0% |

→ All symbols satisfy the agent criteria due to the fixed stop-loss.

---

## 9. Top-down + Bottom-up Hybrid Selection (v2.5.3)

### Background

The previous `select_final_tickers` used a purely bottom-up approach. It detected candidates based on trigger signals (surges, volume) and selected the Top 3 based on composite_score/final_score rankings. The only macro integration was a ±0.1 score adjustment for leading/lagging sectors, which was too negligible compared to the base scores to have any real impact.

In v2.5.3, a top-down channel was added to directly reflect leading sector information from the macroeconomic analysis (`macro_intelligence_agent`) into the symbol selection.

### Architecture

```
macro_context (Macro Analysis Results)
├── market_regime: "strong_bull" | "moderate_bull" | "sideways" | "moderate_bear" | "strong_bear"
├── leading_sectors: [{"sector": "Technology", "confidence": 0.9}, ...]
├── lagging_sectors: [{"sector": "Construction", "confidence": 0.7}, ...]
└── sector_map: {"AAPL": "Technology", "TSLA": "Consumer Cyclical", ...}

                    ┌──────────────────┐
                    │  Trigger Candidates│
                    │  (Top 10 of each) │
                    └────────┬─────────┘
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │  Top-down Pool   │        │  Bottom-up Pool  │
    │ leading_sectors  │        │ (Keep Legacy)    │
    │ Matching Filter  │        │ Top 1 per trigger│
    │ + confidence wgt │        │ + fill by score  │
    └────────┬─────────┘        └────────┬─────────┘
              │                           │
              └─────────┬─────────────────┘
                        ▼
               ┌──────────────────┐
               │Regime Slot Alloc │
               │(Top-down N+Btm M)│
               └────────┬─────────┘
                        ▼
               ┌──────────────────┐
               │Final 3 Selected  │
               └──────────────────┘
```

### Top-down Pool Construction (`_build_topdown_pool`)

Filters symbols matching `leading_sectors` among the trigger candidates and amplifies their scores using the sector confidence.

```
topdown_score = base_score × (1 + sector_confidence × 0.3)
```

- `base_score`: Existing `final_score` or `composite_score`
- `sector_confidence`: Confidence level of the sector (0.0~1.0) in the `leading_sectors` of `macro_context`
- Amplification is based on the existing score, so no new scoring system is introduced.

**Sector Matching**: Prefers exact matches, using fuzzy substring matching as a defense mechanism. This acts as a safety guard in case the LLM deviates from the `sector_taxonomy`.

```python
# US Sectors: yfinance GICS 11 sectors (Technology, Healthcare, etc.)
```

### Slot Allocation by Regime (`_get_regime_slots`)

| Regime | Top-down | Bottom-up | Rationale |
|--------|--------|--------|------|
| `strong_bull` | **2** | 1 | In a bull market, **sector rotation is a key driver of returns**. Since symbols in leading sectors are structurally more advantageous than non-leading sector symbols, sector betting is strengthened with 2 top-down symbols. |
| `moderate_bull` | 1 | **2** | Upward trend but lacks strong conviction. Reflects macro signals with 1 top-down symbol while hedging individual momentum with 2 bottom-up symbols. |
| `sideways` | 1 | **2** | In a sideways market, **individual breakout/volume signals are more reliable** than overall sector movements. Only 1 top-down symbol is kept. |
| `moderate_bear` | 1 | **2** | In a moderate bear market, the macro agent's `leading_sectors` naturally shift to **defensive sectors (Utilities, Healthcare, Consumer Staples)**. Having 1 top-down symbol for defensive sector rotation is beneficial for managing downside risk. |
| `strong_bear` | 0 | **3** | In a strong bear market, **any sector can decline**. Sector betting itself is risky, so it relies purely on bottom-up technical signals (reversals, volume anomalies) of individual symbols. |
| (Unrecognized) | 1 | **2** | Unrecognized regimes fall back to the `sideways` default. |

> **Design Decision (ADR)**: A score multiplier approach (Option B) was also considered. However, given max_selections=3, a slot-based allocation was chosen because it allows clear tracking of "why this symbol was selected," which is highly beneficial for operation and debugging. A multiplier approach, being an extension of the legacy ±0.1 adjustment, risked repeating the same issue of opacity.

### 3-Step Selection Process

**Phase 1 — Filling Top-down Slots**
1. Sort the top-down pool in descending order of `topdown_score`.
2. Select as many symbols as the top-down slot count allocated by the regime.
3. Tag the selected symbols with `SelectionChannel = "top-down"`.

**Phase 2 — Filling Bottom-up Slots**
1. Follow the existing logic: Select the top 1 symbol per trigger.
2. Exclude symbols already selected in Phase 1.
3. Tag the selected symbols with `SelectionChannel = "bottom-up"`.

**Phase 3 — Remaining Backfill**
1. If fewer than 3 symbols are selected, backfill using overall candidate scores.
2. If there are insufficient candidates in the top-down pool, the remaining slots are automatically allocated to bottom-up.

### Fallback (Safety Measures)

| Scenario | Behavior |
|------|------|
| `macro_context = None` | 100% bottom-up (Identical to existing behavior, no regression) |
| `leading_sectors` is empty | 100% bottom-up |
| `sector_map` is empty | 100% bottom-up |
| Top-down candidates < allocated slots | Automatically backfill remaining slots using bottom-up |
| `market_regime` unrecognized | `sideways` default (1 top-down + 2 bottom-up) |

### Observability

**Log Output**:
```
[TOP-DOWN] 005930 selected (sector=전기·전자, score=1.016, trigger=Volume Surge Top)
[BOTTOM-UP] 051910 selected (trigger=Gap Up Momentum Top)
[BOTTOM-UP] 003490 selected (fill, trigger=Intraday Rise Top)
Selection summary: 1 top-down + 2 bottom-up = 3 total (regime=moderate_bull, strategy=hybrid_topdown_bottomup)
```

**JSON metadata**:
```json
{
  "selection_strategy": "hybrid_topdown_bottomup",
  "market_regime": "moderate_bull",
  "topdown_slots": 1,
  "bottomup_slots": 2,
  "topdown_count": 1,
  "bottomup_count": 2
}
```

**selection_channel per symbol**: Include `"selection_channel": "top-down"` or `"bottom-up"` in each symbol's JSON output.

### Canonical US Notes

| Item | US (`trigger_batch.py`) |
|------|-------------------------|
| Score Column | `CompositeScore`, `FinalScore` |
| Sector Source | `get_us_sector_map()` via yfinance (GICS 11 sectors) |
| Company Name Column | `CompanyName` |
| Sector Examples | Technology, Healthcare, Financial Services |

---

## 10. Final Selection Logic (`select_final_tickers`)

1. Gather the top 10 candidates from each trigger.
2. Hybrid mode: Calculate agent scores using 10-day data.
3. **Build the top-down pool**: `leading_sectors` matching + confidence weighting (v2.5.3).
4. **Slot allocation by regime**: Top-down N + Bottom-up M = 3 (v2.5.3).
5. Phase 1: Fill top-down slots.
6. Phase 2: Fill bottom-up slots (Top 1 per trigger).
7. Phase 3: Remaining backfill (by overall score).
8. Remove duplicate symbols, tag SelectionChannel.

---

## 11. Usage

### Basic Execution

```bash
# Morning batch
python trigger_batch.py morning INFO

# Afternoon batch
python trigger_batch.py afternoon INFO
```

### Options

```bash
# Save JSON results
python trigger_batch.py afternoon INFO --output result.json

# Debug mode
python trigger_batch.py afternoon DEBUG
```

### Output Example (JSON, v2.5.3)

```json
{
  "Intraday Rise Top": [
    {
      "code": "272210",
      "name": "Hanwha Systems",
      "current_price": 88700.0,
      "change_rate": 14.16,
      "volume": 14393649,
      "trade_value": 1220949944400.0,
      "agent_fit_score": 1.0,
      "risk_reward_ratio": 3.0,
      "stop_loss_pct": 5.0,
      "stop_loss_price": 84265.0,
      "target_price": 102005.0,
      "final_score": 1.0,
      "selection_channel": "top-down"
    }
  ],
  "Closing Strength Top": [
    {
      "code": "420770",
      "name": "Gigavis",
      "current_price": 40050.0,
      "change_rate": 18.49,
      "closing_strength": 0.93,
      "agent_fit_score": 1.0,
      "risk_reward_ratio": 3.0,
      "stop_loss_pct": 5.0,
      "final_score": 1.0,
      "selection_channel": "bottom-up"
    }
  ],
  "Volume Surge Sideways": [
    {
      "code": "017670",
      "name": "SK Telecom",
      "current_price": 54300.0,
      "change_rate": 2.45,
      "agent_fit_score": 1.0,
      "risk_reward_ratio": 2.14,
      "stop_loss_pct": 7.0,
      "final_score": 1.0,
      "selection_channel": "bottom-up"
    }
  ],
  "metadata": {
    "run_time": "2026-03-11T09:30:00",
    "trigger_mode": "afternoon",
    "trade_date": "20260311",
    "selection_mode": "hybrid",
    "lookback_days": 10,
    "selection_strategy": "hybrid_topdown_bottomup",
    "market_regime": "moderate_bull",
    "topdown_slots": 1,
    "bottomup_slots": 2,
    "topdown_count": 1,
    "bottomup_count": 2
  }
}
```

---

## Appendix: Function List

| Function Name | Category | Description |
|--------|----------|------|
| `get_snapshot` | Data | Retrieve current day OHLCV |
| `get_previous_snapshot` | Data | Retrieve previous day OHLCV |
| `get_multi_day_ohlcv` | Data | Retrieve N-day OHLCV data per symbol |
| `get_market_cap_df` | Data | Retrieve market cap details |
| `apply_absolute_filters` | Filter | Absolute criteria filter (10B KRW+) |
| `filter_low_liquidity` | Filter | Low liquidity filter |
| `normalize_and_score` | Scoring | Normalization and composite scoring |
| `calculate_agent_fit_metrics` | Scoring | Agent criteria scoring (v1.16.6 fixed stop-loss) |
| `score_candidates_by_agent_criteria` | Scoring | Batch calculation of agent scores for candidates |
| `enhance_dataframe` | Utility | Add symbol names/sectors |
| `_get_regime_slots` | Selection | regime → (top-down, bottom-up) slot mapping (v2.5.3) |
| `_build_topdown_pool` | Selection | Build top-down pool matching leading_sectors + confidence weighting (v2.5.3) |
| `trigger_morning_volume_surge` | Morning | Volume surge trigger |
| `trigger_morning_gap_up_momentum` | Morning | Gap-up momentum trigger |
| `trigger_morning_value_to_cap_ratio` | Morning | Capital inflow relative to market cap trigger |
| `trigger_afternoon_daily_rise_top` | Afternoon | Daily rise top trigger |
| `trigger_afternoon_closing_strength` | Afternoon | Closing strength trigger |
| `trigger_afternoon_volume_surge_flat` | Afternoon | Flat price volume surge trigger |
| `select_final_tickers` | Selection | Final top-down + bottom-up hybrid selection (v2.5.3) |
| `get_us_sector_map` | Data | US symbol → GICS sector mapping (US only) |
| `run_batch` | Execution | Execute batch pipeline |

---

**Document Version**: 4.0
**Last Updated**: 2026-03-11
**Author**: PRISM-INSIGHT Development Team
