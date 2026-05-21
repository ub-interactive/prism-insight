import atexit
import textwrap
from pathlib import Path

import pytest

from repo_paths import REPO_ROOT

CONFIG_DIR = REPO_ROOT / "trading" / "config"
CONFIG_FILE = CONFIG_DIR / "kis_devlp.yaml"
_CREATED_TEST_CONFIG = False

if not CONFIG_FILE.exists():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        textwrap.dedent(
            """
            my_agent: test-agent
            default_mode: demo
            auto_trading: true
            default_product_code: "01"
            default_unit_amount: 100000
            default_unit_amount_usd: 250
            my_app: PSREALKEY
            my_sec: real-secret
            paper_app: PSVTTESTKEY
            paper_sec: paper-secret
            my_htsid: test-user
            prod: https://example.com
            vps: https://example.com
            ops: wss://example.com
            vops: wss://example.com
            accounts:
              - name: bootstrap-demo
                mode: demo
                account: "12345678"
                product: "01"
                market: all
                primary: true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    _CREATED_TEST_CONFIG = True


if _CREATED_TEST_CONFIG:
    atexit.register(lambda: CONFIG_FILE.unlink(missing_ok=True))

from trading import kis_auth as ka


def _patch_cfg(monkeypatch, cfg):
    monkeypatch.setattr(ka, "_cfg", cfg, raising=False)
    monkeypatch.setattr(
        ka,
        "DEFAULT_PRODUCT_CODE",
        str(cfg.get("default_product_code", cfg.get("my_prod", "01"))),
        raising=False,
    )
    monkeypatch.setattr(
        ka,
        "DEFAULT_BUY_AMOUNT_USD",
        float(cfg.get("default_unit_amount_usd", 0) or 0),
        raising=False,
    )


def _base_cfg():
    return {
        "default_product_code": "01",
        "default_unit_amount": 100000,
        "default_unit_amount_usd": 250.0,
        "my_prod": "01",
    }


def test_get_configured_accounts_normalizes_filters_and_preserves_overrides(monkeypatch):
    cfg = _base_cfg()
    cfg["accounts"] = [
        {
            "name": "us-demo-alt",
            "mode": "demo",
            "account": "11112222",
            "product": "01",
            "market": "us",
            "buy_amount_usd": 99.0,
        },
        {
            "name": "us-demo-primary",
            "mode": "demo",
            "account": "33334444",
            "product": "01",
            "market": "us",
            "primary": True,
            "buy_amount_usd": 123.45,
        },
        {
            "name": "us-real",
            "mode": "real",
            "account": "55556666",
            "product": "01",
            "market": "us",
        },
    ]
    _patch_cfg(monkeypatch, cfg)

    us_demo_accounts = ka.get_configured_accounts(svr="demo", market="us")

    assert [account["name"] for account in us_demo_accounts] == ["us-demo-alt", "us-demo-primary"]
    assert us_demo_accounts[1]["svr"] == "vps"
    assert us_demo_accounts[1]["account_key"] == "vps:33334444:01"
    assert us_demo_accounts[1]["primary"] is True
    assert us_demo_accounts[1]["buy_amount_usd"] == 123.45


def test_get_configured_accounts_rejects_korean_market(monkeypatch):
    cfg = _base_cfg()
    cfg["accounts"] = [
        {
            "name": "invalid-kr",
            "mode": "demo",
            "account": "11112222",
            "product": "01",
            "market": "kr",
        }
    ]
    _patch_cfg(monkeypatch, cfg)

    with pytest.raises(ValueError, match="Korean domestic market"):
        ka.get_configured_accounts(svr="demo", market="us")


def test_get_configured_accounts_supports_legacy_fallback(monkeypatch):
    cfg = _base_cfg()
    cfg.update(
        {
            "my_acct_stock": "87654321",
            "my_paper_stock": "12345678",
            "my_prod": "01",
        }
    )
    _patch_cfg(monkeypatch, cfg)

    with pytest.warns(DeprecationWarning):
        accounts = ka.get_configured_accounts()

    assert [account["name"] for account in accounts] == [
        "legacy-real-stock",
        "legacy-demo-stock",
    ]
    assert accounts[0]["market"] == "us"
    assert accounts[0]["primary"] is True
    assert accounts[0]["buy_amount_usd"] == 250.0
    assert accounts[1]["account_key"] == "vps:12345678:01"


def test_resolve_account_prefers_primary_then_first(monkeypatch):
    cfg = _base_cfg()
    cfg["accounts"] = [
        {
            "name": "first-us",
            "mode": "demo",
            "account": "10000001",
            "product": "01",
            "market": "us",
        },
        {
            "name": "primary-us",
            "mode": "demo",
            "account": "10000002",
            "product": "01",
            "market": "us",
            "primary": True,
        },
    ]
    _patch_cfg(monkeypatch, cfg)

    primary = ka.resolve_account(svr="vps", market="us")
    assert primary["name"] == "primary-us"

    cfg["accounts"][1]["primary"] = False
    _patch_cfg(monkeypatch, cfg)

    fallback = ka.resolve_account(svr="vps", market="us")
    assert fallback["name"] == "first-us"


def test_resolve_account_supports_account_key(monkeypatch):
    cfg = _base_cfg()
    cfg["accounts"] = [
        {
            "name": "acct-a",
            "mode": "demo",
            "account": "11110000",
            "product": "01",
            "market": "us",
        },
        {
            "name": "acct-b",
            "mode": "demo",
            "account": "22220000",
            "product": "01",
            "market": "us",
        },
    ]
    _patch_cfg(monkeypatch, cfg)

    resolved = ka.resolve_account(
        svr="vps",
        product="01",
        account_key="vps:22220000:01",
        market="us",
    )

    assert resolved["name"] == "acct-b"
    assert resolved["account"] == "22220000"


def test_get_configured_accounts_rejects_unknown_mode(monkeypatch):
    _patch_cfg(monkeypatch, _base_cfg())

    with pytest.raises(ValueError, match="Unknown server mode"):
        ka.get_configured_accounts(svr="staging")


def test_get_configured_accounts_rejects_too_many_accounts(monkeypatch):
    cfg = _base_cfg()
    cfg["accounts"] = [
        {
            "name": f"acct-{index}",
            "mode": "demo",
            "account": f"{10000000 + index}",
            "product": "01",
            "market": "us",
        }
        for index in range(11)
    ]
    _patch_cfg(monkeypatch, cfg)

    with pytest.raises(ValueError, match="Too many accounts configured"):
        ka.get_configured_accounts()
