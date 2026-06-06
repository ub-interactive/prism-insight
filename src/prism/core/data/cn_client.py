"""
CN A-share Data Client

Unified interface for fetching Chinese A-share market data using akshare.
"""

import logging

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
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            if df is None or df.empty:
                logger.warning(f"No OHLCV data found for {code}")
                return pd.DataFrame()

            df = df.rename(columns=_OHLCV_RENAME)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.set_index("Date")

            logger.info(f"Retrieved {len(df)} OHLCV records for {code}")
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {code}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, code: str) -> dict:
        """Get stock profile fields from East Money."""
        try:
            df = ak.stock_individual_info_em(symbol=code)
            if df is None or df.empty or "item" not in df.columns or "value" not in df.columns:
                logger.warning(f"No stock info found for {code}")
                return {}
            return dict(zip(df["item"], df["value"]))
        except Exception as e:
            logger.error(f"Error fetching stock info for {code}: {e}")
            return {}

    def get_company_name(self, code: str) -> str:
        """Return company short name, or the code if unavailable."""
        info = self.get_stock_info(code)
        return str(info.get("股票简称") or info.get("证券简称") or code)

    def get_financial_indicators(self, code: str) -> pd.DataFrame:
        """Get financial analysis indicators."""
        try:
            df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2020")
            if df is None or df.empty:
                logger.warning(f"No financial indicators found for {code}")
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Error fetching financial indicators for {code}: {e}")
            return pd.DataFrame()

    def get_top_holders(self, code: str) -> pd.DataFrame:
        """Get top 10 shareholders."""
        try:
            ticker = normalize(code)
            df = ak.stock_gdfx_top_10_em(symbol=ticker.akshare_symbol)
            if df is None or df.empty:
                logger.warning(f"No top holders found for {code}")
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Error fetching top holders for {code}: {e}")
            return pd.DataFrame()

    def get_fund_holdings(self, code: str) -> pd.DataFrame:
        """Get fund holdings for the symbol."""
        try:
            df = ak.stock_fund_stock_holder(symbol=code)
            if df is None or df.empty:
                logger.warning(f"No fund holdings found for {code}")
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Error fetching fund holdings for {code}: {e}")
            return pd.DataFrame()

    def get_northbound_flow(self, code: str) -> pd.DataFrame:
        """Get northbound (Stock Connect) flow data."""
        try:
            df = ak.stock_hsgt_individual_em(symbol=code)
            if df is None or df.empty:
                logger.warning(f"No northbound flow found for {code}")
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Error fetching northbound flow for {code}: {e}")
            return pd.DataFrame()

    def get_index_ohlcv(self, symbol: str) -> pd.DataFrame:
        """Get index OHLCV data."""
        try:
            df = ak.stock_zh_index_daily_em(symbol=symbol)
            if df is None or df.empty:
                logger.warning(f"No index OHLCV data found for {symbol}")
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Error fetching index OHLCV for {symbol}: {e}")
            return pd.DataFrame()
