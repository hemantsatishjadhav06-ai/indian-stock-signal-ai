from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .api import routes_market, routes_analysis, routes_paper


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Indian Stock AI - Signals & Paper Trading",
    version="0.1.0",
    description="Fundamental + technical signal generation and paper trading for NSE/BSE.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env, "provider": settings.data_provider}


app.include_router(routes_market.router, prefix="/api", tags=["market"])
app.include_router(routes_analysis.router, prefix="/api", tags=["analysis"])
app.include_router(routes_paper.router, prefix="/api", tags=["paper"])
