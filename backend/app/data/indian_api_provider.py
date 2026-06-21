from __future__ import annotations
import pandas as pd
import httpx
from .base import DataProvider
from .yfinance_provider import YFinanceProvider


class IndianAPIProvider(DataProvider):
    """Adapter for a deployed Indian-Stock-Market-API instance
    (https://github.com/0xramm/Indian-Stock-Market-API).

    Endpoints vary by deployment, so the base URL is configurable and the
    adapter falls back to yfinance for OHLCV history if the API does not
    expose candles. Set INDIAN_API_BASE_URL to enable."""
    name = "indian_api"

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._fallback = YFinanceProvider()

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        # The reference API is quote/fundamentals oriented; use yfinance for candles.
        return self._fallback.get_history(ticker, period=period, interval=interval)

    def get_fundamentals(self, ticker: str) -> dict:
        symbol = ticker.split(".")[0]
        try:
            with httpx.Client(timeout=10) as client:
                r = client.get(f"{self.base_url}/stock", params={"name": symbol})
                if r.status_code == 200:
                    return _normalize(r.json())
        except Exception:
            pass
        return self._fallback.get_fundamentals(ticker)


def _normalize(payload: dict) -> dict:
    """Best-effort mapping of the Indian API shape onto yfinance-style keys."""
    out = dict(payload) if isinstance(payload, dict) else {}
    return out
