"""Prefetch CN A-share data for agent injection."""

import logging
from datetime import datetime, timedelta

from prism.core.data.cn_client import CNDataClient
from prism.core.data.prefetch import _df_to_markdown
from prism.core.market.cn_ticker import normalize

logger = logging.getLogger(__name__)

CN_INDEX_SYMBOLS = {
    "shanghai_composite": ("sh000001", "上证指数"),
    "shenzhen_component": ("sz399001", "深证成指"),
    "chinext": ("sz399006", "创业板指"),
    "csi300": ("sh000300", "沪深300"),
}


def _ref_to_dates(reference_date: str) -> tuple[str, str]:
    end = datetime.strptime(reference_date, "%Y%m%d")
    start = end - timedelta(days=365)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def prefetch_cn_analysis_data(code: str, reference_date: str) -> dict:
    ticker = normalize(code)
    client = CNDataClient()
    start_date, end_date = _ref_to_dates(reference_date)
    result = {}

    ohlcv_df = client.get_ohlcv(ticker.code, start_date=start_date, end_date=end_date)
    if ohlcv_df is None or ohlcv_df.empty:
        raise ValueError(
            f"No price data for {ticker.code} — market may be closed or code invalid"
        )
    result["stock_ohlcv"] = _df_to_markdown(ohlcv_df.tail(252), f"OHLCV: {ticker.code} (1y)")

    info = client.get_stock_info(ticker.code)
    if info:
        lines = [f"- **{k}**: {v}" for k, v in info.items()]
        result["stock_info"] = "### Stock Info\n\n" + "\n".join(lines)
        result["company_profile"] = result["stock_info"]

    holders_parts = []
    top = client.get_top_holders(ticker.code)
    if top is not None and not top.empty:
        holders_parts.append(_df_to_markdown(top, "Top 10 Shareholders (十大股东)"))
    funds = client.get_fund_holdings(ticker.code)
    if funds is not None and not funds.empty:
        holders_parts.append(_df_to_markdown(funds, "Fund Holdings (基金持仓)"))
    north = client.get_northbound_flow(ticker.code)
    if north is not None and not north.empty:
        holders_parts.append(_df_to_markdown(north, "Northbound Flow (北向资金)"))
    if holders_parts:
        result["holder_info"] = "\n\n".join(holders_parts)

    fin = client.get_financial_indicators(ticker.code)
    if fin is not None and not fin.empty:
        result["financial_statements"] = _df_to_markdown(fin.tail(8), "Financial Indicators")

    market_indices = {}
    for key, (symbol, title) in CN_INDEX_SYMBOLS.items():
        idx_df = client.get_index_ohlcv(symbol)
        if idx_df is not None and not idx_df.empty:
            market_indices[key] = _df_to_markdown(idx_df.tail(60), title)
    if market_indices:
        result["market_indices"] = market_indices

    logger.info(f"Prefetched CN data for {ticker.code}: {list(result.keys())}")
    return result
