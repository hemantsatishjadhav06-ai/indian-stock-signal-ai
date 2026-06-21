"""Loads strategies.json and turns indicator + fundamental scores into per-strategy signals.
Score fusion only - all numbers come from deterministic code upstream."""
from __future__ import annotations
import json
import math
from pathlib import Path
import pandas as pd

from ..analysis.technical import snapshot, technical_score

STRAT_PATH = Path(__file__).with_name("strategies.json")

# which technical archetype each strategy uses for scoring
ARCHETYPE = {
    "S1": "trend_momentum", "S2": "trend_momentum", "S4": "trend_momentum",
    "S5": "trend_momentum", "S7": "trend_momentum", "S8": "trend_momentum",
    "S3": "mean_reversion", "S6": "mean_reversion", "S9": "mean_reversion",
}


def load_strategies() -> dict:
    with open(STRAT_PATH) as f:
        return json.load(f)


STRATEGIES = load_strategies()
MIN_SCORE = STRATEGIES.get("score_fusion", {}).get("min_total_score_to_trade", 65)


def detect_regime(df: pd.DataFrame) -> dict:
    snap = snapshot(df)
    if not snap.get("ok"):
        return {"regime": "range", "confidence": 30, "drivers": ["insufficient benchmark data"]}
    close, sma50, sma200, atr14 = snap["close"], snap["sma50"], snap["sma200"], snap["atr14"]
    drivers = []
    atr_pct = (atr14 / close) if (atr14 and close) else 0.0
    ret5 = float(df["close"].pct_change(5).iloc[-1]) if len(df) > 5 else 0.0

    if sma50 and sma200 and close > sma50 > sma200:
        regime, conf = "bullish", 70; drivers.append("price > 50DMA > 200DMA")
    elif sma50 and sma200 and close < sma50 < sma200:
        regime, conf = "bearish", 70; drivers.append("price < 50DMA < 200DMA")
    else:
        regime, conf = "range", 55; drivers.append("moving averages intertwined")

    if atr_pct > 0.035 or abs(ret5) > 0.06:
        regime = "volatile"; conf = 60
        drivers.append(f"elevated volatility (ATR {atr_pct*100:.1f}%/day)")
    return {"regime": regime, "confidence": conf, "drivers": drivers, "atr_pct": round(atr_pct * 100, 2)}


def _gates_ok(sid: str, snap: dict, regime: str, best_regimes: list) -> tuple[bool, list]:
    fails = []
    if regime not in best_regimes and "—" not in best_regimes:
        fails.append(f"regime {regime} not in {best_regimes}")
    arc = ARCHETYPE.get(sid, "trend_momentum")
    if arc == "trend_momentum" and not snap.get("above_50dma"):
        fails.append("price below 50DMA")
    if arc == "mean_reversion":
        rsi = snap.get("rsi14")
        if rsi is None or rsi > 50:
            fails.append("not pulled back (RSI>50)")
    if sid == "S6" and not snap.get("above_200dma"):
        fails.append("200DMA broken (no value-in-uptrend)")
    if sid == "S9" and not (snap.get("adx14") is not None and snap["adx14"] < 20):
        fails.append("ADX not in range conditions")
    return (len(fails) == 0), fails


def evaluate(ticker: str, snap: dict, fundamental: dict, regime: dict) -> list[dict]:
    out = []
    reg = regime.get("regime", "range")
    fscore = fundamental.get("fundamental_score")
    fscore_eff = fscore if fscore is not None else 50.0  # neutral when fundamentals missing
    sentiment = 50.0  # placeholder until a live news/sentiment feed is wired in

    for s in STRATEGIES["strategies"]:
        sid = s["id"]
        arc = ARCHETYPE.get(sid, "trend_momentum")
        tscore, treasons = technical_score(snap, arc)
        best = s.get("best_regimes", [])
        regime_score = 100.0 if reg in best else 40.0
        w = s["score_weights"]
        fused = (
            w.get("technical", 0) * tscore
            + w.get("fundamental", 0) * fscore_eff
            + w.get("regime", 0) * regime_score
            + w.get("news_sentiment", 0) * sentiment
        )
        gates_ok, fails = _gates_ok(sid, snap, reg, best)
        actionable = fused >= MIN_SCORE and gates_ok and snap.get("ok")

        entry = snap.get("close")
        atr = snap.get("atr14")
        stop = target = rr = None
        if entry and atr:
            mult = 1.0 if arc == "mean_reversion" else 1.5
            stop = round(entry - mult * atr, 2)
            rrr = float(s["technical_block"].get("min_reward_to_risk", 1.5)) if "technical_block" in s else 1.5
            target = round(entry + rrr * (entry - stop), 2)
            rr = rrr

        out.append({
            "strategy_id": sid,
            "strategy": s["name"],
            "category": s["category"],
            "bias": "long" if actionable else "no_trade",
            "fused_score": round(fused, 1),
            "technical_score": round(tscore, 1),
            "fundamental_score": round(fscore_eff, 1),
            "regime_fit": reg in best,
            "technical_reasons": treasons,
            "gate_failures": fails,
            "entry": entry, "stop": stop, "target": target, "reward_risk": rr,
        })
    out.sort(key=lambda x: x["fused_score"], reverse=True)
    return out
