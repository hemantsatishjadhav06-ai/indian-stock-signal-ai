from __future__ import annotations
import pandas as pd
import yfinance as yf
from .base import DataProvider


class YFinanceProvider(DataProvider):
    """Primary provider. Supports NSE (.NS) and BSE (.BO) tickers."""
    name = "yfinance"

    def get_history(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
        df.index = pd.to_datetime(df.index)
        return df.dropna()

    def get_fundamentals(self, ticker: str) -> dict:
        try:
            info = yf.Ticker(ticker).info or {}
        except Exception:
            info = {}
        return info
