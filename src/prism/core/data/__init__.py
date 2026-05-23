"""Data access layer — yfinance client, prefetch, surge detection, social sentiment."""

from prism.core.data.client import USDataClient, get_us_data_client

__all__ = [
    "USDataClient",
    "get_us_data_client",
]
