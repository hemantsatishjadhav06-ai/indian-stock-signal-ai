"""Cost-aware backtester over daily bars.

Models EOD execution at the signal bar's close, with stops/targets checked on
later bars' high/low (gap-aware). Costs are charged as a single round-trip in
basis points, which captures Indian frictions (brokerage + STT + exchange +
GST + stamp + slippage). Intraday strategies are approximated on daily bars and
labelled as such. Deterministic - no look-ahead beyond the executing close."""
from __future__ import annotations
import numpy as np
import pandas as pd

from .technical import sma, ema, rsi, atr, macd, bollinger
from ..core.strategy_engine import ARCHETYPE


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    c = d["close"]
    d["sma50"] = sma(c, 50); d["sma200"] = sma(c, 200)
    d["ema20"] = ema(c, 20); d["ema50"] = ema(c, 50)
    d["rsi"] = rsi(c); d["atr"] = atr(d)
    ml, sg, _ = macd(c); d["macd"] = ml; d["macd_sig"] = sg
    bbm, _, bbl = bollinger(c); d["bbm"] = bbm; d["bbl"] = bbl
    return d.dropna()


def _entry(row, arc: str) -> bool:
    if arc == "mean_reversion":
        return (row.close > row.sma200) and (row.rsi < 35) and (row.close <= row.bbl * 1.02)
    return ((row.close > row.sma50 > row.sma200) and (row.ema20 > row.ema50)
            and (50 <= row.rsi <= 72) and (row.macd > row.macd_sig))


def run_backtest(df: pd.DataFrame, strategy_id: str, round_trip_bps: float = 30.0,
                 start_cash: float = 100000.0) -> dict:
    arc = ARCHETYPE.get(strategy_id, "trend_momentum")
    d = _prep(df)
    if len(d) < 60:
        return {"error": "insufficient history for a backtest (need ~60+ daily bars)"}

    cost = round_trip_bps / 10000.0
    rr = 1.5 if arc == "mean_reversion" else 2.0
    stop_mult = 1.5 if arc == "mean_reversion" else 2.0
    max_hold = 15 if arc == "mean_reversion" else 40

    rows = list(d.itertuples())
    n = len(rows)
    c0 = rows[0].close
    equity = start_cash
    eq_dates, eq_vals, bh_vals = [], [], []
    trades = []
    in_pos = False
    entry = stop = target = 0.0
    entry_i = 0
    entry_date = None
    exposure = 0

    for i, row in enumerate(rows):
        if in_pos:
            exit_price, reason = None, None
            if row.low <= stop:
                exit_price = min(row.open, stop); reason = "stop"
            elif row.high >= target:
                exit_price = max(row.open, target); reason = "target"
            elif arc == "trend_momentum" and row.close < row.sma50:
                exit_price, reason = row.close, "trend_break"
            elif arc == "mean_reversion" and row.rsi > 55:
                exit_price, reason = row.close, "revert"
            elif (i - entry_i) >= max_hold:
                exit_price, reason = row.close, "time"
            if exit_price is not None:
                net = (exit_price / entry - 1.0) - cost
                equity *= (1.0 + net)
                trades.append({"entry_date": entry_date, "exit_date": str(row.Index.date()),
                               "entry": round(entry, 2), "exit": round(exit_price, 2),
                               "ret_pct": round(net * 100, 2), "bars": i - entry_i, "reason": reason})
                in_pos = False
        elif _entry(row, arc) and row.atr > 0 and i < n - 1:
            entry, entry_i, entry_date = row.close, i, str(row.Index.date())
            stop = entry - stop_mult * row.atr
            target = entry + rr * (entry - stop)
            in_pos = True

        mtm = equity * (row.close / entry) if in_pos else equity
        if in_pos:
            exposure += 1
        eq_vals.append(mtm)
        bh_vals.append(start_cash * row.close / c0)
        eq_dates.append(str(row.Index.date()))

    if in_pos:
        last = rows[-1]
        net = (last.close / entry - 1.0) - cost
        equity *= (1.0 + net)
        trades.append({"entry_date": entry_date, "exit_date": str(last.Index.date()),
                       "entry": round(entry, 2), "exit": round(last.close, 2),
                       "ret_pct": round(net * 100, 2), "bars": n - 1 - entry_i, "reason": "open_end"})
        eq_vals[-1] = equity

    rets = [t["ret_pct"] for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    eq = pd.Series(eq_vals)
    dd = (eq / eq.cummax() - 1.0)
    days = max((d.index[-1] - d.index[0]).days, 1)
    total = equity / start_cash - 1.0
    cagr = (equity / start_cash) ** (365.0 / days) - 1.0 if equity > 0 else None
    bh = rows[-1].close / c0 - 1.0
    daily_ret = eq.pct_change().dropna()
    sharpe = float(np.sqrt(252) * daily_ret.mean() / daily_ret.std()) if daily_ret.std() else None

    metrics = {
        "strategy_id": strategy_id, "archetype": arc,
        "trades": len(trades),
        "win_rate": round(len(wins) / len(trades) * 100, 1) if trades else 0.0,
        "avg_win_pct": round(float(np.mean(wins)), 2) if wins else 0.0,
        "avg_loss_pct": round(float(np.mean(losses)), 2) if losses else 0.0,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 2) if losses and sum(losses) != 0 else None,
        "expectancy_pct": round(float(np.mean(rets)), 2) if rets else 0.0,
        "total_return_pct": round(total * 100, 1),
        "cagr_pct": round(cagr * 100, 1) if cagr is not None else None,
        "max_drawdown_pct": round(float(dd.min()) * 100, 1),
        "sharpe": round(sharpe, 2) if sharpe is not None else None,
        "exposure_pct": round(exposure / n * 100, 1),
        "buy_hold_pct": round(bh * 100, 1),
        "ending_equity": round(equity, 0),
        "start_cash": start_cash, "round_trip_bps": round_trip_bps,
        "intraday_note": arc == "trend_momentum" and strategy_id in {"S1", "S2", "S4"},
    }

    # downsample curves for charting (~180 points)
    step = max(1, len(eq_dates) // 180)
    curve = [{"date": eq_dates[k], "strategy": round(eq_vals[k]), "buy_hold": round(bh_vals[k])}
             for k in range(0, len(eq_dates), step)]
    if curve and curve[-1]["date"] != eq_dates[-1]:
        curve.append({"date": eq_dates[-1], "strategy": round(eq_vals[-1]), "buy_hold": round(bh_vals[-1])})

    return {"metrics": metrics, "equity_curve": curve, "trades": trades[-60:]}
