"""Position sizing + risk caps. Risk manager has the final say in the flow."""
from __future__ import annotations
import math
from ..config import settings


def size_position(equity: float, entry: float, stop: float, risk_pct: float | None = None) -> dict:
    risk_pct = risk_pct if risk_pct is not None else settings.risk_per_trade_pct
    if not entry or not stop or entry <= stop:
        return {"shares": 0, "reason": "invalid entry/stop (entry must exceed stop for a long)"}
    risk_amount = equity * risk_pct / 100.0
    per_share = entry - stop
    shares = math.floor(risk_amount / per_share)
    notional = shares * entry
    if notional > equity:                       # cap at available equity (no leverage)
        shares = math.floor(equity / entry)
        notional = shares * entry
    return {
        "shares": int(shares),
        "risk_amount": round(risk_amount, 2),
        "per_share_risk": round(per_share, 2),
        "notional": round(notional, 2),
        "risk_pct": risk_pct,
    }
