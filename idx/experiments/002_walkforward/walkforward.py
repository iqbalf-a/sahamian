"""
Eksperimen 002 — Tahap 3 tangga validasi: walk-forward bergulir + sensitivitas parameter.

Dua pertanyaan:
  A. Apakah hasilnya stabil lintas waktu kalau parameter dipatok? (walk-forward)
  B. Apakah memilih parameter dari data latih tiap jendela MENGALAHKAN patokan tetap?
     (METHODOLOGY 3.3 menemukan di forex: TIDAK — patokan tetap menang)
  C. Apakah lookback=6 / top=9 duduk di dataran datar atau di puncak sempit? (sensitivitas)

Utama dijalankan di EKSPLORASI 2019-2023 saja. Rentang penuh 2019-2026 ikut dilaporkan tapi
ditandai INFORMATIF — brankas sudah dibuka 2026-09-07, jadi itu bukan uji independen lagi.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import engine  # noqa: E402

LOOKBACKS = [1, 2, 3, 6, 9, 12]
TOP_NS = [3, 5, 9, 12, 15, 20]
FIXED_LOOKBACK = 6
FIXED_TOP_N = 9
CAPITAL0 = 100_000_000.0


def segment(start: pd.Timestamp, end: pd.Timestamp, lookback: int, top_n: int) -> dict:
    """Backtest satu segmen. Bulan pertama dibuang karena selalu ramp-up (portofolio
    masih kosong, P&L pasti nol) -- kalau tidak, jendela pendek terlihat lebih buruk."""
    warm = (start - pd.DateOffset(months=1)).strftime("%Y-%m-%d")
    res = engine.momentum_backtest(engine.BacktestParams(
        lookback_months=lookback, top_n=top_n,
        start=warm, end=end.strftime("%Y-%m-%d"), capital0=CAPITAL0,
    ))
    rets = np.array(res.returns[1:])
    if len(rets) == 0:
        return {"n": 0}
    m = engine.compute_metrics(rets, CAPITAL0)
    return {"n": len(rets), "total_return_pct": m["total_return_pct"], "cagr_pct": m["cagr_pct"],
            "pf": m["pf"], "win_rate_pct": m["win_rate_pct"], "max_dd_pct": m["max_dd_pct"]}


def walk_forward(range_start: str, range_end: str, train_months=24, test_months=12) -> list[dict]:
    windows = []
    t0 = pd.Timestamp(range_start)
    end = pd.Timestamp(range_end)
    while True:
        train_start = t0
        train_end = train_start + pd.DateOffset(months=train_months) - pd.DateOffset(days=1)
        test_start = train_end + pd.DateOffset(days=1)
        test_end = test_start + pd.DateOffset(months=test_months) - pd.DateOffset(days=1)
        if test_end > end:
            break

        # (B) pilih lookback terbaik dari data LATIH saja
        train_scores = {lb: segment(train_start, train_end, lb, FIXED_TOP_N) for lb in LOOKBACKS}
        best_lb = max(LOOKBACKS, key=lambda lb: train_scores[lb].get("total_return_pct", -1e9))

        tuned = segment(test_start, test_end, best_lb, FIXED_TOP_N)
        fixed = segment(test_start, test_end, FIXED_LOOKBACK, FIXED_TOP_N)

        windows.append({
            "train": f"{train_start:%Y-%m}..{train_end:%Y-%m}",
            "test": f"{test_start:%Y-%m}..{test_end:%Y-%m}",
            "picked_lookback": best_lb,
            "tuned": tuned,
            "fixed": fixed,
        })
        t0 = t0 + pd.DateOffset(months=test_months)
    return windows


def compound(windows: list[dict], key: str) -> float:
    growth = 1.0
    for w in windows:
        growth *= 1 + w[key]["total_return_pct"] / 100
    return (growth - 1) * 100


def sensitivity(start: str, end: str) -> list[dict]:
    rows = []
    for lb in LOOKBACKS:
        for tn in TOP_NS:
            res = engine.momentum_backtest(engine.BacktestParams(
                lookback_months=lb, top_n=tn, start=start, end=end, capital0=CAPITAL0))
            m = res.metrics
            rows.append({"lookback": lb, "top_n": tn, "cagr_pct": m["cagr_pct"],
                         "pf": m["pf"], "max_dd_pct": m["max_dd_pct"],
                         "win_rate_pct": m["win_rate_pct"]})
    return rows


if __name__ == "__main__":
    out = {}

    for label, (s, e) in {
        "explore": ("2019-01-01", "2023-12-31"),
        "full_informational": ("2019-01-01", "2026-08-31"),
    }.items():
        wins = walk_forward(s, e)
        out[f"walkforward_{label}"] = {
            "windows": wins,
            "tuned_total_pct": round(compound(wins, "tuned"), 1),
            "fixed_total_pct": round(compound(wins, "fixed"), 1),
        }
        print(f"\n=== Walk-forward {label} ({len(wins)} jendela uji) ===")
        print(f"{'Jendela uji':<18} {'pilih':>6} {'tuned':>9} {'patok-6':>9}")
        for w in wins:
            print(f"{w['test']:<18} {w['picked_lookback']:>5}b "
                  f"{w['tuned']['total_return_pct']:>8.1f}% {w['fixed']['total_return_pct']:>8.1f}%")
        print(f"{'TOTAL majemuk':<18} {'':>6} "
              f"{out[f'walkforward_{label}']['tuned_total_pct']:>8.1f}% "
              f"{out[f'walkforward_{label}']['fixed_total_pct']:>8.1f}%")

    print("\n=== Sensitivitas parameter (eksplorasi 2019-2023, CAGR %) ===")
    grid = sensitivity("2019-01-01", "2023-12-31")
    out["sensitivity_explore"] = grid
    df = pd.DataFrame(grid).pivot(index="lookback", columns="top_n", values="cagr_pct")
    print(df.to_string())

    Path(__file__).with_name("results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {Path(__file__).with_name('results.json')}")
