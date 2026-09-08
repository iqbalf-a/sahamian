"""
Eksperimen 003 — Validasi template screener yang statusnya "belum diuji".

Tiap template diubah jadi strategi portofolio yang SEBANDING dengan eksperimen 001:
long-only, rebalance bulanan, top-9 skor tertinggi, equal weight, biaya 0,20%/0,30%.
Dengan begitu perbedaan hasil datang dari sinyalnya, bukan dari mekanika lain.

Template overnight/intraday TIDAK diikutkan: keduanya berpindah posisi harian dan sudah
terbukti kalah oleh biaya di screener (temuan 9 di INDEX.md) — memaksakannya ke kerangka
bulanan akan mengukur hal yang berbeda.

Periode utama: eksplorasi 2019-2023. Brankas dilaporkan terpisah dan ditandai INFORMATIF
(sudah terpakai 2026-09-07).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import engine  # noqa: E402
from stats import bootstrap_metrics, permute_drawdown_returns  # noqa: E402

TOP_N = 9
CAPITAL0 = 100_000_000.0
COST_BUY, COST_SELL = 0.0020, 0.0030


def load_frames() -> dict[str, pd.DataFrame]:
    out = {}
    for t in engine.universe_tickers():
        df = engine.load_prices(t)
        if df is None or len(df) < 300:
            continue
        c = df["Close"]
        df = df.assign(
            sma50=engine.sma(c, 50),
            sma200=engine.sma(c, 200),
            rsi=engine.rsi(c),
            obv=(np.sign(c.diff().fillna(0.0)) * df["Volume"]).cumsum(),
            vol20=df["Volume"].rolling(20).mean(),
            vol60=df["Volume"].rolling(60).mean(),
            vol5=df["Volume"].rolling(5).mean(),
            close_pos=((c - df["Low"]) / (df["High"] - df["Low"]).replace(0, np.nan)).rolling(5).mean(),
            high60=c.rolling(60).max().shift(1),
            low60=c.rolling(60).min().shift(1),
        )
        out[t] = df
    return out


def _asof(df: pd.DataFrame, dt: pd.Timestamp) -> pd.Series | None:
    sub = df.loc[:dt]
    return sub.iloc[-1] if len(sub) >= 220 else None


def score_momentum(df, dt, months=6):
    m = df["Close"].loc[:dt].resample("ME").last()
    if len(m) <= months or pd.isna(m.iloc[-1 - months]) or m.iloc[-1 - months] <= 0:
        return None
    v = float(m.iloc[-1] / m.iloc[-1 - months] - 1)
    return v if v > 0 else None


def score_trend(df, dt):
    r = _asof(df, dt)
    if r is None or pd.isna(r["sma50"]) or pd.isna(r["sma200"]):
        return None
    if not (r["Close"] > r["sma50"] and r["Close"] > r["sma200"]):
        return None
    s = df["sma50"].loc[:dt]
    if len(s) < 21 or pd.isna(s.iloc[-21]) or s.iloc[-21] <= 0:
        return None
    slope = float(s.iloc[-1] / s.iloc[-21] - 1)
    return slope if slope > 0 else None


def score_breakout(df, dt):
    r = _asof(df, dt)
    if r is None or pd.isna(r["high60"]) or r["high60"] <= 0:
        return None
    dist = float(r["Close"] / r["high60"] - 1)
    if dist < 0:
        return None
    vol_ok = (not pd.isna(r["vol20"])) and r["vol20"] > 0 and r["Volume"] / r["vol20"] >= 1.2
    return dist + (0.05 if vol_ok else 0.0)


def score_pullback(df, dt):
    r = _asof(df, dt)
    if r is None or pd.isna(r["sma200"]) or pd.isna(r["rsi"]):
        return None
    if r["Close"] <= r["sma200"] or r["rsi"] >= 45:
        return None
    return float(45 - r["rsi"])


def score_akumulasi(df, dt):
    r = _asof(df, dt)
    if r is None or pd.isna(r["vol60"]) or r["vol60"] <= 0 or pd.isna(r["close_pos"]):
        return None
    o = df["obv"].loc[:dt]
    if len(o) < 21 or pd.isna(r["vol20"]) or r["vol20"] <= 0:
        return None
    vol_ratio = float(r["vol5"] / r["vol60"])
    obv_slope = float((o.iloc[-1] - o.iloc[-21]) / (r["vol20"] * 20))
    return vol_ratio + float(r["close_pos"]) + obv_slope  # dinormalkan lewat peringkat di bawah


SCORERS = {
    "momentum": score_momentum,
    "trend": score_trend,
    "breakout": score_breakout,
    "pullback": score_pullback,
    "akumulasi": score_akumulasi,
}


def run_template(name: str, frames: dict, start: str, end: str) -> dict:
    scorer = SCORERS[name]
    panel = pd.DataFrame({t: df["Close"] for t, df in frames.items()})
    monthly = panel.resample("ME").last()
    dates = monthly.index
    window = dates[(dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))]

    capital = CAPITAL0
    prev_w: dict[str, float] = {}
    months = []

    for dt in window:
        loc = dates.get_loc(dt)
        if loc == 0:
            continue
        prev_dt = dates[loc - 1]

        pnl = 0.0
        for tkr, w in prev_w.items():
            p0, p1 = monthly.loc[prev_dt, tkr], monthly.loc[dt, tkr]
            if pd.isna(p0) or pd.isna(p1) or p0 <= 0:
                continue
            pnl += capital * w * (p1 / p0 - 1.0)
        before = capital + pnl

        scores = {}
        for t, df in frames.items():
            s = scorer(df, dt)
            if s is not None and np.isfinite(s):
                scores[t] = s
        picked = sorted(scores, key=lambda t: -scores[t])[:TOP_N]
        new_w = {t: 1.0 / len(picked) for t in picked} if picked else {}

        cost = 0.0
        for t in set(prev_w) | set(new_w):
            d = new_w.get(t, 0.0) - prev_w.get(t, 0.0)
            cost += before * abs(d) * (COST_BUY if d > 0 else COST_SELL)

        after = before - cost
        months.append({"date": dt.strftime("%Y-%m"), "return_pct": (after / capital - 1) * 100,
                       "n": len(picked)})
        capital, prev_w = after, new_w

    rets = np.array([m["return_pct"] / 100 for m in months])
    if len(rets) == 0:
        return {}
    metrics = engine.compute_metrics(rets, CAPITAL0)
    boot = {b.metric: b for b in bootstrap_metrics(rets * 100, n_iter=10_000)}
    dd = permute_drawdown_returns(rets, n_iter=5_000)
    pf = boot["Profit Factor"]
    return {
        "template": name,
        **metrics,
        "pf_ci_low": round(pf.ci_low, 2), "pf_ci_high": round(pf.ci_high, 2),
        "prob_pf_above1": round(pf.prob_above, 3),
        "dd_p95": round(dd["p95"], 1),
        "avg_holdings": round(float(np.mean([m["n"] for m in months])), 1),
        "months_invested": int(sum(1 for m in months if m["n"] > 0)),
    }


def benchmark(frames, start, end) -> dict:
    panel = pd.DataFrame({t: df["Close"] for t, df in frames.items()}).resample("ME").last()
    sub = panel.loc[start:end]
    valid = sub.iloc[0].dropna().index
    norm = sub[valid] / sub[valid].iloc[0]
    curve = norm.mean(axis=1)
    rets = curve.pct_change().dropna().values
    return {"template": "buy&hold equal-weight", **engine.compute_metrics(rets, CAPITAL0),
            "pf_ci_low": None, "pf_ci_high": None, "prob_pf_above1": None,
            "dd_p95": None, "avg_holdings": len(valid), "months_invested": len(rets)}


if __name__ == "__main__":
    frames = load_frames()
    print(f"{len(frames)} saham universe dimuat\n")

    out = {}
    for label, (s, e) in {
        "explore": ("2019-01-01", "2023-12-31"),
        "vault_informational": ("2024-01-01", "2026-12-31"),
    }.items():
        rows = [run_template(n, frames, s, e) for n in SCORERS]
        rows.append(benchmark(frames, s, e))
        out[label] = rows

        print(f"=== {label} ({s} s/d {e}) ===")
        hdr = f"{'template':<22} {'CAGR':>7} {'PF':>5} {'CI PF':>13} {'P(>1)':>6} {'WR':>6} {'DDp95':>6} {'pegang':>7}"
        print(hdr)
        for r in rows:
            ci = f"[{r['pf_ci_low']},{r['pf_ci_high']}]" if r["pf_ci_low"] is not None else "—"
            p = f"{r['prob_pf_above1']:.0%}" if r["prob_pf_above1"] is not None else "—"
            dd = f"{r['dd_p95']}%" if r["dd_p95"] is not None else "—"
            print(f"{r['template']:<22} {r['cagr_pct']:>6}% {r['pf']:>5} {ci:>13} {p:>6} "
                  f"{r['win_rate_pct']:>5}% {dd:>6} {r['avg_holdings']:>7}")
        print()

    Path(__file__).with_name("results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("hasil disimpan ke results.json")
