"""Fundamental scoring from a provider 'info' dict (e.g. yfinance .info).
Missing data is handled gracefully and never invented."""
from __future__ import annotations


def _num(info: dict, *keys):
    for k in keys:
        v = info.get(k)
        if isinstance(v, (int, float)) and v == v:  # not NaN
            return float(v)
    return None


def _band(v, lo, hi):
    """Map v in [lo,hi] -> [0,100], clamped. lo<hi expected."""
    if v is None:
        return None
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (v - lo) / (hi - lo) * 100.0))


def score_fundamentals(info: dict) -> dict:
    strengths, weaknesses, sub = [], [], {}

    rev_g = _num(info, "revenueGrowth")
    eps_g = _num(info, "earningsGrowth", "earningsQuarterlyGrowth")
    roe = _num(info, "returnOnEquity")
    op_m = _num(info, "operatingMargins")
    gr_m = _num(info, "grossMargins")
    d2e = _num(info, "debtToEquity")
    fcf = _num(info, "freeCashflow")
    fpe = _num(info, "forwardPE")
    tpe = _num(info, "trailingPE")
    peg = _num(info, "pegRatio", "trailingPegRatio")

    growth = _avg([_band(rev_g, 0.0, 0.25), _band(eps_g, 0.0, 0.25)])
    if growth is not None:
        sub["growth"] = growth
        (strengths if growth >= 60 else weaknesses).append(
            f"growth {'strong' if growth >= 60 else 'soft'}"
            + (f" (rev {rev_g*100:.0f}%)" if rev_g is not None else "")
        )

    prof = _avg([_band(roe, 0.05, 0.25), _band(op_m, 0.05, 0.30), _band(gr_m, 0.15, 0.60)])
    if prof is not None:
        sub["profitability"] = prof
        (strengths if prof >= 60 else weaknesses).append(
            f"profitability {'high' if prof >= 60 else 'low'}"
            + (f" (ROE {roe*100:.0f}%)" if roe is not None else "")
        )

    # leverage: lower debt/equity is better. yfinance reports d2e as a percentage (e.g. 45 = 0.45x)
    lev = None
    if d2e is not None:
        ratio = d2e / 100.0 if d2e > 5 else d2e
        lev = max(0.0, min(100.0, (2.0 - ratio) / 2.0 * 100.0))
        sub["leverage"] = lev
        (strengths if lev >= 60 else weaknesses).append(
            f"leverage {'conservative' if lev >= 60 else 'elevated'} (D/E {ratio:.2f})"
        )

    cash = 100.0 if (fcf is not None and fcf > 0) else (0.0 if fcf is not None else None)
    if cash is not None:
        sub["cash_flow"] = cash
        (strengths if cash >= 60 else weaknesses).append(
            "positive free cash flow" if cash >= 60 else "negative free cash flow"
        )

    # valuation view (not folded into the quality score; reported separately)
    val_view, val_score = "unclear", None
    pe = fpe if fpe is not None else tpe
    if peg is not None:
        val_score = max(0.0, min(100.0, (2.0 - peg) / 2.0 * 100.0))
        val_view = "cheap" if peg < 1 else ("fair" if peg < 1.8 else "expensive")
    elif pe is not None:
        val_score = max(0.0, min(100.0, (40.0 - pe) / 40.0 * 100.0))
        val_view = "cheap" if pe < 15 else ("fair" if pe < 28 else "expensive")

    quality = _avg(list(sub.values()))
    return {
        "fundamental_score": round(quality, 1) if quality is not None else None,
        "subscores": {k: round(v, 1) for k, v in sub.items()},
        "valuation_view": val_view,
        "valuation_score": round(val_score, 1) if val_score is not None else None,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "metrics": {
            "revenueGrowth": rev_g, "earningsGrowth": eps_g, "returnOnEquity": roe,
            "operatingMargins": op_m, "grossMargins": gr_m, "debtToEquity": d2e,
            "freeCashflow": fcf, "forwardPE": fpe, "trailingPE": tpe, "pegRatio": peg,
            "marketCap": _num(info, "marketCap"),
        },
        "data_complete": quality is not None and len(sub) >= 3,
    }


def _avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None
