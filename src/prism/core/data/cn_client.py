"""
CN A-share Data Client

Unified interface for fetching Chinese A-share market data using akshare.
Falls back to non-Eastmoney sources when Eastmoney endpoints are unreachable.
"""

import logging
from collections.abc import Callable

import akshare as ak
import pandas as pd

from prism.core.market.cn_ticker import normalize

logger = logging.getLogger(__name__)

_OHLCV_RENAME = {
    "日期": "Date",
    "开盘": "Open",
    "收盘": "Close",
    "最高": "High",
    "最低": "Low",
    "成交量": "Volume",
    "成交额": "Amount",
    "振幅": "Amplitude",
    "涨跌幅": "Change_pct",
    "涨跌额": "Change",
    "换手率": "Turnover_rate",
}

_TX_OHLCV_RENAME = {
    "date": "Date",
    "open": "Open",
    "close": "Close",
    "high": "High",
    "low": "Low",
    "amount": "Amount",
}

_SINA_OHLCV_RENAME = {
    "date": "Date",
    "open": "Open",
    "close": "Close",
    "high": "High",
    "low": "Low",
}


def _call_akshare(fn: Callable, *args, **kwargs):
    """Call akshare once; retry once on transient network errors."""
    last_error = None
    for attempt in range(2):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                logger.debug(f"Retrying {fn.__name__} after {type(exc).__name__}")
                continue
            raise last_error


def _normalize_ohlcv(df: pd.DataFrame, rename_map: dict[str, str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.rename(columns=rename_map)
    if "Date" not in out.columns:
        return pd.DataFrame()

    out["Date"] = pd.to_datetime(out["Date"])
    return out.set_index("Date")


class CNDataClient:
    """Unified CN A-share data client backed by akshare."""

    def __init__(self):
        pass

    def get_ohlcv(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """Get OHLCV data for a CN A-share symbol."""
        ticker = normalize(code)
        sources: list[tuple[str, Callable[[], pd.DataFrame], dict[str, str]]] = [
            (
                "eastmoney",
                lambda: ak.stock_zh_a_hist(
                    symbol=ticker.code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                ),
                _OHLCV_RENAME,
            ),
            (
                "tencent",
                lambda: ak.stock_zh_a_hist_tx(
                    symbol=ticker.akshare_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                ),
                _TX_OHLCV_RENAME,
            ),
            (
                "sina",
                lambda: ak.stock_zh_a_daily(
                    symbol=ticker.akshare_symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust,
                ),
                _SINA_OHLCV_RENAME,
            ),
        ]

        for source_name, fetch, rename_map in sources:
            try:
                df = _call_akshare(fetch)
                normalized = _normalize_ohlcv(df, rename_map)
                if normalized.empty:
                    logger.warning(f"No OHLCV data from {source_name} for {ticker.code}")
                    continue
                logger.info(
                    f"Retrieved {len(normalized)} OHLCV records for {ticker.code} via {source_name}"
                )
                return normalized
            except Exception as exc:
                logger.warning(
                    f"OHLCV fetch via {source_name} failed for {ticker.code}: {exc}"
                )

        logger.error(f"All OHLCV sources failed for {ticker.code}")
        return pd.DataFrame()

    def get_stock_info(self, code: str) -> dict:
        """Get stock profile fields from East Money or CNINFO."""
        try:
            df = _call_akshare(ak.stock_individual_info_em, symbol=code)
            if df is not None and not df.empty and "item" in df.columns and "value" in df.columns:
                return dict(zip(df["item"], df["value"]))
        except Exception as exc:
            logger.warning(f"Eastmoney stock info failed for {code}: {exc}")

        try:
            df = _call_akshare(ak.stock_profile_cninfo, symbol=code)
            if df is not None and not df.empty:
                info = df.iloc[0].dropna().to_dict()
                logger.info(f"Retrieved stock info for {code} via CNINFO")
                return info
        except Exception as exc:
            logger.error(f"Error fetching stock info for {code}: {exc}")

        return {}

    def get_company_name(self, code: str) -> str:
        """Return company short name, or the code if unavailable."""
        info = self.get_stock_info(code)
        for key in ("股票简称", "证券简称", "A股简称", "公司名称"):
            value = info.get(key)
            if value:
                return str(value)
        return code

    def get_financial_indicators(self, code: str) -> pd.DataFrame:
        """Get financial analysis indicators."""
        try:
            df = _call_akshare(ak.stock_financial_analysis_indicator, symbol=code, start_year="2020")
            if df is None or df.empty:
                logger.warning(f"No financial indicators found for {code}")
                return pd.DataFrame()
            return df
        except Exception as exc:
            logger.error(f"Error fetching financial indicators for {code}: {exc}")
            return pd.DataFrame()

    def get_top_holders(self, code: str) -> pd.DataFrame:
        """Get top 10 shareholders."""
        try:
            ticker = normalize(code)
            df = _call_akshare(ak.stock_gdfx_top_10_em, symbol=ticker.akshare_symbol)
            if df is None or df.empty:
                logger.warning(f"No top holders found for {code}")
                return pd.DataFrame()
            return df
        except Exception as exc:
            logger.error(f"Error fetching top holders for {code}: {exc}")
            return pd.DataFrame()

    def get_fund_holdings(self, code: str) -> pd.DataFrame:
        """Get fund holdings for the symbol."""
        try:
            df = _call_akshare(ak.stock_fund_stock_holder, symbol=code)
            if df is None or df.empty:
                logger.warning(f"No fund holdings found for {code}")
                return pd.DataFrame()
            return df
        except Exception as exc:
            logger.error(f"Error fetching fund holdings for {code}: {exc}")
            return pd.DataFrame()

    def get_northbound_flow(self, code: str) -> pd.DataFrame:
        """Get northbound (Stock Connect) flow data."""
        try:
            df = _call_akshare(ak.stock_hsgt_individual_em, symbol=code)
            if df is None or df.empty:
                logger.warning(f"No northbound flow found for {code}")
                return pd.DataFrame()
            return df
        except Exception as exc:
            logger.warning(f"Northbound flow unavailable for {code}: {exc}")
            return pd.DataFrame()

    def get_index_ohlcv(self, symbol: str) -> pd.DataFrame:
        """Get index OHLCV data."""
        sources: list[tuple[str, Callable[[], pd.DataFrame]]] = [
            ("eastmoney", lambda: ak.stock_zh_index_daily_em(symbol=symbol)),
            ("tencent", lambda: ak.stock_zh_index_daily_tx(symbol=symbol)),
        ]

        for source_name, fetch in sources:
            try:
                df = _call_akshare(fetch)
                if df is None or df.empty:
                    logger.warning(f"No index OHLCV from {source_name} for {symbol}")
                    continue
                logger.info(
                    f"Retrieved {len(df)} index OHLCV records for {symbol} via {source_name}"
                )
                return df
            except Exception as exc:
                logger.warning(
                    f"Index OHLCV fetch via {source_name} failed for {symbol}: {exc}"
                )

        logger.error(f"All index OHLCV sources failed for {symbol}")
        return pd.DataFrame()
