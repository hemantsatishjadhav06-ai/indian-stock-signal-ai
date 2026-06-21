from __future__ import annotations
from functools import lru_cache
from ..config import settings
from .base import DataProvider
from .yfinance_provider import YFinanceProvider
from .indian_api_provider import IndianAPIProvider
from .alpaca_provider import AlpacaProvider
from .twelvedata_provider import TwelveDataProvider


@lru_cache(maxsize=1)
def get_provider() -> DataProvider:
    # Twelve Data works from datacenter IPs (Render); auto-activates with a key.
    if settings.twelvedata_api_key:
        return TwelveDataProvider(settings.twelvedata_api_key)
    if settings.data_provider == "indian_api" and settings.indian_api_base_url:
        return IndianAPIProvider(settings.indian_api_base_url)
    if settings.data_provider == "alpaca" and settings.alpaca_key_id and settings.alpaca_secret_key:
        return AlpacaProvider(settings.alpaca_key_id, settings.alpaca_secret_key, settings.alpaca_base_url)
    return YFinanceProvider()
