"""Internal paper-trading engine (works for any market, incl. NSE/BSE). SQLite-backed."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Session, select


class PaperAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cash: float = 0.0
    starting_cash: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Position(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    qty: float = 0.0
    avg_price: float = 0.0
    strategy: str = ""
    opened_at: datetime = Field(default_factory=datetime.utcnow)


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    side: str = "buy"
    qty: float = 0.0
    price: float = 0.0
    strategy: str = ""
    status: str = "filled"
    realized_pnl: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


def get_account(session: Session) -> PaperAccount:
    from ..config import settings
    acct = session.exec(select(PaperAccount)).first()
    if not acct:
        acct = PaperAccount(cash=settings.starting_cash, starting_cash=settings.starting_cash)
        session.add(acct)
        session.commit()
        session.refresh(acct)
    return acct


def list_positions(session: Session) -> list[Position]:
    return list(session.exec(select(Position)))


def place_order(session: Session, ticker: str, side: str, qty: float, price: float, strategy: str = "") -> dict:
    if qty <= 0 or price <= 0:
        raise ValueError("qty and price must be positive")
    acct = get_account(session)
    side = side.lower()
    pos = session.exec(select(Position).where(Position.ticker == ticker)).first()
    realized = 0.0

    if side == "buy":
        cost = qty * price
        if cost > acct.cash + 1e-6:
            raise ValueError(f"insufficient cash: need {cost:.2f}, have {acct.cash:.2f}")
        acct.cash -= cost
        if pos:
            new_qty = pos.qty + qty
            pos.avg_price = (pos.qty * pos.avg_price + qty * price) / new_qty
            pos.qty = new_qty
        else:
            pos = Position(ticker=ticker, qty=qty, avg_price=price, strategy=strategy)
            session.add(pos)
    elif side == "sell":
        if not pos or pos.qty <= 0:
            raise ValueError(f"no position in {ticker} to sell")
        qty = min(qty, pos.qty)
        proceeds = qty * price
        realized = (price - pos.avg_price) * qty
        acct.cash += proceeds
        pos.qty -= qty
        if pos.qty <= 1e-9:
            session.delete(pos)
    else:
        raise ValueError("side must be 'buy' or 'sell'")

    order = Order(ticker=ticker, side=side, qty=qty, price=price, strategy=strategy, realized_pnl=realized)
    session.add(order)
    session.commit()
    return {"ticker": ticker, "side": side, "qty": qty, "price": price, "realized_pnl": round(realized, 2)}


def portfolio(session: Session, provider) -> dict:
    acct = get_account(session)
    positions = list_positions(session)
    rows, mkt_value, unreal = [], 0.0, 0.0
    for p in positions:
        try:
            last = provider.get_quote(p.ticker).get("price") or p.avg_price
        except Exception:
            last = p.avg_price
        value = p.qty * last
        pnl = (last - p.avg_price) * p.qty
        mkt_value += value
        unreal += pnl
        rows.append({
            "ticker": p.ticker, "qty": p.qty, "avg_price": round(p.avg_price, 2),
            "last": round(last, 2), "value": round(value, 2),
            "unrealized_pnl": round(pnl, 2),
            "unrealized_pct": round((last / p.avg_price - 1) * 100, 2) if p.avg_price else 0.0,
            "strategy": p.strategy,
        })
    equity = acct.cash + mkt_value
    return {
        "cash": round(acct.cash, 2),
        "market_value": round(mkt_value, 2),
        "equity": round(equity, 2),
        "starting_cash": round(acct.starting_cash, 2),
        "total_pnl": round(equity - acct.starting_cash, 2),
        "total_pnl_pct": round((equity / acct.starting_cash - 1) * 100, 2) if acct.starting_cash else 0.0,
        "unrealized_pnl": round(unreal, 2),
        "positions": rows,
    }


def equity(session: Session, provider) -> float:
    return portfolio(session, provider)["equity"]
