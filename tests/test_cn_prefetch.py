from unittest.mock import patch

import pandas as pd
import pytest

from prism.core.data.cn_prefetch import prefetch_cn_analysis_data


@patch("prism.core.data.cn_prefetch.CNDataClient")
def test_prefetch_returns_required_keys(MockClient):
    instance = MockClient.return_value
    instance.get_ohlcv.return_value = pd.DataFrame({
        "Open": [1], "High": [2], "Low": [0.5], "Close": [1.5], "Volume": [100],
    }, index=pd.to_datetime(["2026-01-02"]))
    instance.get_stock_info.return_value = {"股票简称": "贵州茅台"}
    instance.get_top_holders.return_value = pd.DataFrame({"股东": ["A"], "持股": [1]})
    instance.get_fund_holdings.return_value = pd.DataFrame()
    instance.get_northbound_flow.return_value = pd.DataFrame()
    instance.get_financial_indicators.return_value = pd.DataFrame({"指标": [1]})
    instance.get_index_ohlcv.return_value = pd.DataFrame({"close": [3000]})

    result = prefetch_cn_analysis_data("600519", reference_date="20260606")

    assert "stock_ohlcv" in result
    assert "stock_info" in result
    assert "holder_info" in result
    assert "market_indices" in result
    assert "600519" in result["stock_ohlcv"] or "OHLCV" in result["stock_ohlcv"]


@patch("prism.core.data.cn_prefetch.CNDataClient")
def test_prefetch_raises_when_ohlcv_empty(MockClient):
    instance = MockClient.return_value
    instance.get_ohlcv.return_value = pd.DataFrame()
    with pytest.raises(ValueError, match="No price data"):
        prefetch_cn_analysis_data("600519", reference_date="20260606")
