import pytest

from prism.core.cn.market.ticker import CNTicker, normalize, CNTickerError


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
