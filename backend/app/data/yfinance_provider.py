from __future__ import annotations
import pandas as pd
import yfinance as yf
from .base import DataProvider

# Yahoo throttles datacenter IPs (e.g. Render). A curl_cffi session that
# impersonates Chrome usually restores access. Fall back gracefully if absent.
try:
    from curl_cffi import requests as _cffi
    _SESSION = _cffi.Session(impersonate="chrome")
except Exception:  # pragma: no cover
    _SESSION = None


class YFinanceProvider(DataProvider):
    """Primary provider. Supports NSE (.NS) and BSE (.BO) tickers."""
    name = "yfinance"

    def _ticker(self, ticker: str):
        try:
            return yf.Ticker(ticker, session=_SESSION) if _SESSION else yf.Ticker(ticker)
        except Exception:
            return yf.Ticker(ticker)

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        cols = ["open", "high", "low", "close", "volume"]
        try:
            df = self._ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        except Exception:
            df = None
        if df is None or df.empty:
            return pd.DataFrame(columns=cols)
        df = df.rename(columns=str.lower)[cols]
        df.index = pd.to_datetime(df.index)
        return df.dropna()

    def get_fundamentals(self, ticker: str) -> dict:
        try:
            return self._ticker(ticker).info or {}
        except Exception:
            return {}
