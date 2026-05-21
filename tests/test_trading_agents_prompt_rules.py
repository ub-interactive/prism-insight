"""Prompt-rule regression tests for the KR trading scenario agent.

These tests lock down the structural invariants of the strategist prompt so
that future edits cannot silently drop the CAN SLIM identity, the fundamental
gate, the market-regime matrix, the No-Entry justification rules, or the
prohibited expressions list.

Tests assert *prompt content*, not LLM output — they catch unintended prompt
drift, not modeling regressions.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cores.agents.trading_agents import create_trading_scenario_agent


# --- Identity & framework -------------------------------------------------

def test_identity_is_can_slim_only_en():
    agent = create_trading_scenario_agent(language="en")
    assert "creator of the CAN SLIM system" in agent.instruction
    assert "NOT value-investing" in agent.instruction


def test_can_slim_framework_present_en():
    agent = create_trading_scenario_agent(language="en")
    for element in ("C — Current quarter", "A — Annual earnings", "N — New",
                    "S — Supply/Demand", "L — Leader", "I — Institutional sponsorship",
                    "M — Market direction"):
        assert element in agent.instruction


# --- Fundamental gate -----------------------------------------------------

def test_fundamental_gate_four_checks_en():
    agent = create_trading_scenario_agent(language="en")
    assert "Step 1 — Fundamental Gate (mandatory)" in agent.instruction
    for check in ("F1 Profitability", "F2 Balance sheet", "F3 Growth", "F4 Business clarity"):
        assert check in agent.instruction


# --- Market-regime matrix (single source of truth) ------------------------

def test_market_regime_matrix_values_en():
    agent = create_trading_scenario_agent(language="en")
    for row in (
        "| strong_bull   | 4 | 1.0 | -7% | 1+ | 0 |",
        "| moderate_bull | 4 | 1.2 | -7% | 1+ | 0 |",
        "| sideways      | 5 | 1.3 | -6% | 1+ | 0 |",
        "| moderate_bear | 5 | 1.5 | -5% | 2+ | 1 |",
        "| strong_bear   | 6 | 1.8 | -5% | 2+ | 1 |",
    ):
        assert row in agent.instruction, f"missing matrix row: {row}"


def test_min_score_schema_matches_matrix_en():
    agent = create_trading_scenario_agent(language="en")
    assert "strong_bull:4, moderate_bull:4, sideways:5, moderate_bear:5, strong_bear:6" in agent.instruction


# --- No-Entry justification ----------------------------------------------

def test_no_entry_standalone_reasons_en():
    agent = create_trading_scenario_agent(language="en")
    assert "**Standalone (any one is sufficient):**" in agent.instruction
    assert "Stop loss support is at -10% or worse" in agent.instruction
    assert "PER ≥ 2.5× industry average" in agent.instruction
    assert "Fundamental Gate fail in sideways / bear regime" in agent.instruction
    assert 'severity risk event' in agent.instruction
    assert "effective_score < min_score" in agent.instruction


def test_prohibited_expressions_en():
    agent = create_trading_scenario_agent(language="en")
    for forbidden in ("overheating concern", "inflection signal",
                      "needs more confirmation", "short-term correction risk",
                      "wait and see is safer"):
        assert forbidden in agent.instruction


# --- Decision rule and macro adjustment -----------------------------------

def test_decision_rule_uses_effective_score_en():
    agent = create_trading_scenario_agent(language="en")
    assert "effective_score ≥ min_score" in agent.instruction
    assert "NOT folded into buy_score" in agent.instruction
    assert "effective_score = buy_score + macro_adjustment" in agent.instruction


# --- JSON schema must include the new gates -------------------------------

def test_json_schema_has_required_keys_en():
    agent = create_trading_scenario_agent(language="en")
    for key in ('"fundamental_check":', '"buy_score":', '"macro_adjustment":',
                '"effective_score":', '"min_score":', '"momentum_signal_count":',
                '"additional_confirmation_count":', '"decision":'):
        assert key in agent.instruction


# --- Sector constraint substitution still works ---------------------------

def test_sector_constraint_applied_en():
    agent = create_trading_scenario_agent(language="en",
                                           sector_names=["Semiconductors", "Biotech"])
    assert "Semiconductors, Biotech" in agent.instruction
    assert "{sector_constraint}" not in agent.instruction


# --- Restored content: trigger detail / portfolio guide / perplexity / R/R / checklist ---

def test_macro_sector_leader_detail_present_en():
    agent = create_trading_scenario_agent(language="en")
    assert "**Macro Sector Leader trigger — analysis points:**" in agent.instruction
    assert "weigh the medium-term tailwind from the sector" in agent.instruction


def test_contrarian_value_detail_present_en():
    agent = create_trading_scenario_agent(language="en")
    assert "**Contrarian Value Stock trigger — analysis points:**" in agent.instruction
    assert "earnings deterioration / loss of competitive edge" in agent.instruction


def test_portfolio_analysis_guide_present_en():
    agent = create_trading_scenario_agent(language="en")
    assert "## Portfolio Analysis Guide" in agent.instruction
    for item in ("Current number of holdings", "Sector distribution",
                 "Investment-period distribution", "Portfolio average return"):
        assert item in agent.instruction


def test_perplexity_detail_present_en():
    agent = create_trading_scenario_agent(language="en")
    assert "major peer competitors valuation comparison" in agent.instruction
    assert "Include the current date" in agent.instruction


def test_rr_formula_present_en():
    agent = create_trading_scenario_agent(language="en")
    assert "## R/R Calculation (reference)" in agent.instruction
    assert "expected_return_pct = (target_price - current_price)" in agent.instruction


def test_entry_checklist_passed_in_schema_en():
    agent = create_trading_scenario_agent(language="en")
    assert '"entry_checklist_passed":' in agent.instruction


# --- Anti-loophole: "ambiguous → No Entry" loophole removed ---------------

def test_ambiguous_setup_no_longer_auto_no_entry_en():
    agent = create_trading_scenario_agent(language="en")
    assert "name the *specific* uncertainty in the rationale" in agent.instruction
    assert '"Vague concern" is not allowed as a No Entry reason' in agent.instruction


# --- v2.12.0: Parabolic regime + target_price fallback + DD kill switch ---

def test_parabolic_regime_row_in_matrix_en():
    agent = create_trading_scenario_agent(language="en")
    assert "| parabolic     | 4 | 0.7 | -7% | 1+ | 0 |" in agent.instruction


def test_parabolic_activation_conditions_en():
    agent = create_trading_scenario_agent(language="en")
    assert "KOSPI 90-day return ≥ +30%" in agent.instruction
    assert "KOSPI 30-day return ≥ +10%" in agent.instruction
    assert "Daily Rise Top / Closing Strength / Gap Up Momentum" in agent.instruction
    assert 'excludes** "Volume Surge" and' in agent.instruction


def test_distribution_day_kill_switch_en():
    agent = create_trading_scenario_agent(language="en")
    assert "Distribution Day Kill Switch" in agent.instruction
    assert "distribution days" in agent.instruction
    assert "parabolic → strong_bull" in agent.instruction


def test_target_price_fallback_rule_en():
    agent = create_trading_scenario_agent(language="en")
    assert "current_price × 1.05" in agent.instruction
    assert "report target is stale" in agent.instruction
    assert "80% of the distance" in agent.instruction


def test_parabolic_position_sizing_en():
    agent = create_trading_scenario_agent(language="en")
    assert "Parabolic position management" in agent.instruction
    assert "Do NOT reduce slots" in agent.instruction
    assert "use the report-derived max_portfolio_size as-is" in agent.instruction


def test_parabolic_min_score_in_schema_en():
    agent = create_trading_scenario_agent(language="en")
    assert "parabolic:4" in agent.instruction
