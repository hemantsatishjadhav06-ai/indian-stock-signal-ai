"""Orchestration: fetch data -> indicators + fundamentals -> regime -> per-strategy signals."""
from __future__ import annotations
import time
from ..config import settings
from ..data.factory import get_provider
from .technical import snapshot
from .fundamental import score_fundamentals
from ..core import strategy_engine as eng

_regime_cache = {"ts": 0.0, "val": None}


def get_regime():
    now = time.time()
    if _regime_cache["val"] and now - _regime_cache["ts"] < 900:
        return _regime_cache["val"]
    df = get_provider().get_history(settings.benchmark, period="1y")
    reg = eng.detect_regime(df)
    _regime_cache.update(ts=now, val=reg)
    return reg


def analyze(ticker: str) -> dict:
    provider = get_provider()
    df = provider.get_history(ticker, period="1y")
    snap = snapshot(df)
    info = provider.get_fundamentals(ticker)
    fund = score_fundamentals(info or {})
    regime = get_regime()
    signals = eng.evaluate(ticker, snap, fund, regime)

    history = []
    if df is not None and not df.empty:
        tail = df.tail(180)
        history = [
            {"date": idx.strftime("%Y-%m-%d"), "close": round(float(v), 2)}
            for idx, v in tail["close"].items()
        ]
    return {
        "ticker": ticker,
        "regime": regime,
        "snapshot": snap,
        "fundamental": fund,
        "signals": signals,
        "history": history,
    }


def scan(tickers: list[str]) -> list[dict]:
    results = []
    for t in tickers:
        try:
            r = analyze(t)
            best = r["signals"][0] if r["signals"] else None
            actionable = [s for s in r["signals"] if s["bias"] == "long"]
            results.append({
                "ticker": t,
                "regime": r["regime"]["regime"],
                "fundamental_score": r["fundamental"]["fundamental_score"],
                "best": best,
                "actionable_count": len(actionable),
            })
        except Exception as e:  # noqa: BLE001
            results.append({"ticker": t, "error": str(e)})
    results.sort(key=lambda x: (x.get("best") or {}).get("fused_score", 0), reverse=True)
    return results
