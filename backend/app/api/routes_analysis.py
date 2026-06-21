from fastapi import APIRouter, Query
from pydantic import BaseModel
from ..config import settings
from ..analysis import signals
from ..analysis.backtest import run_backtest
from ..data.factory import get_provider
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


class BacktestIn(BaseModel):
    ticker: str
    strategy_id: str = "S5"
    period: str = "2y"
    round_trip_bps: float = 30.0
    start_cash: float = 100000.0


@router.post("/backtest")
def backtest(b: BacktestIn):
    df = get_provider().get_history(b.ticker, period=b.period)
    result = run_backtest(df, b.strategy_id, b.round_trip_bps, b.start_cash)
    return {"ticker": b.ticker, "period": b.period, **result}
