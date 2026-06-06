from unittest.mock import patch

import pandas as pd

from prism.core.data.cn_client import CNDataClient


@patch("prism.core.data.cn_client.ak")
def test_get_ohlcv_normalizes_columns(mock_ak):
    mock_ak.stock_zh_a_hist.return_value = pd.DataFrame({
        "日期": ["2026-01-02"],
        "开盘": [100.0],
        "收盘": [101.0],
        "最高": [102.0],
        "最低": [99.0],
        "成交量": [1000],
        "成交额": [100000.0],
        "振幅": [1.0],
        "涨跌幅": [1.0],
        "涨跌额": [1.0],
        "换手率": [0.5],
    })
    client = CNDataClient()
    df = client.get_ohlcv("600519", start_date="20250101", end_date="20250601")
    assert not df.empty
    assert "Close" in df.columns
    assert "Open" in df.columns
    assert isinstance(df.index, pd.DatetimeIndex)
    assert "Date" not in df.columns
    mock_ak.stock_zh_a_hist.assert_called_once_with(
        symbol="600519",
        period="daily",
        start_date="20250101",
        end_date="20250601",
        adjust="qfq",
    )


@patch("prism.core.data.cn_client.ak")
def test_get_stock_info_returns_dict(mock_ak):
    mock_ak.stock_individual_info_em.return_value = pd.DataFrame({
        "item": ["股票简称", "总市值"],
        "value": ["贵州茅台", "2000000000000"],
    })
    client = CNDataClient()
    info = client.get_stock_info("600519")
    assert info["股票简称"] == "贵州茅台"
