"""
Data pasar untuk menu Utama aplikasi: daftar top gainer/loser/trending, kalender
untung-rugi, dan corporate action.

Terpisah dari `engine.py` (yang berisi strategi & backtest) karena isinya murni penyajian
data pasar, bukan riset.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import engine

INDEX_DIR = Path(__file__).parent / "data_index"
ACTIONS_DIR = Path(__file__).parent / "data_actions"
ACTIONS_DIR.mkdir(exist_ok=True)
ACTIONS_TTL_DAYS = 7


# --------------------------------------------------------------------------- indeks

def load_index(symbol: str = "IHSG") -> pd.DataFrame | None:
    path = INDEX_DIR / f"{symbol}.csv"
    if not path.exists():
        return None
    return pd.read_csv(path, index_col=0, parse_dates=True).sort_index()


def load_any(symbol: str) -> pd.DataFrame | None:
    """IHSG atau saham biasa."""
    if symbol.upper() == "IHSG":
        return load_index()
    return engine.load_prices(symbol)


# ------------------------------------------------------------------ daftar Utama

def _snapshot() -> list[dict]:
    names = engine.ticker_names()
    universe = set(engine.UNIVERSE)
    rows = []
    for t in engine.available_tickers():
        df = engine.load_prices(t)
        if df is None or len(df) < 60:
            continue
        c = df["Close"]
        last, prev = float(c.iloc[-1]), float(c.iloc[-2])
        value_today = float(c.iloc[-1] * df["Volume"].iloc[-1])
        value_avg20 = float((c * df["Volume"]).iloc[-21:-1].mean())
        vol_avg20 = float(df["Volume"].iloc[-21:-1].mean())
        rows.append({
            "ticker": t,
            "name": names.get(t, {}).get("name", ""),
            "price": round(last, 2),
            "change_pct": round((last / prev - 1) * 100, 2),
            "value_bn": round(value_today / 1e9, 2),
            "volume_ratio": round(float(df["Volume"].iloc[-1]) / vol_avg20, 2) if vol_avg20 > 0 else None,
            "value_ratio": round(value_today / value_avg20, 2) if value_avg20 > 0 else None,
            "ret_1m_pct": round(float(c.iloc[-1] / c.iloc[-22] - 1) * 100, 1) if len(c) > 22 else None,
            "from_high52_pct": round((last / float(c.tail(252).max()) - 1) * 100, 1),
            "from_low52_pct": round((last / float(c.tail(252).min()) - 1) * 100, 1),
            "in_universe": t in universe,
            "last_date": df.index[-1].strftime("%Y-%m-%d"),
        })
    return rows


COLUMNS = [
    {"key": "ticker", "label": "Saham", "format": "ticker", "align": "left"},
    {"key": "name", "label": "Nama", "format": "text", "align": "left"},
    {"key": "price", "label": "Harga", "format": "price"},
    {"key": "change_pct", "label": "Perubahan", "format": "pct", "digits": 2, "good": "high"},
    {"key": "value_bn", "label": "Nilai transaksi", "format": "num", "digits": 1,
     "hint": "Rp miliar hari ini"},
    {"key": "value_ratio", "label": "vs rata² 20h", "format": "ratio", "digits": 2, "good": "high",
     "hint": "nilai transaksi hari ini dibanding rata-rata 20 hari"},
    {"key": "ret_1m_pct", "label": "1 bulan", "format": "pct", "digits": 1, "good": "high"},
]

TABS = {
    "gainer": {
        "name": "Top gainer",
        "sort": lambda r: -r["change_pct"],
        "note": "Kenaikan harga terbesar pada hari perdagangan terakhir.",
    },
    "loser": {
        "name": "Top loser",
        "sort": lambda r: r["change_pct"],
        "note": "Penurunan harga terbesar pada hari perdagangan terakhir.",
    },
    "trending": {
        "name": "Trending",
        "sort": lambda r: -(r["value_ratio"] or 0),
        "note": ("Nilai transaksi hari ini dibanding rata-rata 20 hari — proksi 'ramai'. "
                 "Ini BUKAN data trending media sosial; hanya lonjakan aktivitas transaksi."),
    },
    "aktif": {
        "name": "Teraktif",
        "sort": lambda r: -r["value_bn"],
        "note": "Nilai transaksi terbesar hari ini (Rp miliar).",
    },
    "high52": {
        "name": "Dekat tertinggi 52m",
        "sort": lambda r: -r["from_high52_pct"],
        "note": "Harga paling dekat dengan tertinggi 52 minggu.",
    },
    "low52": {
        "name": "Dekat terendah 52m",
        "sort": lambda r: r["from_low52_pct"],
        "note": "Harga paling dekat dengan terendah 52 minggu.",
    },
}


def home_list(tab: str = "gainer", limit: int = 30) -> dict:
    if tab not in TABS:
        raise KeyError(tab)
    rows = _snapshot()
    meta = TABS[tab]
    rows.sort(key=meta["sort"])
    cols = list(COLUMNS)
    if tab == "high52":
        cols = cols + [{"key": "from_high52_pct", "label": "Dari tertinggi 52m", "format": "pct", "digits": 1}]
    elif tab == "low52":
        cols = cols + [{"key": "from_low52_pct", "label": "Dari terendah 52m", "format": "pct", "digits": 1}]

    idx = load_index()
    index_info = None
    if idx is not None and len(idx) > 1:
        c = idx["Close"]
        index_info = {
            "symbol": "IHSG",
            "value": round(float(c.iloc[-1]), 2),
            "change_pct": round(float(c.iloc[-1] / c.iloc[-2] - 1) * 100, 2),
            "last_date": idx.index[-1].strftime("%Y-%m-%d"),
        }

    return {
        "tab": tab,
        "name": meta["name"],
        "note": meta["note"],
        "columns": cols,
        "rows": rows[:limit],
        "total_tickers": len(rows),
        "index": index_info,
        "as_of": max((r["last_date"] for r in rows), default=None),
    }


def list_tabs() -> list[dict]:
    return [{"id": k, "name": v["name"]} for k, v in TABS.items()]


# ------------------------------------------------------------------------ kalender

def calendar(symbol: str = "IHSG", year: int | None = None) -> dict:
    df = load_any(symbol)
    if df is None:
        return {}
    c = df["Close"]
    ret = c.pct_change().dropna() * 100
    change = c.diff().dropna()          # perubahan absolut: poin indeks / rupiah per saham
    years = sorted({d.year for d in ret.index})
    year = year or years[-1]
    sel = ret[ret.index.year == year]
    sel_chg = change[change.index.year == year]

    days = [{
        "date": d.strftime("%Y-%m-%d"),
        "return_pct": round(float(v), 2),
        "change": round(float(sel_chg.get(d, 0.0)), 2),
        "close": round(float(c.get(d, 0.0)), 2),
    } for d, v in sel.items()]

    monthly = []
    for m, g in sel.groupby(sel.index.month):
        growth = float(np.prod(1 + g.values / 100) - 1) * 100
        monthly.append({
            "month": int(m),
            "return_pct": round(growth, 2),
            "up_days": int((g > 0).sum()),
            "down_days": int((g < 0).sum()),
        })

    total = float(np.prod(1 + sel.values / 100) - 1) * 100
    best = sel.idxmax() if len(sel) else None
    worst = sel.idxmin() if len(sel) else None

    sym = symbol.upper()
    is_index = sym == "IHSG"
    name = ("Indeks Harga Saham Gabungan" if is_index
            else engine.ticker_names().get(sym, {}).get("name", ""))
    # "harga sekarang" selalu harga terakhir yang tersedia, bukan harga akhir tahun
    # yang sedang dilihat — supaya tetap jadi acuan saat menelusuri tahun lama
    last_close = float(c.iloc[-1])
    prev_close = float(c.iloc[-2]) if len(c) > 1 else last_close

    return {
        "symbol": sym,
        "name": name,
        "is_index": is_index,
        "price": round(last_close, 2),
        "price_change_pct": round((last_close / prev_close - 1) * 100, 2) if prev_close else None,
        "price_change": round(last_close - prev_close, 2),
        "price_date": df.index[-1].strftime("%Y-%m-%d"),
        "year": year,
        "years": years,
        "days": days,
        "monthly": monthly,
        "summary": {
            "total_return_pct": round(total, 2),
            "up_days": int((sel > 0).sum()),
            "down_days": int((sel < 0).sum()),
            "flat_days": int((sel == 0).sum()),
            "win_rate_pct": round(float((sel > 0).mean() * 100), 1) if len(sel) else None,
            "best_day": {"date": best.strftime("%Y-%m-%d"), "return_pct": round(float(sel.max()), 2)} if best is not None else None,
            "worst_day": {"date": worst.strftime("%Y-%m-%d"), "return_pct": round(float(sel.min()), 2)} if worst is not None else None,
        },
    }


# --------------------------------------------------------------- corporate action

def corporate_actions(ticker: str, refresh: bool = False) -> dict:
    t = engine.valid_ticker(ticker)
    path = ACTIONS_DIR / f"{t}.json"
    if path.exists() and not refresh:
        age_days = (time.time() - path.stat().st_mtime) / 86400
        if age_days < ACTIONS_TTL_DAYS:
            return json.loads(path.read_text(encoding="utf-8"))

    import yfinance as yf
    tk = yf.Ticker(f"{t}.JK")
    out = {"ticker": t, "dividends": [], "splits": []}
    try:
        for d, v in tk.dividends.items():
            out["dividends"].append({"date": d.strftime("%Y-%m-%d"), "amount": round(float(v), 2)})
        for d, v in tk.splits.items():
            out["splits"].append({"date": d.strftime("%Y-%m-%d"), "ratio": float(v)})
    except Exception as e:
        out["error"] = type(e).__name__

    df = engine.load_prices(t)
    if df is not None and out["dividends"]:
        price = float(df["Close"].iloc[-1])
        last12 = [d for d in out["dividends"]
                  if pd.Timestamp(d["date"]) >= df.index[-1] - pd.DateOffset(months=12)]
        total = sum(d["amount"] for d in last12)
        out["dividend_yield_pct"] = round(total / price * 100, 2) if price > 0 else None
        out["dividend_12m_total"] = round(total, 2)

    out["dividends"] = out["dividends"][-24:][::-1]
    out["splits"] = out["splits"][::-1]
    path.write_text(json.dumps(out), encoding="utf-8")
    return out
