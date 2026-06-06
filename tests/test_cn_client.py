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
    mock_ak.stock_zh_a_hist_tx.assert_not_called()


@patch("prism.core.data.cn_client.ak")
def test_get_ohlcv_falls_back_to_tencent(mock_ak):
    mock_ak.stock_zh_a_hist.side_effect = ConnectionError("eastmoney blocked")
    mock_ak.stock_zh_a_hist_tx.return_value = pd.DataFrame({
        "date": ["2026-01-02"],
        "open": [100.0],
        "close": [101.0],
        "high": [102.0],
        "low": [99.0],
        "amount": [100000.0],
    })
    client = CNDataClient()
    df = client.get_ohlcv("600519", start_date="20250101", end_date="20250601")
    assert not df.empty
    assert df["Close"].iloc[0] == 101.0
    mock_ak.stock_zh_a_hist_tx.assert_called_once_with(
        symbol="sh600519",
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


@patch.object(CNDataClient, "get_stock_info", return_value={"股票简称": "贵州茅台"})
def test_get_company_name_prefers_short_name(_mock_get_stock_info):
    client = CNDataClient()
    assert client.get_company_name("600519") == "贵州茅台"


@patch.object(CNDataClient, "get_stock_info", return_value={})
def test_get_company_name_falls_back_to_code(_mock_get_stock_info):
    client = CNDataClient()
    assert client.get_company_name("600519") == "600519"


@patch("prism.core.data.cn_client.ak")
def test_get_top_holders_uses_prefixed_symbol(mock_ak):
    mock_ak.stock_gdfx_top_10_em.return_value = pd.DataFrame({"holder": ["Test"]})
    client = CNDataClient()
    df = client.get_top_holders("600519")
    assert not df.empty
    mock_ak.stock_gdfx_top_10_em.assert_called_once_with(symbol="sh600519")


@patch("prism.core.data.cn_client.ak")
def test_get_fund_holdings_calls_akshare(mock_ak):
    mock_ak.stock_fund_stock_holder.return_value = pd.DataFrame({"fund": ["Test Fund"]})
    client = CNDataClient()
    df = client.get_fund_holdings("600519")
    assert not df.empty
    mock_ak.stock_fund_stock_holder.assert_called_once_with(symbol="600519")


@patch("prism.core.data.cn_client.ak")
def test_get_ohlcv_returns_empty_on_exception(mock_ak):
    mock_ak.stock_zh_a_hist.side_effect = RuntimeError("network error")
    mock_ak.stock_zh_a_hist_tx.side_effect = RuntimeError("network error")
    mock_ak.stock_zh_a_daily.side_effect = RuntimeError("network error")
    client = CNDataClient()
    df = client.get_ohlcv("600519", start_date="20250101", end_date="20250601")
    assert df.empty
