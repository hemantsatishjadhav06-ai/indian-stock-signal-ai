import numpy as np
import pandas as pd
from app.analysis import technical as ta
from app.analysis.fundamental import score_fundamentals
from app.trading.risk import size_position


def ohlc_from_close(close):
    close = pd.Series(close, dtype=float)
    return pd.DataFrame({"open": close, "high": close * 1.01, "low": close * 0.99,
                         "close": close, "volume": np.full(len(close), 1000.0)})


def test_rsi_all_gains_is_100():
    rsi = ta.rsi(pd.Series(np.arange(1, 60, dtype=float)))
    assert round(rsi.iloc[-1], 6) == 100.0


def test_rsi_bounds():
    rng = np.random.default_rng(0)
    rsi = ta.rsi(pd.Series(rng.normal(100, 5, 200).cumsum() + 500))
    assert rsi.dropna().between(0, 100).all()


def test_macd_constant_is_zero():
    line, sig, hist = ta.macd(pd.Series([100.0] * 60))
    assert abs(line.iloc[-1]) < 1e-9 and abs(hist.iloc[-1]) < 1e-9


def test_atr_constant_is_zero():
    df = pd.DataFrame({"open": [100.0]*40, "high": [100.0]*40, "low": [100.0]*40,
                       "close": [100.0]*40, "volume": [1.0]*40})
    assert abs(ta.atr(df).iloc[-1]) < 1e-9


def test_bollinger_constant_collapses():
    mid, up, low = ta.bollinger(pd.Series([100.0] * 40))
    assert abs(up.iloc[-1] - low.iloc[-1]) < 1e-9


def test_vwap_constant_price():
    df = ohlc_from_close([100.0] * 30)
    df["high"] = 100.0; df["low"] = 100.0
    assert abs(ta.vwap(df).iloc[-1] - 100.0) < 1e-6


def test_adx_uptrend_di_and_bounds():
    df = ohlc_from_close(np.arange(1, 120, dtype=float))
    adx_line, plus_di, minus_di = ta.adx(df)
    assert plus_di.iloc[-1] > minus_di.iloc[-1]
    assert adx_line.dropna().between(0, 100).all()


def test_snapshot_and_scores():
    df = ohlc_from_close(np.linspace(100, 300, 260))  # strong uptrend
    snap = ta.snapshot(df)
    assert snap["ok"] and snap["above_200dma"] and snap["ema_stack_up"]
    trend, _ = ta.technical_score(snap, "trend_momentum")
    mr, _ = ta.technical_score(snap, "mean_reversion")
    assert 0 <= trend <= 100 and 0 <= mr <= 100 and trend > mr


def test_fundamentals_strong_vs_weak_vs_missing():
    strong = score_fundamentals({"revenueGrowth": 0.30, "earningsGrowth": 0.30,
        "returnOnEquity": 0.25, "operatingMargins": 0.30, "grossMargins": 0.60,
        "debtToEquity": 20, "freeCashflow": 1e9, "forwardPE": 18})
    weak = score_fundamentals({"revenueGrowth": -0.05, "earningsGrowth": -0.10,
        "returnOnEquity": 0.02, "operatingMargins": 0.02, "grossMargins": 0.10,
        "debtToEquity": 250, "freeCashflow": -1e8, "forwardPE": 90})
    missing = score_fundamentals({})
    assert strong["fundamental_score"] > 60
    assert weak["fundamental_score"] < 45
    assert missing["fundamental_score"] is None and missing["data_complete"] is False


def test_position_sizing_matches_worked_example():
    s = size_position(equity=50000, entry=20.0, stop=19.5, risk_pct=0.5)
    assert s["shares"] == 500 and s["risk_amount"] == 250.0
