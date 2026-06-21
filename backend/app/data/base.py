from __future__ import annotations
from abc import ABC, abstractmethod
import pandas as pd


class DataProvider(ABC):
    """All providers return a daily OHLCV DataFrame with columns:
    open, high, low, close, volume - indexed by date."""

    name: str = "base"

    @abstractmethod
    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame: ...

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> dict: ...

    def get_quote(self, ticker: str) -> dict:
        df = self.get_history(ticker, period="5d", interval="1d")
        if df is None or df.empty:
            return {"ticker": ticker, "price": None}
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        price = float(last["close"])
        chg = price - float(prev["close"])
        return {
            "ticker": ticker,
            "price": price,
            "change": chg,
            "change_pct": (chg / float(prev["close"]) * 100) if prev["close"] else None,
            "volume": float(last["volume"]),
        }
