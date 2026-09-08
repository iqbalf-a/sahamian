"""Backend aplikasi analisis saham IDX. Jalankan lewat: uvicorn app.server:api"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine  # noqa: E402
import market  # noqa: E402
import news  # noqa: E402
import screeners  # noqa: E402
from stats import bootstrap_metrics, permute_drawdown_returns  # noqa: E402

api = FastAPI(title="IDX Stock Analysis")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/api/health")
def health():
    return {"ok": True, "tickers": len(engine.available_tickers())}


@api.get("/api/tickers")
def tickers():
    names = engine.ticker_names()
    return {
        "universe": engine.universe_tickers(),
        "extra": engine.extra_tickers(),
        "names": {t: names.get(t, {}).get("name", "") for t in engine.available_tickers()},
    }


@api.get("/api/search")
def search(q: str, remote: bool = True):
    """Saran saham: cocokkan kode ATAU nama perusahaan. Yang sudah ada datanya didahulukan;
    kalau kurang dari 5, dilengkapi hasil pencarian yfinance ke seluruh emiten IDX."""
    q = q.strip()
    if len(q) < 1:
        return {"results": []}
    local = engine.search_local(q)
    results = list(local)
    if remote and len(local) < 5 and len(q) >= 2:
        results += engine.search_remote(q, limit=8 - len(local))
    return {"results": results}


@api.get("/api/screen")
def screen(lookback: int = 6, top_n: int = 9):
    lookback = max(1, min(24, lookback))
    top_n = max(1, min(30, top_n))
    return engine.screen(lookback_months=lookback, top_n=top_n)


@api.get("/api/briefing")
def briefing(refresh: bool = False):
    return news.briefing(refresh=refresh)


@api.post("/api/briefing/ai")
def briefing_ai():
    data = news.briefing()
    try:
        return news.ai_analysis(data["movers"], data["headlines"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Panggilan AI gagal: {type(e).__name__}: {e}")


@api.get("/api/home/tabs")
def home_tabs():
    return {"tabs": market.list_tabs()}


@api.get("/api/home")
def home(tab: str = "gainer", limit: int = 30):
    try:
        return market.home_list(tab, limit=max(5, min(100, limit)))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"tab '{tab}' tidak dikenal")


@api.get("/api/calendar")
def calendar(symbol: str = "IHSG", year: int | None = None):
    try:
        data = market.calendar(symbol, year)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not data:
        raise HTTPException(status_code=404, detail=f"data {symbol} tidak ada")
    return data


@api.get("/api/actions/{ticker}")
def actions(ticker: str):
    try:
        return market.corporate_actions(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api.get("/api/screen/templates")
def screen_templates():
    return {"templates": screeners.list_templates()}


@api.get("/api/screen/run/{template_id}")
def screen_run(template_id: str, days: int = 504):
    try:
        if template_id in ("overnight", "intraday"):
            return screeners.run(template_id, days=max(120, min(2000, days)))
        return screeners.run(template_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"template '{template_id}' tidak dikenal")


@api.get("/api/stock/{ticker}")
def stock(ticker: str, bars: int = 500):
    try:
        detail = engine.stock_detail(ticker, bars=max(60, min(2500, bars)))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if detail is None:
        raise HTTPException(status_code=404, detail=f"{ticker} belum ada di data lokal")
    return detail


@api.post("/api/fetch/{ticker}")
def fetch(ticker: str):
    """Tarik saham baru dari yfinance ke universe lokal."""
    try:
        df = engine.fetch_ticker(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if df is None:
        raise HTTPException(status_code=404, detail=f"{ticker}.JK tidak ditemukan / data terlalu pendek")
    return {"ticker": engine.valid_ticker(ticker), "bars": len(df)}


class BacktestRequest(BaseModel):
    lookback_months: int = Field(6, ge=1, le=24)
    top_n: int = Field(9, ge=1, le=30)
    cost_buy_pct: float = Field(0.20, ge=0, le=2)
    cost_sell_pct: float = Field(0.30, ge=0, le=2)
    capital0: float = Field(100_000_000, ge=1_000_000, le=100_000_000_000)
    start: str = engine.EXPLORE_START
    end: str = engine.EXPLORE_END
    require_positive_momentum: bool = True
    tickers: list[str] | None = None


@api.post("/api/backtest")
def backtest(req: BacktestRequest):
    params = engine.BacktestParams(
        lookback_months=req.lookback_months,
        top_n=req.top_n,
        cost_buy=req.cost_buy_pct / 100,
        cost_sell=req.cost_sell_pct / 100,
        capital0=req.capital0,
        start=req.start,
        end=req.end,
        require_positive_momentum=req.require_positive_momentum,
        tickers=req.tickers,
    )
    result = engine.momentum_backtest(params)
    if not result.months:
        raise HTTPException(status_code=400, detail="tidak ada bulan dalam rentang tersebut")

    # statistik dijalankan atas RETURN bulanan (%), bukan rupiah — supaya tidak
    # terdistorsi oleh pemajemukan modal (lihat stats.permute_drawdown_returns)
    rets = np.array(result.returns, dtype=float)
    boot = {
        b.metric: {
            "observed": round(b.observed, 3),
            "ci_low": round(b.ci_low, 3),
            "ci_high": round(b.ci_high, 3),
            "prob_above": round(b.prob_above, 4) if b.prob_above is not None else None,
        }
        for b in bootstrap_metrics(rets * 100, n_iter=5_000)
    }
    dd = permute_drawdown_returns(rets, n_iter=2_000)

    return {
        "params": req.model_dump(),
        "metrics": result.metrics,
        "yearly": result.yearly,
        "months": result.months,
        "benchmark": result.benchmark,
        "bootstrap": boot,
        "drawdown_permutation": {k: round(v, 2) for k, v in dd.items()},
        "vault_touched": req.end > engine.EXPLORE_END,
    }


@api.get("/api/walkforward")
def walkforward():
    """Hasil eksperimen 002 (pra-hitung — grid 36 sel + walk-forward butuh ~3 menit)."""
    path = Path(__file__).resolve().parents[1] / "experiments" / "002_walkforward" / "results.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="jalankan experiments/002_walkforward/walkforward.py dulu")
    return json.loads(path.read_text(encoding="utf-8"))


@api.get("/api/config")
def config():
    return {
        "explore": {"start": engine.EXPLORE_START, "end": engine.EXPLORE_END},
        "vault_start": engine.VAULT_START,
        "cost_note": "beli 0,20% + jual 0,30% (broker retail tipikal)",
    }
