# Indian Stock AI — Signals & Paper Trading

An auto **signal generator** that scores NSE/BSE stocks with **fundamental + technical analysis** (kept separate, by design), turns the scores into trade setups from a library of **9 strategies**, and simulates them in a **paper-trading** book. FastAPI backend, React + Tailwind frontend, deploys to Render.

> ⚠️ **Educational tool, not investment advice.** Signals come from deterministic rules and scoring — they carry no guaranteed edge. Trading is risky. The app is **paper-only by default**; live broker execution is opt-in and disabled until you wire it up yourself. Validate everything with backtests and out-of-sample testing before risking real money.

---

## What it does

- **Scans a watchlist** and scores every stock with all 9 strategies.
- **Separates the two lenses everywhere:** a *fundamental* score (growth, profitability, leverage, cash flow, valuation) and a *technical* score (trend, momentum, RSI/MACD/ADX, location vs VWAP/MAs).
- **Detects the market regime** (bullish / bearish / range / volatile) from the NIFTY benchmark and gates strategies to the regimes they fit.
- **Generates setups** with entry, ATR-based stop, and reward-based target.
- **Paper-trades** approved long setups, sizing each position with a 0.5%-risk model, and tracks P&L.
- **Research tab** with hand-built deep dives whose numbers are fact-checked against primary sources (ships with a Sandur Manganese example).

## Architecture

```
┌─────────────┐   REST/JSON   ┌──────────────────────────────────────────┐
│  React SPA  │ ─────────────▶│  FastAPI backend                          │
│ (Vite+TW)   │               │   data adapters → indicators (pandas)     │
│  Recharts   │◀───────────── │   + fundamentals → strategy engine        │
└─────────────┘               │   → paper broker (SQLite) + risk model    │
   Render static              └──────────────────────────────────────────┘
                                   │ data
                          ┌────────┴─────────┬─────────────┐
                       yfinance (.NS/.BO)  Indian-Stock   Alpaca (US/crypto,
                       — primary           -Market-API     optional)
```

All numbers (indicators, scores, sizing, P&L) are computed in **deterministic Python** — the design never asks an LLM to do arithmetic.

## The 9 strategies

Intraday: **S1** Opening Range Breakout · **S2** VWAP Trend Pullback · **S3** Liquidity Sweep Reversal (SMC) · **S4** Flag/Pennant Momentum.
Swing: **S5** Quality-Growth Base Breakout · **S6** Value Pullback in Uptrend · **S7** Post-Earnings Drift · **S8** Sector Rotation RS.
Mean reversion: **S9** Range/Risk-Off.

Each strategy is defined in `backend/app/core/strategies.json` with a **fundamental block** and a **technical block** kept separate, plus regime fit, score-fusion weights, gates, entry/stop/target, and skip rules. (Full write-up: the *Strategy Library* document.)

## Tech stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Uvicorn, pandas/numpy, SQLModel (SQLite), httpx |
| Data | yfinance (primary), Indian-Stock-Market-API adapter, Alpaca adapter (optional) |
| Frontend | React 18, Vite, Tailwind CSS, Recharts |
| Infra | Docker, docker-compose, Render Blueprint, GitHub Actions CI |

## Repository structure

```
indian-stock-signal-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # env-driven settings
│   │   ├── db.py                # SQLite engine
│   │   ├── analysis/            # technical.py, fundamental.py, signals.py
│   │   ├── core/                # strategies.json + strategy_engine.py
│   │   ├── data/                # provider adapters + factory
│   │   ├── trading/             # paper broker + risk model
│   │   └── api/                 # routes_market / routes_analysis / routes_paper
│   ├── tests/                   # indicator + sizing tests (pytest)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # Vite React + Tailwind dashboard
│   ├── src/components/          # Signals, TickerDetail, Portfolio, Strategies, Research
│   └── public/research/         # research JSON (Sandur Manganese example)
├── render.yaml                  # one-click Render Blueprint
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Run locally

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # edit if needed
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
pytest -q                       # run the test suite
```

**Frontend**
```bash
cd frontend
cp .env.example .env            # VITE_API_BASE=http://localhost:8000
npm install
npm run dev                     # http://localhost:5173
```

**Or everything at once**
```bash
docker compose up --build
```

## Environment variables

| Variable | Where | Default | Notes |
|---|---|---|---|
| `DATA_PROVIDER` | backend | `yfinance` | `yfinance` \| `indian_api` \| `alpaca` |
| `INDIAN_API_BASE_URL` | backend | — | URL of a deployed Indian-Stock-Market-API instance |
| `ALPACA_KEY_ID` / `ALPACA_SECRET_KEY` | backend | — | **US/crypto only**, optional. Env only — never commit |
| `BENCHMARK` | backend | `^NSEI` | regime detection index |
| `CORS_ORIGINS` | backend | `*` | set to your frontend URL in production |
| `STARTING_CASH` | backend | `1000000` | paper account (₹10 lakh) |
| `RISK_PER_TRADE_PCT` | backend | `0.5` | position-sizing risk |
| `DB_URL` | backend | `sqlite:///./trading.db` | use Render Postgres for persistence |
| `VITE_API_BASE` | frontend | `http://localhost:8000` | backend URL |

### 🔐 Security
Never commit API keys. Keys live only in `.env` (git-ignored) or your host's secret manager. If a key is ever exposed, **rotate it immediately** in the provider dashboard.

## Deploy to Render

**Blueprint (recommended)**
1. Push this repo to GitHub.
2. Render → **New → Blueprint** → pick the repo. It reads `render.yaml` and creates two services: `stock-ai-backend` (Docker) and `stock-ai-frontend` (static).
3. After both deploy, set the two cross-URLs:
   - Backend env `CORS_ORIGINS` → your frontend URL (e.g. `https://stock-ai-frontend.onrender.com`)
   - Frontend env `VITE_API_BASE` → your backend URL (e.g. `https://stock-ai-backend.onrender.com`)
4. Redeploy the frontend so the new `VITE_API_BASE` is baked into the build.

Free tier spins services down when idle (first request is slow) and SQLite is ephemeral — for a persistent paper book, attach **Render Postgres** and point `DB_URL` at it.

## API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/api/universe` | watchlist + benchmark + provider |
| GET | `/api/regime` | current market regime |
| GET | `/api/strategies` | the 9 strategies (JSON) |
| GET | `/api/analyze/{ticker}` | full fundamental + technical + per-strategy signals + price history |
| GET | `/api/signals?tickers=` | scan watchlist (or a CSV list) |
| GET | `/api/quote/{ticker}` · `/api/history/{ticker}` | price data |
| GET | `/api/portfolio` | paper account + positions + P&L |
| POST | `/api/orders` | place a paper order (auto-sizes if `qty` omitted) |
| POST | `/api/scan-and-trade` | scan and paper-buy approved long setups |

## Roadmap / reality checks

- Wire a real **intraday feed** (Alpaca/Polygon/broker) — the 1-minute strategies (S1–S4) are approximated on daily bars until then.
- Add a **cost-aware backtester** (slippage, brokerage, STT) and require walk-forward + out-of-sample passes before any strategy goes live.
- Live **news/sentiment** agent (currently a neutral placeholder).
- Optional **Zerodha Kite** adapter for Indian data + execution.

## License
MIT — see [LICENSE](LICENSE).
