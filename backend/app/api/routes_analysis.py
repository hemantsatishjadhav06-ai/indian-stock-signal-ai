from fastapi import APIRouter, Query
from ..config import settings
from ..analysis import signals
from ..core import strategy_engine

router = APIRouter()


@router.get("/regime")
def regime():
    return signals.get_regime()


@router.get("/strategies")
def strategies():
    return strategy_engine.STRATEGIES


@router.get("/analyze/{ticker}")
def analyze(ticker: str):
    return signals.analyze(ticker)


@router.get("/signals")
def scan(tickers: str | None = Query(default=None, description="comma separated; defaults to watchlist")):
    universe = [t.strip() for t in tickers.split(",")] if tickers else settings.watchlist
    return {"regime": signals.get_regime(), "results": signals.scan(universe)}
