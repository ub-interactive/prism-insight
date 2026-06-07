from dataclasses import dataclass


class CNTickerError(ValueError):
    """Invalid or unsupported A-share ticker."""


@dataclass(frozen=True)
class CNTicker:
    code: str
    exchange: str
    akshare_symbol: str


_SH_PREFIXES = ("60", "68")
_SZ_PREFIXES = ("00", "30")


def normalize(code: str) -> CNTicker:
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
