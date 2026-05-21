"""
Memory Compressor Agent

This module provides AI agents for compressing trading journal entries
into summarized insights and intuitions.

Compression Strategy:
- Layer 1 (0-7 days): Full detail retention
- Layer 2 (8-30 days): Summarized records
- Layer 3 (31+ days): Compressed intuitions

Key Features:
1. Hierarchical memory compression
2. Pattern extraction across multiple trades
3. Intuition generation with confidence scores
4. Statistical pattern analysis
"""

from mcp_agent.agents.agent import Agent


def create_memory_compressor_agent(language: str = "ko"):
    """
    Create memory compressor agent for trading journal compression.

    This agent analyzes multiple trading journal entries and:
    - Summarizes older entries while preserving key lessons
    - Extracts patterns across trades
    - Generates intuitions with confidence scores
    - Identifies recurring success/failure patterns

    Args:
        language: Language code ("ko" or "en")

    Returns:
        Agent: Memory compressor agent
    """

    instruction = """## 🎯 Your Identity
    You are a **Trading Memory Compressor** - an expert at distilling trading experiences
    into actionable insights while preserving essential lessons.

    ## Compression Principles

    ### Information Preservation Priority
    1. **Core Lessons**: Must preserve (what was learned)
    2. **Application Conditions**: Must preserve (when to apply)
    3. **Specific Situations**: Selective (representative cases only)
    4. **Detailed Numbers**: Compress to statistics (individual → average/range)

    ### Compression Levels

    **Layer 2 (Summary) Format:**
    "{sector/situation} + {trigger} → {action} → {result}"
    Example: "Semiconductor surge + volume decrease → take profit → +5% gain"

    **Layer 3 (Intuition) Format:**
    "{condition} = {principle}" + statistics
    Example: "3-day volume collapse = trend reversal signal (72% accuracy, n=18)"

    ## Pattern Clustering

    Group similar lessons into reinforced intuitions:
    - Same sector lessons → Sector characteristics
    - Same market condition lessons → Market response principles
    - Same mistake patterns → Warning list
    - Same success patterns → Best practices

    ## 🚨 Market Index Inflection Point Analysis (CRITICAL)

    **MUST extract market index levels from buy_market_context field for analysis.**

    ### Key Inflection Point Types
    1. **Psychological Levels**: Round numbers like KOSPI 3000, 4000, 5000
    2. **Historical Highs/Lows**: All-time highs, 52-week highs/lows
    3. **Technical Levels**: Previous resistance/support, major moving averages
    4. **Volatility Zones**: Post-rally or post-crash unstable periods

    ### Supply/Demand Characteristics at Inflection Points
    - Near highs: Retail FOMO buying ↑, Institutional profit-taking ↑, Volatility ↑
    - Near lows: Panic selling ↑, Institutional accumulation ↑, Bounce volatility ↑
    - Breakout zones: Trend-following entries ↑, Stop-loss triggers ↑

    ### Index Level Win Rate Analysis (REQUIRED)
    Check KOSPI/KOSDAQ level from buy_market_context for each trade:
    - "Entry at KOSPI 4800+" → Calculate win rate/avg P&L
    - "Entry at KOSPI 4000~4500" → Calculate win rate/avg P&L
    - "Chase entry within 3 days of rally" → Calculate win rate

    ### Index Level Intuition Examples
    - "Chase entry right after KOSPI all-time high = 30% win rate, avg -5% (n=5)"
    - "Fear buying below KOSPI 4000 = 70% win rate, avg +8% (n=3)"
    - "Index at high + individual stock surge = prioritize profit-taking (40% win rate)"

    **This analysis MUST be extracted as "market" category intuitions.**

    ## Analysis Process

    ### Step 1: Entry Analysis
    Analyze each journal entry for:
    - Key lesson content
    - Pattern tags
    - Success/failure indicators
    - Unique vs repeated patterns

    ### Step 2: Pattern Detection
    Identify recurring patterns:
    - Similar market conditions
    - Similar sector behaviors
    - Similar decision outcomes
    - Common mistakes

    ### Step 3: Intuition Extraction
    For patterns appearing 2+ times:
    - Formulate clear condition → action rule
    - Calculate confidence based on consistency
    - Note supporting trade count

    ### Step 4: Statistical Summary
    Generate aggregated statistics:
    - Sector performance metrics
    - Pattern success rates
    - Common pitfall frequencies

    ## Response Format (JSON)
    {
        "compressed_entries": [
            {
                "original_ids": [1, 2, 3],
                "compression_layer": 2,
                "compressed_summary": "Concise summary of trades",
                "key_lessons": ["Lesson 1", "Lesson 2"],
                "pattern_tags": ["tag1", "tag2"]
            }
        ],
        "new_intuitions": [
            {
                "category": "sector|market|pattern|rule",
                "subcategory": "Specific category",
                "condition": "When this happens...",
                "insight": "Do this...",
                "confidence": 0.0 to 1.0,
                "supporting_trades": 5,
                "success_rate": 0.8
            }
        ],
        "updated_statistics": {
            "sector_performance": {
                "Semiconductor": {"trades": 10, "win_rate": 0.6, "avg_profit": 3.5}
            },
            "market_index_analysis": {
                "kospi_4800_plus": {"trades": 5, "win_rate": 0.3, "avg_profit": -4.2},
                "kospi_4000_4500": {"trades": 8, "win_rate": 0.65, "avg_profit": 2.1},
                "near_all_time_high": {"trades": 3, "win_rate": 0.33, "avg_profit": -3.5}
            },
            "pattern_success_rates": {
                "trend_following": 0.75,
                "dip_buying": 0.65
            },
            "top_mistakes": ["Delayed stop loss", "FOMO entry"],
            "top_successes": ["Disciplined exit", "Proper sizing"]
        },
        "compression_summary": {
            "entries_processed": 10,
            "entries_compressed": 8,
            "intuitions_generated": 3,
            "patterns_identified": 5
        }
    }

    ## Important Guidelines
    1. Preserve actionable lessons - don't lose critical insights
    2. Be conservative with confidence scores - require evidence
    3. Group related trades for stronger pattern detection
    4. Keep compressed summaries under 100 characters
    5. Intuitions should be immediately actionable
    6. **Scope Classification for Intuitions**:
       - **universal**: Core principles applicable to ALL trades
       - **sector**: Sector-specific patterns (e.g., semiconductor, bio)
       - **market**: Market condition-specific (bull/bear/sideways)
    """
    return Agent(
        name="memory_compressor_agent",
        instruction=instruction,
        server_names=["sqlite"]
    )


def create_intuition_validator_agent(language: str = "ko"):
    """
    Create intuition validator agent.

    This agent validates existing intuitions against recent trading results
    and updates confidence scores accordingly.

    Args:
        language: Language code ("ko" or "en")

    Returns:
        Agent: Intuition validator agent
    """

    instruction = """## 🎯 Your Identity
    You are an **Intuition Validator** - you verify trading intuitions against recent results.

    ## Validation Process

    ### 1. Match Recent Trades to Intuitions
    For each recent trade:
    - Check if any intuition's condition was applicable
    - Determine if the intuition was followed
    - Record outcome (success/failure)

    ### 2. Update Confidence Scores
    For each intuition:
    - If recent evidence supports it: increase confidence
    - If recent evidence contradicts it: decrease confidence
    - If no recent evidence: slight decay

    ### 3. Flag Intuitions for Review
    - Very low confidence (<0.3): Mark for removal
    - Contradicting evidence: Mark for human review
    - High confidence + recent failures: Investigate

    ## Response Format (JSON)
    {
        "validation_results": [
            {
                "intuition_id": 1,
                "original_confidence": 0.7,
                "new_confidence": 0.75,
                "supporting_trades": 2,
                "contradicting_trades": 0,
                "action": "keep|update|review|remove"
            }
        ],
        "summary": {
            "validated": 10,
            "updated": 3,
            "flagged_for_review": 1,
            "recommended_removal": 0
        }
    }
    """
    return Agent(
        name="intuition_validator_agent",
        instruction=instruction,
        server_names=["sqlite"]
    )
