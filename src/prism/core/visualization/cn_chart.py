"""
CN A-share Chart Generation Module

Generates charts for CN A-share analysis reports using akshare DataFrames.
Chart types:
1. Price Chart (Close + MA + Volume)
2. Technical Indicators Chart (RSI + MACD)
3. Top Holders Chart (horizontal bar)
"""

import logging

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from prism.core.us.visualization.chart import (
    HIST_DOWN_COLOR,
    HIST_UP_COLOR,
    MACD_COLOR,
    PRIMARY_COLORS,
    RSI_COLOR,
    SIGNAL_COLOR,
    calculate_macd,
    calculate_rsi,
    figure_to_base64_html,
)

logger = logging.getLogger(__name__)

_MIN_TECH_ROWS = 26  # MACD slow period

_LABEL_COLS = ("股东名称", "HOLDER_NAME", "股东")
_VALUE_COLS = (
    "占总股本持股比例",
    "占总股本比例",
    "期末持股-持股占流通股比",
    "FREE_HOLDNUM_RATIO",
    "持股数",
    "期末持股-数量",
    "HOLD_NUM",
)
_RANK_COLS = {"名次", "序号", "HOLDER_RANK", "股东排名"}


def _ensure_cn_font() -> None:
    from matplotlib import font_manager

    candidates = (
        "PingFang SC",
        "Noto Sans CJK SC",
        "Noto Sans SC",
        "SimHei",
        "Arial Unicode MS",
    )
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name, *plt.rcParams["font.sans-serif"]]
            plt.rcParams["axes.unicode_minus"] = False
            return
    logger.warning("No CJK font found; CN chart labels may render as boxes")


def _resolve_holder_columns(holders_df: pd.DataFrame) -> tuple[str, str] | None:
    label_col = next((c for c in _LABEL_COLS if c in holders_df.columns), None)
    value_col = next((c for c in _VALUE_COLS if c in holders_df.columns), None)
    if value_col is None:
        numeric = [
            c for c in holders_df.select_dtypes(include="number").columns
            if c not in _RANK_COLS
        ]
        value_col = numeric[0] if numeric else None
    if label_col is None:
        non_numeric = holders_df.select_dtypes(exclude="number").columns.tolist()
        label_col = non_numeric[0] if non_numeric else None
    if not label_col or not value_col:
        return None
    return label_col, value_col


def _html_or_empty(html: str | None) -> str:
    return html or ""


def get_cn_price_chart_html(
    code: str,
    company_name: str,
    hist_df: pd.DataFrame,
    width: int = 900,
    dpi: int = 80,
) -> str:
    """Generate CN price trend chart and return as base64 HTML."""
    _ensure_cn_font()
    fig = None
    try:
        if hist_df is None or hist_df.empty or "Close" not in hist_df.columns:
            return ""

        df = hist_df.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        has_volume = "Volume" in df.columns and not df["Volume"].isna().all()

        if has_volume:
            fig, (ax_price, ax_vol) = plt.subplots(
                2,
                1,
                figsize=(12, 8),
                gridspec_kw={"height_ratios": [3, 1]},
                sharex=True,
            )
        else:
            fig, ax_price = plt.subplots(1, 1, figsize=(12, 6))
            ax_vol = None

        ax_price.plot(
            df.index,
            df["Close"],
            color=PRIMARY_COLORS[0],
            linewidth=1.5,
            label="Close",
        )

        legend_labels = ["Close"]
        if len(df) >= 20:
            ma20 = df["Close"].rolling(window=20).mean()
            if not ma20.isna().all():
                ax_price.plot(
                    df.index,
                    ma20,
                    color="#ff9500",
                    linewidth=1,
                    label="MA20",
                )
                legend_labels.append("MA20")
        if len(df) >= 60:
            ma60 = df["Close"].rolling(window=60).mean()
            if not ma60.isna().all():
                ax_price.plot(
                    df.index,
                    ma60,
                    color="#0066cc",
                    linewidth=1.5,
                    label="MA60",
                )
                legend_labels.append("MA60")

        ax_price.set_title(
            f"{company_name} ({code}) Price Trend",
            fontsize=14,
            fontweight="bold",
        )
        ax_price.set_ylabel("Price (CNY)", fontsize=10)
        ax_price.legend(loc="upper left", fontsize=8)
        ax_price.grid(True, linestyle="--", alpha=0.3)
        ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))

        if ax_vol is not None:
            close_diff = df["Close"].diff().fillna(0)
            vol_colors = [
                "#26a69a" if change >= 0 else "#ef5350" for change in close_diff
            ]
            ax_vol.bar(df.index, df["Volume"], color=vol_colors, alpha=0.6, width=0.8)
            ax_vol.set_ylabel("Volume", fontsize=10)
            ax_vol.grid(True, linestyle="--", alpha=0.3)

        plt.tight_layout()
        return _html_or_empty(
            figure_to_base64_html(fig, f"{code} Price Trend", width, dpi, "jpg")
        )
    except Exception as e:
        logger.warning(f"Failed to create CN price chart for {code}: {e}")
        if fig is not None:
            plt.close(fig)
        return ""


def get_cn_technical_chart_html(
    code: str,
    company_name: str,
    hist_df: pd.DataFrame,
    width: int = 900,
    dpi: int = 80,
) -> str:
    """Generate CN RSI/MACD technical chart and return as base64 HTML."""
    _ensure_cn_font()
    fig = None
    try:
        if hist_df is None or hist_df.empty or "Close" not in hist_df.columns:
            return ""
        if len(hist_df) < _MIN_TECH_ROWS:
            return ""

        df = hist_df.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        df["RSI"] = calculate_rsi(df["Close"], 14)
        df["MACD"], df["Signal"], df["Histogram"] = calculate_macd(
            df["Close"], 12, 26, 9
        )

        fig, (ax_rsi, ax_macd) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        fig.suptitle(
            f"{company_name} ({code}) Technical Indicators",
            fontsize=14,
            fontweight="bold",
        )

        ax_rsi.plot(df.index, df["RSI"], color=RSI_COLOR, linewidth=1.5)
        ax_rsi.fill_between(df.index, df["RSI"], alpha=0.1, color=RSI_COLOR)
        ax_rsi.axhline(y=70, color="red", linestyle="--", linewidth=0.8, alpha=0.7)
        ax_rsi.axhline(y=30, color="green", linestyle="--", linewidth=0.8, alpha=0.7)
        ax_rsi.axhline(y=50, color="gray", linestyle=":", linewidth=0.5, alpha=0.5)
        ax_rsi.fill_between(df.index, 70, 100, alpha=0.1, color="red")
        ax_rsi.fill_between(df.index, 0, 30, alpha=0.1, color="green")
        ax_rsi.set_ylabel("RSI", fontsize=10)
        ax_rsi.set_ylim(0, 100)
        ax_rsi.set_title("RSI (14)", fontsize=11, loc="left")
        ax_rsi.grid(True, linestyle="--", alpha=0.3)

        ax_macd.plot(df.index, df["MACD"], color=MACD_COLOR, linewidth=1.5, label="MACD")
        ax_macd.plot(
            df.index, df["Signal"], color=SIGNAL_COLOR, linewidth=1.5, label="Signal"
        )
        hist_colors = [
            HIST_UP_COLOR if h >= 0 else HIST_DOWN_COLOR for h in df["Histogram"]
        ]
        ax_macd.bar(df.index, df["Histogram"], color=hist_colors, alpha=0.6, width=0.8)
        ax_macd.axhline(y=0, color="gray", linestyle="-", linewidth=0.5)
        ax_macd.set_ylabel("MACD", fontsize=10)
        ax_macd.set_xlabel("Date", fontsize=10)
        ax_macd.set_title("MACD (12/26/9)", fontsize=11, loc="left")
        ax_macd.legend(loc="upper left", fontsize=8)
        ax_macd.grid(True, linestyle="--", alpha=0.3)

        ax_macd.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        plt.tight_layout()
        return _html_or_empty(
            figure_to_base64_html(
                fig, f"{code} Technical Indicators", width, dpi, "jpg"
            )
        )
    except Exception as e:
        logger.warning(f"Failed to create CN technical chart for {code}: {e}")
        if fig is not None:
            plt.close(fig)
        return ""


def get_cn_holder_chart_html(
    code: str,
    company_name: str,
    holders_df: pd.DataFrame,
    width: int = 900,
    dpi: int = 80,
) -> str:
    """Generate CN top holders horizontal bar chart and return as base64 HTML."""
    _ensure_cn_font()
    fig = None
    try:
        if holders_df is None or holders_df.empty:
            return ""

        resolved = _resolve_holder_columns(holders_df)
        if resolved is None:
            return ""
        label_col, value_col = resolved
        labels = holders_df[label_col].astype(str)

        plot_df = pd.DataFrame({"label": labels, "value": holders_df[value_col]})
        plot_df = plot_df.dropna(subset=["value"]).sort_values("value", ascending=False).head(10)
        if plot_df.empty:
            return ""

        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle(
            f"{company_name} ({code}) Top Holders",
            fontsize=14,
            fontweight="bold",
        )

        y_pos = range(len(plot_df))
        bars = ax.barh(y_pos, plot_df["value"], color=PRIMARY_COLORS[0], alpha=0.8)
        display_labels = [
            label[:25] + "..." if len(label) > 28 else label
            for label in plot_df["label"]
        ]
        ax.set_yticks(y_pos)
        ax.set_yticklabels(display_labels, fontsize=9)
        ax.invert_yaxis()
        if "比例" in value_col or "RATIO" in value_col:
            xlabel = "Shareholding Ratio (%)"
        else:
            xlabel = value_col
        ax.set_xlabel(xlabel, fontsize=10)
        ax.grid(axis="x", linestyle="--", alpha=0.3)

        max_val = plot_df["value"].max()
        for bar, val in zip(bars, plot_df["value"]):
            ax.text(
                bar.get_width() + max_val * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}",
                va="center",
                fontsize=8,
            )

        if max_val > 0:
            ax.set_xlim(0, max_val * 1.15)

        plt.tight_layout()
        return _html_or_empty(
            figure_to_base64_html(fig, f"{code} Top Holders", width, dpi, "jpg")
        )
    except Exception as e:
        logger.warning(f"Failed to create CN holder chart for {code}: {e}")
        if fig is not None:
            plt.close(fig)
        return ""
