from fastapi import APIRouter
from ..config import settings
from ..data.factory import get_provider

router = APIRouter()


@router.get("/universe")
def universe():
    return {"watchlist": settings.watchlist, "benchmark": settings.benchmark,
            "provider": get_provider().name}


@router.get("/quote/{ticker}")
def quote(ticker: str):
    return get_provider().get_quote(ticker)


@router.get("/history/{ticker}")
def history(ticker: str, period: str = "1y"):
    df = get_provider().get_history(ticker, period=period)
    candles = [
        {"date": idx.strftime("%Y-%m-%d"), "open": round(float(r.open), 2),
         "high": round(float(r.high), 2), "low": round(float(r.low), 2),
         "close": round(float(r.close), 2), "volume": float(r.volume)}
        for idx, r in df.iterrows()
    ]
    return {"ticker": ticker, "candles": candles}
