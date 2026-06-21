"""Twelve Data adapter - works from datacenter IPs (Render) where Yahoo is blocked.
Free tier: ~800 calls/day, 8/min. Get a free key at https://twelvedata.com/pricing
and set TWELVEDATA_API_KEY. History powers all technicals/charts/signals; fundamentals
are limited on the free tier."""
from __future__ import annotations
import time
import pandas as pd
import httpx
from .base import DataProvider

_BASE = "https://api.twelvedata.com"
_INDEX_MAP = {"^NSEI": ("NIFTY 50", None), "^BSESN": ("SENSEX", None)}
_COLS = ["open", "high", "low", "close", "volume"]


class TwelveDataProvider(DataProvider):
    name = "twelvedata"

    def __init__(self, api_key: str):
        self.key = api_key
        self._cache: dict = {}
        self._ttl = 300  # seconds

    def _symbol(self, ticker: str):
        if ticker in _INDEX_MAP:
            return _INDEX_MAP[ticker]
        if ticker.endswith(".NS"):
            return ticker[:-3], "NSE"
        if ticker.endswith(".BO"):
            return ticker[:-3], "BSE"
        return ticker, None

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        cache_key = (ticker, period, interval)
        now = time.time()
        hit = self._cache.get(cache_key)
        if hit and now - hit[0] < self._ttl:
            return hit[1]

        sym, exch = self._symbol(ticker)
        td_int = {"1d": "1day", "1h": "1h", "1m": "1min"}.get(interval, "1day")
        out_size = {"1y": 300, "6mo": 160, "3mo": 70, "1mo": 30, "5d": 7}.get(period, 300)
        params = {"symbol": sym, "interval": td_int, "outputsize": out_size,
                  "apikey": self.key, "order": "ASC", "timezone": "Asia/Kolkata"}
        if exch:
            params["exchange"] = exch
        try:
            with httpx.Client(timeout=20) as cl:
                data = cl.get(f"{_BASE}/time_series", params=params).json()
            values = data.get("values") or []
            if not values:
                df = pd.DataFrame(columns=_COLS)
            else:
                df = pd.DataFrame(values)
                df["datetime"] = pd.to_datetime(df["datetime"])
                df = df.set_index("datetime").sort_index()
                for c in _COLS:
                    df[c] = pd.to_numeric(df.get(c), errors="coerce")
                df = df[_COLS].dropna(subset=["close"])
                df["volume"] = df["volume"].fillna(0)
        except Exception:
            df = pd.DataFrame(columns=_COLS)
        self._cache[cache_key] = (now, df)
        return df

    def get_fundamentals(self, ticker: str) -> dict:
        sym, exch = self._symbol(ticker)
        params = {"symbol": sym, "apikey": self.key}
        if exch:
            params["exchange"] = exch
        out: dict = {}
        try:
            with httpx.Client(timeout=15) as cl:
                q = cl.get(f"{_BASE}/quote", params=params).json()
            fw = q.get("fifty_two_week") or {}
            if fw.get("high"):
                out["fiftyTwoWeekHigh"] = float(fw["high"])
            if fw.get("low"):
                out["fiftyTwoWeekLow"] = float(fw["low"])
        except Exception:
            pass
        return out
