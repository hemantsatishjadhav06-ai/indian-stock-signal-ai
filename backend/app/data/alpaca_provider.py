from __future__ import annotations
import pandas as pd
import httpx
from .base import DataProvider


class AlpacaProvider(DataProvider):
    """Optional. US equities / crypto only - NOT Indian stocks.
    Keys come from environment, never hardcoded."""
    name = "alpaca"

    def __init__(self, key_id: str, secret_key: str, base_url: str):
        self.key_id = key_id
        self.secret_key = secret_key
        self.data_url = "https://data.alpaca.markets"

    def _headers(self):
        return {"APCA-API-KEY-ID": self.key_id, "APCA-API-SECRET-KEY": self.secret_key}

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        tf = {"1d": "1Day", "1h": "1Hour", "1m": "1Min"}.get(interval, "1Day")
        try:
            with httpx.Client(timeout=15) as client:
                r = client.get(
                    f"{self.data_url}/v2/stocks/{ticker}/bars",
                    params={"timeframe": tf, "limit": 1000},
                    headers=self._headers(),
                )
                bars = r.json().get("bars", [])
        except Exception:
            bars = []
        if not bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = pd.DataFrame(bars)
        df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume", "t": "date"})
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date")[["open", "high", "low", "close", "volume"]]

    def get_fundamentals(self, ticker: str) -> dict:
        return {}  # Alpaca does not provide fundamentals
