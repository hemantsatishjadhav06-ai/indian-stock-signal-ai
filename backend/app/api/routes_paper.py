from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from ..db import get_session
from ..data.factory import get_provider
from ..config import settings
from ..trading import paper, risk
from ..analysis import signals

router = APIRouter()


class OrderIn(BaseModel):
    ticker: str
    side: str
    qty: float | None = None
    price: float | None = None
    strategy: str = "manual"


@router.get("/portfolio")
def portfolio(session: Session = Depends(get_session)):
    return paper.portfolio(session, get_provider())


@router.post("/orders")
def place_order(o: OrderIn, session: Session = Depends(get_session)):
    provider = get_provider()
    price = o.price or (provider.get_quote(o.ticker) or {}).get("price")
    if not price:
        raise HTTPException(400, "could not determine price")
    qty = o.qty
    if qty is None:
        eq = paper.equity(session, provider)
        # default size: risk model with a 1.5xATR stop proxy = 3% below price
        sizing = risk.size_position(eq, price, price * 0.97)
        qty = sizing["shares"]
    if not qty or qty <= 0:
        raise HTTPException(400, "computed quantity is zero")
    try:
        return paper.place_order(session, o.ticker, o.side, qty, price, o.strategy)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/scan-and-trade")
def scan_and_trade(session: Session = Depends(get_session)):
    provider = get_provider()
    results = signals.scan(settings.watchlist)
    held = {p.ticker for p in paper.list_positions(session)}
    open_count = len(held)
    eq = paper.equity(session, provider)
    actions = []
    for r in results:
        best = r.get("best")
        if not best or best.get("bias") != "long" or r["ticker"] in held:
            continue
        if open_count >= settings.max_open_positions:
            break
        sizing = risk.size_position(eq, best["entry"], best["stop"])
        if sizing["shares"] <= 0:
            continue
        try:
            paper.place_order(session, r["ticker"], "buy", sizing["shares"], best["entry"], best["strategy"])
        except ValueError:
            continue
        held.add(r["ticker"]); open_count += 1
        actions.append({
            "ticker": r["ticker"], "strategy": best["strategy"], "shares": sizing["shares"],
            "entry": best["entry"], "stop": best["stop"], "target": best["target"],
            "fused_score": best["fused_score"],
        })
    return {"actions": actions, "equity": round(paper.equity(session, provider), 2),
            "note": "Paper only. Signals are not investment advice."}
