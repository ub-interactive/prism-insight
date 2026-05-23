"""Prompt-rule regression tests for the US trading scenario agent."""

from prism.core.agents.trading_agents import create_trading_scenario_agent


def test_identity_is_can_slim_only_en():
    agent = create_trading_scenario_agent(language="en")
    assert "creator of the CAN SLIM system" in agent.instruction
    assert "NOT value-investing" in agent.instruction


def test_market_regime_uses_sp500_vix_en():
    agent = create_trading_scenario_agent(language="en")
    assert "S&P 500 (^GSPC)" in agent.instruction
    assert "VIX < 18" in agent.instruction
    assert "VIX > 25" in agent.instruction


def test_fundamental_gate_and_matrix_present_en():
    agent = create_trading_scenario_agent(language="en")
    assert "Step 1 — Fundamental Gate (mandatory)" in agent.instruction
    assert "Step 2 — Market-Regime Entry Matrix" in agent.instruction
    for row in (
        "| parabolic     | 4 | 0.7 | -7% | 1+ | 0 |",
        "| strong_bull   | 4 | 1.0 | -7% | 1+ | 0 |",
        "| moderate_bull | 4 | 1.2 | -7% | 1+ | 0 |",
        "| sideways      | 5 | 1.3 | -6% | 1+ | 0 |",
        "| moderate_bear | 5 | 1.5 | -5% | 2+ | 1 |",
        "| strong_bear   | 6 | 1.8 | -5% | 2+ | 1 |",
    ):
        assert row in agent.instruction


def test_no_entry_forbidden_expressions_present_en():
    agent = create_trading_scenario_agent(language="en")
    for forbidden in (
        "overheating concern",
        "inflection signal",
        "needs more confirmation",
        "short-term correction risk",
        "wait and see is safer",
    ):
        assert forbidden in agent.instruction


def test_effective_score_and_json_schema_present_en():
    agent = create_trading_scenario_agent(language="en")
    assert "effective_score ≥ min_score" in agent.instruction
    for key in (
        '"fundamental_check":',
        '"buy_score":',
        '"macro_adjustment":',
        '"effective_score":',
        '"min_score":',
        '"momentum_signal_count":',
        '"additional_confirmation_count":',
        '"entry_checklist_passed":',
    ):
        assert key in agent.instruction


def test_uses_canonical_stock_holdings_table_en():
    agent = create_trading_scenario_agent(language="en")
    assert "US portfolio table is `stock_holdings`." in agent.instruction
    assert "us_stock_holdings" not in agent.instruction


def test_sector_constraint_applied_en():
    agent = create_trading_scenario_agent(
        language="en",
        sector_names=["Technology", "Healthcare"],
    )
    assert "Technology, Healthcare" in agent.instruction
    assert "{sector_constraint}" not in agent.instruction
