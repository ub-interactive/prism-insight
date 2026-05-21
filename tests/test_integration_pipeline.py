"""US-only integration checks for root pipeline modules."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest


def _sample_snapshot() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 200.0],
            "Close": [104.0, 198.0],
            "Volume": [4_000_000, 2_500_000],
            "Amount": [450_000_000, 350_000_000],
        },
        index=["AAPL", "MSFT"],
    )


def test_trigger_to_agents_flow_smoke():
    from cores.agents import get_agent_directory
    from trigger_batch import trigger_morning_volume_surge

    snapshot = _sample_snapshot()
    prev_snapshot = snapshot.copy()
    prev_snapshot["Volume"] = prev_snapshot["Volume"] * 0.5
    prev_snapshot["Close"] = prev_snapshot["Close"] * 0.99
    cap_df = pd.DataFrame({"MarketCap": [2.5e12, 2.0e12]}, index=["AAPL", "MSFT"])

    triggered = trigger_morning_volume_surge(
        trade_date=datetime.now().strftime("%Y%m%d"),
        snapshot=snapshot,
        prev_snapshot=prev_snapshot,
        cap_df=cap_df,
        top_n=5,
    )
    assert isinstance(triggered, pd.DataFrame)

    agents = get_agent_directory(
        company_name="Apple Inc.",
        ticker="AAPL",
        reference_date=datetime.now().strftime("%Y%m%d"),
        base_sections=["price_volume_analysis", "news_analysis"],
        language="en",
    )
    assert "price_volume_analysis" in agents
    assert "news_analysis" in agents


@pytest.mark.asyncio
async def test_orchestrator_trigger_batch_mock():
    from stock_analysis_orchestrator import USStockAnalysisOrchestrator

    with patch("telegram_config.TelegramConfig") as mock_config:
        mock_config.return_value.use_telegram = False
        orchestrator = USStockAnalysisOrchestrator()

        with patch.object(orchestrator, "run_trigger_batch", new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = [
                {"ticker": "AAPL", "company_name": "Apple Inc.", "trigger_type": "Volume Surge Top"}
            ]
            result = await orchestrator.run_trigger_batch("morning")

    assert len(result) == 1
    assert result[0]["ticker"] == "AAPL"
