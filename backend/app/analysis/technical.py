"""Deterministic technical indicators. Pure pandas/numpy - the LLM never computes these."""
from __future__ import annotations
import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    out = 100 - (100 / (1 + rs))
    out = out.where(avg_loss != 0, 100.0)                       # only gains -> 100
    out = out.where(~((avg_gain == 0) & (avg_loss == 0)), 50.0)  # flat -> neutral
    return out


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    hist = line - sig
    return line, sig, hist


def true_range(df: pd.DataFrame) -> pd.Series:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    return pd.concat([hl, hc, lc], axis=1).max(axis=1)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / period, adjust=False).mean()


def bollinger(close: pd.Series, period: int = 20, k: float = 2.0):
    mid = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    return mid, mid + k * std, mid - k * std


def vwap(df: pd.DataFrame) -> pd.Series:
    """Cumulative VWAP over the supplied window (use a single session for true intraday VWAP)."""
    tp = (df["high"] + df["low"] + df["close"]) / 3
    pv = tp * df["volume"]
    cum_vol = df["volume"].cumsum().replace(0, np.nan)
    return pv.cumsum() / cum_vol


def adx(df: pd.DataFrame, period: int = 14):
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    tr = true_range(df).ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / tr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / tr
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    adx_line = dx.ewm(alpha=1 / period, adjust=False).mean()
    return adx_line, plus_di, minus_di


def _last(s: pd.Series):
    s = s.dropna()
    return float(s.iloc[-1]) if len(s) else None


def snapshot(df: pd.DataFrame) -> dict:
    """Latest values + derived booleans from a daily OHLCV frame."""
    if df is None or len(df) < 30:
        return {"ok": False, "reason": "insufficient history"}

    close = df["close"]
    macd_line, macd_sig, macd_hist = macd(close)
    adx_line, plus_di, minus_di = adx(df)
    bb_mid, bb_up, bb_low = bollinger(close)

    snap = {
        "ok": True,
        "close": _last(close),
        "ema20": _last(ema(close, 20)),
        "ema50": _last(ema(close, 50)),
        "sma50": _last(sma(close, 50)),
        "sma200": _last(sma(close, 200)),
        "rsi14": _last(rsi(close)),
        "macd": _last(macd_line),
        "macd_signal": _last(macd_sig),
        "macd_hist": _last(macd_hist),
        "atr14": _last(atr(df)),
        "adx14": _last(adx_line),
        "plus_di": _last(plus_di),
        "minus_di": _last(minus_di),
        "bb_upper": _last(bb_up),
        "bb_mid": _last(bb_mid),
        "bb_lower": _last(bb_low),
        "vwap": _last(vwap(df)),
    }
    c = snap["close"]
    snap["above_50dma"] = c is not None and snap["sma50"] is not None and c > snap["sma50"]
    snap["above_200dma"] = c is not None and snap["sma200"] is not None and c > snap["sma200"]
    snap["ema_stack_up"] = (
        snap["ema20"] is not None and snap["ema50"] is not None and snap["ema20"] > snap["ema50"]
    )
    snap["macd_bull"] = snap["macd"] is not None and snap["macd"] > snap["macd_signal"]
    snap["trending"] = snap["adx14"] is not None and snap["adx14"] > 20
    snap["di_bull"] = (
        snap["plus_di"] is not None and snap["minus_di"] is not None and snap["plus_di"] > snap["minus_di"]
    )
    return snap


def technical_score(snap: dict, archetype: str = "trend_momentum") -> tuple[float, list[str]]:
    """Transparent 0-100 score. Heuristic + deterministic; tune in backtesting."""
    if not snap.get("ok"):
        return 0.0, ["insufficient data"]
    pts, reasons = 0.0, []
    rsi_v = snap.get("rsi14")

    if archetype == "mean_reversion":
        pts = 20.0
        if snap.get("above_200dma"):
            pts += 15; reasons.append("long-term uptrend intact")
        if rsi_v is not None and rsi_v < 35:
            pts += 25; reasons.append(f"oversold (RSI {rsi_v:.0f})")
        elif rsi_v is not None and rsi_v < 45:
            pts += 12; reasons.append(f"pulling back (RSI {rsi_v:.0f})")
        if snap.get("close") and snap.get("bb_lower") and snap["close"] <= snap["bb_lower"] * 1.01:
            pts += 20; reasons.append("tagging lower Bollinger band")
        if snap.get("adx14") is not None and snap["adx14"] < 20:
            pts += 10; reasons.append("range conditions (ADX<20)")
    else:  # trend_momentum (default), also used by growth/rotation
        pts = 15.0
        if snap.get("above_200dma"):
            pts += 15; reasons.append("above 200DMA")
        if snap.get("above_50dma"):
            pts += 10; reasons.append("above 50DMA")
        if snap.get("ema_stack_up"):
            pts += 10; reasons.append("EMA20>EMA50")
        if rsi_v is not None and 50 <= rsi_v <= 70:
            pts += 15; reasons.append(f"healthy momentum (RSI {rsi_v:.0f})")
        elif rsi_v is not None and rsi_v > 70:
            pts += 5; reasons.append(f"strong but extended (RSI {rsi_v:.0f})")
        if snap.get("macd_bull"):
            pts += 10; reasons.append("MACD bullish")
        if snap.get("trending") and snap.get("di_bull"):
            pts += 15; reasons.append("trending up (ADX>20, +DI>-DI)")
        if snap.get("close") and snap.get("vwap") and snap["close"] > snap["vwap"]:
            pts += 10; reasons.append("above VWAP")
    return float(max(0.0, min(100.0, pts))), reasons
