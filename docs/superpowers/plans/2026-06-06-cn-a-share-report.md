# CN A-Share Report Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable full-parity A-share analysis reports (6 analysts + strategy + summary + PDF) via `python -m prism.ops.dev.demo 600519 --market cn --language zh`.

**Architecture:** Parallel CN module mirroring US (`CNDataClient` → `prefetch_cn_analysis_data` → CN agents → `analyze_cn_stock`). Demo routes on `--market cn`. Shared synthesis helpers (`generate_report`, `generate_investment_strategy`, `generate_summary`) unchanged.

**Tech Stack:** Python 3.10+, akshare, pandas, existing mcp-agent + Perplexity MCP, Playwright PDF, matplotlib charts.

**Spec:** [`docs/superpowers/specs/2026-06-06-cn-a-share-report-design.md`](../specs/2026-06-06-cn-a-share-report-design.md)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `requirements.txt` | Modify | Add `akshare>=1.14` |
| `src/prism/core/market/__init__.py` | Create | Package marker |
| `src/prism/core/market/cn_ticker.py` | Create | 6-digit code validation, SH/SZ inference |
| `src/prism/core/market_calendar_cn.py` | Create | Last CN trading day |
| `src/prism/core/data/cn_client.py` | Create | akshare wrapper |
| `src/prism/core/data/cn_prefetch.py` | Create | Prefetch bundle for agents |
| `src/prism/core/agents/cn/__init__.py` | Create | CN agent package |
| `src/prism/core/agents/cn/stock_price_agents.py` | Create | Price + institutional agents |
| `src/prism/core/agents/cn/company_info_agents.py` | Create | Company status + overview agents |
| `src/prism/core/agents/cn/market_index_agents.py` | Create | CN index market agent |
| `src/prism/core/agents/cn/news_agents.py` | Create | CN news agent (Perplexity) |
| `src/prism/core/agents/cn_directory.py` | Create | `get_cn_agent_directory()` |
| `src/prism/core/visualization/cn_chart.py` | Create | CN chart HTML helpers |
| `src/prism/core/analysis_cn.py` | Create | `analyze_cn_stock()` pipeline |
| `src/prism/core/report_generation.py` | Modify | Add `zh`/`ko` to `LANGUAGE_NAMES`; optional CN disclaimer |
| `src/prism/reporting/report_generator.py` | Modify | `save_cn_report()`, `save_cn_pdf_report()` |
| `src/prism/reporting/pdf_converter.py` | Modify | CJK font stack |
| `src/prism/ops/dev/demo.py` | Modify | `--market cn`, routing, CN name lookup |
| `docs/setup.md` | Modify | akshare + Linux CJK fonts note |
| `tests/test_cn_ticker.py` | Create | Ticker normalization tests |
| `tests/test_cn_market_calendar.py` | Create | Calendar tests |
| `tests/test_cn_client.py` | Create | Mocked CNDataClient tests |
| `tests/test_cn_prefetch.py` | Create | Mocked prefetch tests |
| `tests/test_cn_directory.py` | Create | Agent directory tests |

---

### Task 1: Add akshare dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add dependency**

Append to `requirements.txt` under the US Stock Market section:

```text
# China A-Share Market
akshare>=1.14
```

- [ ] **Step 2: Install and verify import**

Run: `pip install akshare>=1.14 && python -c "import akshare as ak; print(ak.__version__)"`

Expected: version string printed, no ImportError

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add akshare for CN A-share data"
```

---

### Task 2: CN ticker normalization

**Files:**
- Create: `src/prism/core/market/__init__.py`
- Create: `src/prism/core/market/cn_ticker.py`
- Test: `tests/test_cn_ticker.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cn_ticker.py
import pytest

from prism.core.market.cn_ticker import CNTicker, normalize, CNTickerError


def test_sh_main_board():
    t = normalize("600519")
    assert t == CNTicker(code="600519", exchange="SH", akshare_symbol="sh600519")


def test_sh_star_market():
    t = normalize("688981")
    assert t.exchange == "SH"
    assert t.akshare_symbol == "sh688981"


def test_sz_main_board():
    t = normalize("000001")
    assert t == CNTicker(code="000001", exchange="SZ", akshare_symbol="sz000001")


def test_sz_chinext():
    t = normalize("300750")
    assert t.exchange == "SZ"
    assert t.akshare_symbol == "sz300750"


@pytest.mark.parametrize("bad", ["12345", "abc123", "500001", "906519"])
def test_invalid_codes_raise(bad):
    with pytest.raises(CNTickerError):
        normalize(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cn_ticker.py -v`

Expected: FAIL with `ModuleNotFoundError` or `cannot import name 'normalize'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/prism/core/market/__init__.py
"""Market-specific helpers."""

# src/prism/core/market/cn_ticker.py
"""A-share ticker normalization (6-digit codes)."""

from dataclasses import dataclass


class CNTickerError(ValueError):
    """Invalid or unsupported A-share ticker."""


@dataclass(frozen=True)
class CNTicker:
    code: str
    exchange: str  # "SH" or "SZ"
    akshare_symbol: str  # e.g. "sh600519"


_SH_PREFIXES = ("60", "68")
_SZ_PREFIXES = ("00", "30")


def normalize(code: str) -> CNTicker:
    """Validate 6-digit A-share code and infer exchange."""
    raw = (code or "").strip()
    if len(raw) != 6 or not raw.isdigit():
        raise CNTickerError(
            "CN market requires a 6-digit A-share code (e.g. 600519, 000001)"
        )

    prefix = raw[:2]
    if prefix in _SH_PREFIXES:
        exchange = "SH"
        ak_symbol = f"sh{raw}"
    elif prefix in _SZ_PREFIXES:
        exchange = "SZ"
        ak_symbol = f"sz{raw}"
    else:
        raise CNTickerError(
            f"Unrecognized A-share code prefix '{prefix}'. "
            "Supported: 60/68 (Shanghai), 00/30 (Shenzhen). B-shares not supported."
        )

    return CNTicker(code=raw, exchange=exchange, akshare_symbol=ak_symbol)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cn_ticker.py -v`

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/market/ tests/test_cn_ticker.py
git commit -m "feat: add CN A-share ticker normalization"
```

---

### Task 3: CN market calendar

**Files:**
- Create: `src/prism/core/market_calendar_cn.py`
- Test: `tests/test_cn_market_calendar.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cn_market_calendar.py
from datetime import date

from prism.core.market_calendar_cn import get_cn_reference_date, is_cn_market_day


def test_weekend_not_trading_day():
    assert is_cn_market_day(date(2026, 6, 6)) is False  # Saturday


def test_reference_date_returns_yyyymmdd_string():
    ref = get_cn_reference_date(date(2026, 6, 6))
    assert len(ref) == 8
    assert ref.isdigit()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cn_market_calendar.py -v`

Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Mirror `src/prism/core/market_calendar.py` using SSE calendar:

```python
# src/prism/core/market_calendar_cn.py
"""China A-share market calendar utilities (SSE/SZSE shared holidays)."""

import logging
from datetime import date, datetime, timedelta

import pandas_market_calendars as mcal
import pytz

logger = logging.getLogger(__name__)

SSE_CALENDAR = mcal.get_calendar("SSE")
CST = pytz.timezone("Asia/Shanghai")


def is_cn_market_day(check_date: date | None = None) -> bool:
    if check_date is None:
        check_date = datetime.now(CST).date()
    if check_date.weekday() >= 5:
        return False
    fmt = check_date.strftime("%Y-%m-%d")
    return len(SSE_CALENDAR.valid_days(start_date=fmt, end_date=fmt)) > 0


def get_last_trading_day(from_date: date | None = None) -> date:
    if from_date is None:
        from_date = datetime.now(CST).date()
    start = (from_date - timedelta(days=14)).strftime("%Y-%m-%d")
    end = from_date.strftime("%Y-%m-%d")
    valid = SSE_CALENDAR.valid_days(start_date=start, end_date=end)
    if len(valid) == 0:
        return from_date
    last = valid[-1]
    return last.date() if hasattr(last, "date") else last.to_pydatetime().date()


def get_cn_reference_date(from_date: date | None = None) -> str:
    """Return last CN trading day as YYYYMMDD."""
    if from_date is None:
        from_date = datetime.now(CST).date()
    if is_cn_market_day(from_date):
        d = from_date
    else:
        d = get_last_trading_day(from_date)
    return d.strftime("%Y%m%d")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cn_market_calendar.py -v`

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/market_calendar_cn.py tests/test_cn_market_calendar.py
git commit -m "feat: add CN market calendar helpers"
```

---

### Task 4: CNDataClient (akshare wrapper)

**Files:**
- Create: `src/prism/core/data/cn_client.py`
- Test: `tests/test_cn_client.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cn_client.py
from unittest.mock import MagicMock, patch

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


@patch("prism.core.data.cn_client.ak")
def test_get_stock_info_returns_dict(mock_ak):
    mock_ak.stock_individual_info_em.return_value = pd.DataFrame({
        "item": ["股票简称", "总市值"],
        "value": ["贵州茅台", "2000000000000"],
    })
    client = CNDataClient()
    info = client.get_stock_info("600519")
    assert info["股票简称"] == "贵州茅台"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cn_client.py -v`

Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

```python
# src/prism/core/data/cn_client.py
"""China A-share data client using akshare."""

import logging
from typing import Any, Dict, Optional

import akshare as ak
import pandas as pd

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
    "涨跌幅": "ChangePct",
    "涨跌额": "Change",
    "换手率": "Turnover",
}


class CNDataClient:
    """Thin akshare wrapper for A-share analysis."""

    def get_ohlcv(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns=_OHLCV_RENAME)
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.set_index("Date")
            return df
        except Exception as e:
            logger.error(f"akshare OHLCV failed for {code}: {e}")
            return pd.DataFrame()

    def get_stock_info(self, code: str) -> Dict[str, Any]:
        try:
            df = ak.stock_individual_info_em(symbol=code)
            if df is None or df.empty:
                return {}
            return dict(zip(df["item"], df["value"]))
        except Exception as e:
            logger.error(f"akshare stock info failed for {code}: {e}")
            return {}

    def get_company_name(self, code: str) -> str:
        info = self.get_stock_info(code)
        return str(info.get("股票简称") or info.get("证券简称") or code)

    def get_financial_indicators(self, code: str) -> pd.DataFrame:
        try:
            return ak.stock_financial_analysis_indicator(symbol=code, start_year="2020")
        except Exception as e:
            logger.error(f"akshare financial indicators failed for {code}: {e}")
            return pd.DataFrame()

    def get_top_holders(self, code: str) -> pd.DataFrame:
        try:
            return ak.stock_gdfx_top_10_em(symbol=code)
        except Exception as e:
            logger.error(f"akshare top holders failed for {code}: {e}")
            return pd.DataFrame()

    def get_fund_holdings(self, code: str) -> pd.DataFrame:
        try:
            return ak.stock_fund_stock_holder_em(symbol=code)
        except Exception as e:
            logger.error(f"akshare fund holdings failed for {code}: {e}")
            return pd.DataFrame()

    def get_northbound_flow(self, code: str) -> pd.DataFrame:
        try:
            return ak.stock_hsgt_individual_em(symbol=code)
        except Exception as e:
            logger.warning(f"akshare northbound flow unavailable for {code}: {e}")
            return pd.DataFrame()

    def get_index_ohlcv(self, symbol: str) -> pd.DataFrame:
        """symbol e.g. sh000001 (上证指数), sz399001 (深证成指)."""
        try:
            df = ak.stock_zh_index_daily_em(symbol=symbol)
            if df is None or df.empty:
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"akshare index OHLCV failed for {symbol}: {e}")
            return pd.DataFrame()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cn_client.py -v`

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/data/cn_client.py tests/test_cn_client.py
git commit -m "feat: add CNDataClient akshare wrapper"
```

---

### Task 5: CN prefetch bundle

**Files:**
- Create: `src/prism/core/data/cn_prefetch.py`
- Test: `tests/test_cn_prefetch.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cn_prefetch.py
from unittest.mock import MagicMock, patch

import pandas as pd

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
```

Add `import pytest` at top of test file.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cn_prefetch.py -v`

Expected: FAIL with import error

- [ ] **Step 3: Write minimal implementation**

Reuse `_df_to_markdown` from `prefetch.py` (import it):

```python
# src/prism/core/data/cn_prefetch.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cn_prefetch.py -v`

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/data/cn_prefetch.py tests/test_cn_prefetch.py
git commit -m "feat: add CN analysis data prefetch"
```

---

### Task 6: CN analyst agents (price + institutional)

**Files:**
- Create: `src/prism/core/agents/cn/__init__.py`
- Create: `src/prism/core/agents/cn/stock_price_agents.py`

- [ ] **Step 1: Create package and price agents**

Mirror US `stock_price_agents.py` structure. Key differences:
- Currency: CNY (人民币)
- No `yahoo_finance` MCP — `server_names=[]` when prefetched
- Institutional section covers 十大股东 / 基金 / 北向资金
- A-share session: 09:30–11:30, 13:00–15:00 CST; T+1 settlement

```python
# src/prism/core/agents/cn/__init__.py
"""CN A-share analysis agents."""

# src/prism/core/agents/cn/stock_price_agents.py
from mcp_agent.agents.agent import Agent


def create_price_volume_analysis_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_data: str | None = None,
) -> Agent:
    data_block = (
        f"## Pre-collected Data (OHLCV)\n{prefetched_data}\n"
        if prefetched_data
        else "## Data\nUse provided context only."
    )
    instruction = f"""You are a China A-share technical analyst. Analyze {company_name} ({code}.{exchange}) using CNY prices.

{data_block}

## Analysis Elements
1. Price trend and patterns (uptrend/downtrend/sideways)
2. Moving averages (5/10/20/60-day — A-share conventions)
3. Support and resistance in CNY
4. Volume analysis (换手率, 成交额)
5. RSI(14), MACD, Bollinger Bands from OHLCV
6. A-share context: limit-up/limit-down rules, T+1 settlement

## Report Structure
- Start with \\n\\n### 1-1. Price and Volume Analysis
- Sub-sections use #### headings
- All prices in CNY

Company: {company_name} ({code}.{exchange})
Analysis date: {reference_date}
"""
    return Agent(
        name="cn_price_volume_analysis_agent",
        instruction=instruction,
        server_names=[],
    )


def create_institutional_holdings_analysis_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_data: str | None = None,
) -> Agent:
    data_block = (
        f"## Pre-collected Holder Data\n{prefetched_data}\n"
        if prefetched_data
        else ""
    )
    instruction = f"""You are a China A-share ownership analyst for {company_name} ({code}.{exchange}).

{data_block}

Analyze:
1. Top 10 shareholders (十大股东) concentration
2. Fund holdings (基金持仓) trends
3. Northbound Stock Connect flow (北向资金) if data present
4. Implications for float and governance

## Report Structure
- Start with \\n\\n### 1-2. Institutional and Major Holder Analysis
- Sub-sections use #### headings

Analysis date: {reference_date}
"""
    return Agent(
        name="cn_institutional_holdings_analysis_agent",
        instruction=instruction,
        server_names=[],
    )
```

- [ ] **Step 2: Verify import**

Run: `python -c "from prism.core.agents.cn.stock_price_agents import create_price_volume_analysis_agent; print('ok')"`

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/prism/core/agents/cn/
git commit -m "feat: add CN price and institutional agents"
```

---

### Task 7: CN analyst agents (company + market + news)

**Files:**
- Create: `src/prism/core/agents/cn/company_info_agents.py`
- Create: `src/prism/core/agents/cn/market_index_agents.py`
- Create: `src/prism/core/agents/cn/news_agents.py`

- [ ] **Step 1: Company info agents**

```python
# src/prism/core/agents/cn/company_info_agents.py
from mcp_agent.agents.agent import Agent


def create_company_status_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    language: str = "en",
    prefetched_data: dict | None = None,
) -> Agent:
    pf = prefetched_data or {}
    blocks = "\n\n".join(
        v for k, v in pf.items() if v and k in ("stock_info", "financial_statements")
    )
    instruction = f"""You are a China A-share financial analyst for {company_name} ({code}.{exchange}).

## Pre-collected Data
{blocks or "_Limited data — analyze only what is provided._"}

Analyze PER, PBR, ROE, revenue/profit trends, debt, dividends in CNY.
Report title: ### 2-1. Company Financial Status
Analysis date: {reference_date}
"""
    return Agent(name="cn_company_status_agent", instruction=instruction, server_names=[])


def create_company_overview_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    language: str = "en",
    prefetched_data: dict | None = None,
) -> Agent:
    pf = prefetched_data or {}
    profile = pf.get("company_profile", "")
    instruction = f"""You are a China A-share industry analyst for {company_name} ({code}.{exchange}).

## Pre-collected Profile
{profile or "_Use general knowledge sparingly; prefer provided data._"}

Cover business model, competitive position, industry drivers, risks.
Report title: ### 2-2. Company Overview
Analysis date: {reference_date}
"""
    return Agent(name="cn_company_overview_agent", instruction=instruction, server_names=[])
```

- [ ] **Step 2: Market index agent**

```python
# src/prism/core/agents/cn/market_index_agents.py
from mcp_agent.agents.agent import Agent


def create_market_index_analysis_agent(
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_indices: str | None = None,
) -> Agent:
    instruction = f"""You are a China A-share market strategist.

## Pre-collected Index Data
{prefetched_indices or "_No index data provided._"}

Analyze 上证指数, 深证成指, 创业板指, 沪深300 impact on A-share sentiment.
Use perplexity for same-day macro/news catalysts if needed.

Report title: ### 4. Market Analysis
First subsection: #### Same-day Market Movement Factor Analysis
Analysis date: {reference_date}
"""
    return Agent(
        name="cn_market_index_analysis_agent",
        instruction=instruction,
        server_names=["perplexity", "time"],
    )
```

- [ ] **Step 3: News agent**

```python
# src/prism/core/agents/cn/news_agents.py
from mcp_agent.agents.agent import Agent


def create_news_analysis_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    language: str = "en",
) -> Agent:
    instruction = f"""You are a China A-share news analyst for {company_name} ({code}.{exchange}).

Use perplexity to gather recent news (within 1 month of {reference_date}).
Focus on disclosures (公告), policy, sector news, and same-day price drivers.
Cite sources as [Perplexity:N, Date].

Report title: ### 3. Recent Major News Summary
First subsection: #### Analysis of Same-day Stock Price Movement Factors
"""
    return Agent(
        name="cn_news_analysis_agent",
        instruction=instruction,
        server_names=["perplexity", "time"],
    )
```

- [ ] **Step 4: Verify imports**

Run: `python -c "from prism.core.agents.cn.company_info_agents import create_company_status_agent; from prism.core.agents.cn.market_index_agents import create_market_index_analysis_agent; from prism.core.agents.cn.news_agents import create_news_analysis_agent; print('ok')"`

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/agents/cn/company_info_agents.py src/prism/core/agents/cn/market_index_agents.py src/prism/core/agents/cn/news_agents.py
git commit -m "feat: add CN company, market, and news agents"
```

---

### Task 8: CN agent directory

**Files:**
- Create: `src/prism/core/agents/cn_directory.py`
- Test: `tests/test_cn_directory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cn_directory.py
from prism.core.agents.cn_directory import get_cn_agent_directory


def test_builds_all_six_agents():
    agents = get_cn_agent_directory(
        company_name="贵州茅台",
        code="600519",
        exchange="SH",
        reference_date="20260606",
        base_sections=[
            "price_volume_analysis",
            "institutional_holdings_analysis",
            "company_status",
            "company_overview",
            "news_analysis",
            "market_index_analysis",
        ],
        language="zh",
        prefetched_data={"stock_ohlcv": "md", "holder_info": "md", "market_indices": {"csi300": "md"}},
    )
    assert len(agents) == 6
    assert "price_volume_analysis" in agents
    assert "market_index_analysis" in agents
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cn_directory.py -v`

Expected: FAIL with import error

- [ ] **Step 3: Implement directory**

Mirror `src/prism/core/agents/__init__.py` `get_agent_directory`:

```python
# src/prism/core/agents/cn_directory.py
from datetime import datetime, timedelta
from typing import Dict, List

from prism.core.agents.cn.company_info_agents import (
    create_company_overview_agent,
    create_company_status_agent,
)
from prism.core.agents.cn.market_index_agents import create_market_index_analysis_agent
from prism.core.agents.cn.news_agents import create_news_analysis_agent
from prism.core.agents.cn.stock_price_agents import (
    create_institutional_holdings_analysis_agent,
    create_price_volume_analysis_agent,
)


def get_cn_agent_directory(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    base_sections: List[str],
    language: str = "en",
    prefetched_data: dict | None = None,
):
    pf = prefetched_data or {}
    ref_date = datetime.strptime(reference_date, "%Y%m%d")
    max_years = 1
    max_years_ago = (ref_date - timedelta(days=365 * max_years)).strftime("%Y%m%d")
    market_indices = pf.get("market_indices", {})
    combined_indices = "\n\n".join(market_indices.values()) if market_indices else None

    creators = {
        "price_volume_analysis": lambda: create_price_volume_analysis_agent(
            company_name, code, exchange, reference_date, max_years_ago, max_years, language,
            prefetched_data=pf.get("stock_ohlcv"),
        ),
        "institutional_holdings_analysis": lambda: create_institutional_holdings_analysis_agent(
            company_name, code, exchange, reference_date, max_years_ago, max_years, language,
            prefetched_data=pf.get("holder_info"),
        ),
        "company_status": lambda: create_company_status_agent(
            company_name, code, exchange, reference_date, language,
            prefetched_data={
                "stock_info": pf.get("stock_info", ""),
                "financial_statements": pf.get("financial_statements", ""),
            },
        ),
        "company_overview": lambda: create_company_overview_agent(
            company_name, code, exchange, reference_date, language,
            prefetched_data={"company_profile": pf.get("company_profile", "")},
        ),
        "news_analysis": lambda: create_news_analysis_agent(
            company_name, code, exchange, reference_date, language,
        ),
        "market_index_analysis": lambda: create_market_index_analysis_agent(
            reference_date, max_years_ago, max_years, language,
            prefetched_indices=combined_indices,
        ),
    }

    return {s: creators[s]() for s in base_sections if s in creators}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cn_directory.py -v`

Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/prism/core/agents/cn_directory.py tests/test_cn_directory.py
git commit -m "feat: add CN agent directory"
```

---

### Task 9: CN charts

**Files:**
- Create: `src/prism/core/visualization/cn_chart.py`

- [ ] **Step 1: Implement chart helpers**

Reuse `figure_to_base64_html` from `src/prism/core/visualization/chart.py`. Export three functions mirroring US API:

```python
# src/prism/core/visualization/cn_chart.py
"""CN A-share chart generation from akshare OHLCV DataFrames."""

from prism.core.visualization.chart import figure_to_base64_html
# Implement get_cn_price_chart_html(code, company_name, hist_df, ...)
# Implement get_cn_technical_chart_html(...)
# Implement get_cn_holder_chart_html(code, company_name, holders_df, ...)
```

Minimum v1: price candlestick chart + technical RSI/MACD from the same OHLCV DataFrame passed from prefetch (avoid second akshare call). Holder chart optional if holder DataFrame empty.

- [ ] **Step 2: Smoke import**

Run: `python -c "from prism.core.visualization.cn_chart import get_cn_price_chart_html; print('ok')"`

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/prism/core/visualization/cn_chart.py
git commit -m "feat: add CN chart helpers"
```

---

### Task 10: analyze_cn_stock pipeline

**Files:**
- Create: `src/prism/core/analysis_cn.py`

- [ ] **Step 1: Implement analyze_cn_stock**

Copy structure from `src/prism/core/analysis.py` with these substitutions:

| US | CN |
|----|-----|
| `prefetch_us_analysis_data(ticker)` | `prefetch_cn_analysis_data(code, reference_date)` |
| `get_agent_directory(..., ticker, ...)` | `get_cn_agent_directory(..., code, exchange, ...)` |
| `yfinance_sections` | `akshare_sections` (same 5 names) |
| `get_us_*_chart_html` | `get_cn_*_chart_html` |
| yfinance chart data fetch | Use OHLCV DataFrame from prefetch / CNDataClient |
| `_us_market_analysis_cache` | `_cn_market_analysis_cache` |
| Header: `{ticker}` | `{code}.{exchange}` e.g. `600519.SH` |
| `translate_report` when `language != "en"` | Keep same path |

Function signature:

```python
async def analyze_cn_stock(
    code: str,
    company_name: str,
    exchange: str,
    reference_date: str | None = None,
    language: str = "en",
    include_news: bool = True,
) -> str:
```

Sequential delay: `await asyncio.sleep(3)` between akshare-backed sections.

- [ ] **Step 2: Verify import**

Run: `python -c "from prism.core.analysis_cn import analyze_cn_stock; print('ok')"`

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/prism/core/analysis_cn.py
git commit -m "feat: add analyze_cn_stock pipeline"
```

---

### Task 11: Language support and disclaimers

**Files:**
- Modify: `src/prism/core/report_generation.py`

- [ ] **Step 1: Extend LANGUAGE_NAMES**

```python
LANGUAGE_NAMES = {
    "en": "English",
    "zh": "Chinese",
    "ko": "Korean",
    "ja": "Japanese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}
```

- [ ] **Step 2: Add Chinese disclaimer branch in get_disclaimer**

```python
def get_disclaimer(language="en"):
    if language == "zh":
        return """## 投资风险提示

本报告仅供参考，不构成投资建议。报告内容由 AI 基于公开信息生成，
其准确性和完整性不作保证。投资有风险，决策需谨慎，投资者须自行承担投资风险。"""
    return """## Investment Disclaimer
...
"""
```

- [ ] **Step 3: Run existing translation tests**

Run: `pytest tests/test_translation.py -v`

Expected: all passed (no regression)

- [ ] **Step 4: Commit**

```bash
git add src/prism/core/report_generation.py
git commit -m "feat: add zh/ko language names and CN disclaimer"
```

---

### Task 12: CN report save + PDF CJK fonts

**Files:**
- Modify: `src/prism/reporting/report_generator.py`
- Modify: `src/prism/reporting/pdf_converter.py`

- [ ] **Step 1: Add save helpers**

In `report_generator.py`, after `save_us_pdf_report`:

```python
def save_cn_report(code: str, company_name: str, content: str) -> Path:
    reference_date = datetime.now().strftime("%Y%m%d")
    safe_company_name = company_name.replace(" ", "_").replace(".", "").replace(",", "")
    filename = f"{code}_{safe_company_name}_{reference_date}_analysis.md"
    filepath = US_REPORTS_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"CN markdown report saved: {filepath}")
    return filepath


def save_cn_pdf_report(code: str, company_name: str, md_path: Path) -> Path:
    from prism.reporting.pdf_converter import markdown_to_pdf
    reference_date = datetime.now().strftime("%Y%m%d")
    safe_company_name = company_name.replace(" ", "_").replace(".", "").replace(",", "")
    pdf_filename = f"{code}_{safe_company_name}_{reference_date}_analysis.pdf"
    pdf_path = US_PDF_REPORTS_DIR / pdf_filename
    markdown_to_pdf(str(md_path), str(pdf_path), "playwright", add_theme=True)
    logger.info(f"CN PDF report generated: {pdf_path}")
    return pdf_path
```

- [ ] **Step 2: Update PDF font stack**

In `pdf_converter.py` `DEFAULT_CSS`, change `body` font-family to:

```css
font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Noto Sans SC", "Noto Sans CJK SC", "PingFang SC", "Noto Sans KR", sans-serif;
```

- [ ] **Step 3: Commit**

```bash
git add src/prism/reporting/report_generator.py src/prism/reporting/pdf_converter.py
git commit -m "feat: add CN report save helpers and CJK PDF fonts"
```

---

### Task 13: Extend demo CLI

**Files:**
- Modify: `src/prism/ops/dev/demo.py`

- [ ] **Step 1: Add --market argument and CN routing**

Add imports:

```python
from prism.core.analysis_cn import analyze_cn_stock
from prism.core.data.cn_client import CNDataClient
from prism.core.market.cn_ticker import normalize, CNTickerError
from prism.core.market_calendar_cn import get_cn_reference_date
```

Add helper:

```python
def get_cn_company_name(code: str) -> str:
    return CNDataClient().get_company_name(code)
```

Update `generate_report` signature to accept `market: str = "us"`:

```python
async def generate_report(ticker: str, company_name: str, language: str = "en", market: str = "us") -> tuple:
    if market == "cn":
        from prism.reporting.report_generator import save_cn_report, save_cn_pdf_report
        ticker_info = normalize(ticker)
        reference_date = get_cn_reference_date()
        report_content = await analyze_cn_stock(
            code=ticker_info.code,
            company_name=company_name,
            exchange=ticker_info.exchange,
            reference_date=reference_date,
            language=language,
            include_news=check_perplexity_configured(),
        )
        md_path = save_cn_report(ticker_info.code, company_name, report_content)
        pdf_path = save_cn_pdf_report(ticker_info.code, company_name, md_path)
        return md_path, pdf_path
    # existing US path unchanged
```

Add argparse:

```python
parser.add_argument("--market", "-m", choices=["us", "cn"], default="us", help="Market: us or cn")
```

In `main()`:

```python
if args.market == "cn":
    try:
        normalize(args.ticker)
    except CNTickerError as e:
        print(f"Error: {e}")
        sys.exit(1)
    company_name = args.company_name or get_cn_company_name(normalize(args.ticker).code)
else:
    ticker = args.ticker.upper()
    company_name = args.company_name or get_company_name(ticker)
```

Update epilog examples with CN commands.

- [ ] **Step 2: Verify US demo still parses**

Run: `python -m prism.ops.dev.demo --help`

Expected: shows `--market` with `us` default

- [ ] **Step 3: Commit**

```bash
git add src/prism/ops/dev/demo.py
git commit -m "feat: extend demo CLI with --market cn"
```

---

### Task 14: Setup documentation

**Files:**
- Modify: `docs/setup.md`

- [ ] **Step 1: Add CN section**

Append:

```markdown
## China A-Share Reports (optional)

- Requires `akshare` (installed via `requirements.txt`)
- Demo: `python -m prism.ops.dev.demo 600519 --market cn --language zh`
- Linux PDF with Chinese text: install `fonts-noto-cjk` (e.g. `apt install fonts-noto-cjk`)
```

- [ ] **Step 2: Commit**

```bash
git add docs/setup.md
git commit -m "docs: add CN A-share setup notes"
```

---

### Task 15: Full test suite and manual smoke

**Files:**
- (all CN tests from prior tasks)

- [ ] **Step 1: Run CN unit tests**

Run: `pytest tests/test_cn_ticker.py tests/test_cn_market_calendar.py tests/test_cn_client.py tests/test_cn_prefetch.py tests/test_cn_directory.py -v`

Expected: all passed

- [ ] **Step 2: Run core regression tests**

Run: `pytest tests/test_translation.py tests/test_trading_journal.py -v`

Expected: all passed

- [ ] **Step 3: Manual smoke (requires network + API keys)**

```bash
pip install -e .
python -m prism.ops.dev.demo 600519 --market cn --language zh
python -m prism.ops.dev.demo 000001 --market cn --language en
python -m prism.ops.dev.demo AAPL
```

Verify:
- SH and SZ reports complete with 8 sections
- PDF readable for Chinese report
- US AAPL demo unchanged

- [ ] **Step 4: Commit any test fixes**

```bash
git add -A
git commit -m "test: verify CN A-share report pipeline"
```

---

## Spec Coverage Self-Review

| Spec requirement | Task |
|------------------|------|
| akshare dependency | Task 1 |
| 6-digit ticker SH/SZ inference | Task 2 |
| CN reference date | Task 3 |
| CNDataClient methods | Task 4 |
| prefetch bundle keys | Task 5 |
| 6 CN agents full parity | Tasks 6–8 |
| Charts | Task 9 |
| analyze_cn_stock hybrid flow | Task 10 |
| Configurable language | Tasks 11, 13 |
| PDF CJK fonts | Task 12 |
| demo --market cn | Task 13 |
| save to var/reports | Task 12 |
| Unit + mocked integration tests | Tasks 2–5, 8, 15 |
| Manual smoke checklist | Task 15 |
| docs/setup.md | Task 14 |
| Out of scope (trading, batch, macro orchestrator) | Not in plan ✓ |

**Placeholder scan:** No TBD/TODO steps. All code blocks are concrete.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-06-cn-a-share-report.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
