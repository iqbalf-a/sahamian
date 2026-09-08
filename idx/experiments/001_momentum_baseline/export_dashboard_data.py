"""Ekspor angka eksperimen 001 + statistik universe ke JSON untuk tab Riset di aplikasi.

Memakai `engine.py` (versi berparameter) dengan parameter default yang sudah diverifikasi
menghasilkan angka identik dengan snapshot `strategy.py`. Seluruh statistik dihitung di
ruang RETURN — lihat catatan di `stats.permute_drawdown_returns`.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import engine  # noqa: E402
from stats import bootstrap_metrics, permute_drawdown_returns  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OUT = Path(__file__).parent / "dashboard_data.json"

CAPITAL0 = 100_000_000.0
PERIODS = {
    "explore": ("2019-01-01", "2023-12-31"),
    "vault": ("2024-01-01", "2026-12-31"),
    "combined": ("2019-01-01", "2026-12-31"),
}


def summarize(start: str, end: str) -> dict:
    res = engine.momentum_backtest(engine.BacktestParams(start=start, end=end, capital0=CAPITAL0))
    rets = np.array(res.returns)
    boot = {
        b.metric: {
            "observed": round(b.observed, 3), "ci_low": round(b.ci_low, 3),
            "ci_high": round(b.ci_high, 3),
            "prob_above": round(b.prob_above, 4) if b.prob_above is not None else None,
        }
        for b in bootstrap_metrics(rets * 100, n_iter=20_000)
    }
    dd = permute_drawdown_returns(rets, n_iter=20_000)
    return {
        "metrics": res.metrics,
        "yearly": res.yearly,
        "bootstrap": boot,
        "drawdown_permutation": {k: round(v, 2) for k, v in dd.items()},
        "equity": {
            "dates": [m["date"] for m in res.months],
            "strategy": [m["capital"] for m in res.months],
            "benchmark": res.benchmark,
        },
        "total_cost": sum(m["cost"] for m in res.months),
    }


periods = {name: summarize(*rng) for name, rng in PERIODS.items()}

# benchmark buy&hold untuk periode eksplorasi (pembanding headline)
monthly = engine.close_panel().resample("ME").last()
explore = monthly.loc["2019-01-01":"2023-12-31"]
valid = explore.iloc[0].dropna().index
bh_ret = float((explore[valid].iloc[-1] / explore[valid].iloc[0] - 1).mean())
bh_cagr = (1 + bh_ret) ** (1 / ((explore.index[-1] - explore.index[0]).days / 365.25)) - 1

uni_rows = []
for f in sorted(DATA_DIR.glob("*.csv")):
    d = pd.read_csv(f, index_col=0, parse_dates=True).loc["2019-01-01":"2023-12-31"]
    if len(d) < 60:
        continue
    ret = d["Close"].pct_change().dropna()
    monthly_m = d["Close"].resample("ME").last().pct_change().dropna()
    uni_rows.append({
        "ticker": f.stem,
        "n_days": int(len(d)),
        "daily_vol_pct": round(float(ret.std() * 100), 2),
        "avg_monthly_move_pct": round(float(monthly_m.abs().mean() * 100), 2),
        "avg_daily_value_bn": round(float((d["Close"] * d["Volume"]).mean() / 1e9), 2),
    })
uni_rows.sort(key=lambda r: -r["avg_daily_value_bn"])

cost_table = []
for target in [1, 2, 3, 5, 8, 10, 15, 20]:
    ratio = 0.50 / target * 100
    cost_table.append({
        "target_pct": target, "ratio_pct": round(ratio, 1),
        "verdict": "aman" if ratio < 5 else ("berat" if ratio < 15 else "tidak_layak"),
    })

ex = periods["explore"]
out = {
    "meta": {
        "universe": "LQ45 (44 ticker, komposisi Agu-Okt 2026)",
        "period": "2019-01 s/d 2023-12",
        "vault_period": "2024-01 s/d 2026-09",
        "vault_opened": True,
        "capital0": CAPITAL0,
    },
    "kpi": {
        **ex["metrics"],
        "bh_total_return_pct": round(bh_ret * 100, 1),
        "bh_cagr_pct": round(bh_cagr * 100, 1),
        "max_dd_p95_pct": ex["drawdown_permutation"]["p95"],
        "total_cost": ex["total_cost"],
        "total_cost_pct": round(ex["total_cost"] / CAPITAL0 * 100, 1),
    },
    "equity": ex["equity"],
    "yearly": ex["yearly"],
    "bootstrap": ex["bootstrap"],
    "drawdown_permutation": ex["drawdown_permutation"],
    "periods": {
        name: {"metrics": p["metrics"], "yearly": p["yearly"],
               "bootstrap": p["bootstrap"], "drawdown_permutation": p["drawdown_permutation"]}
        for name, p in periods.items()
    },
    "universe_stats": uni_rows,
    "cost_table": cost_table,
}

OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
for name, p in periods.items():
    m = p["metrics"]
    print(f"  {name:9s} n={m['n_months']:3d} CAGR {m['cagr_pct']:>6}% PF {m['pf']} "
          f"DDp95 {p['drawdown_permutation']['p95']}%")
