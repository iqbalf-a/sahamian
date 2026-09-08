"""Analisis eksperimen 001: statistik wajib (Bagian 2.3), tangga validasi tahap 1-2,
dan pembanding equal-weight buy&hold universe. HANYA periode eksplorasi (2019-2023)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # untuk stats.py
from stats import bootstrap_metrics, permute_drawdown  # noqa: E402
from strategy import run, load_monthly_closes, CAPITAL0  # noqa: E402

results = run()
pnl = np.array([r.pnl for r in results])
dates = [r.date for r in results]
n_months = len(results)

print("=" * 78)
print(f"EKSPERIMEN 001 — Momentum lintas saham, periode eksplorasi 2019-2023 ({n_months} bulan)")
print("=" * 78)

final_capital = results[-1].capital_end
total_return = final_capital / CAPITAL0 - 1
years = n_months / 12
cagr = (final_capital / CAPITAL0) ** (1 / years) - 1

print(f"\nModal awal      : Rp{CAPITAL0:>15,.0f}")
print(f"Modal akhir      : Rp{final_capital:>15,.0f}")
print(f"Return total     : {total_return:>+14.1%}   ({years:.1f} tahun)")
print(f"CAGR             : {cagr:>+14.1%}")

# --- tangga validasi tahap 1: screening cepat ---
gp = pnl[pnl > 0].sum()
gl = -pnl[pnl < 0].sum()
pf = gp / gl if gl > 0 else float("inf")
wr = (pnl > 0).mean() * 100
print(f"\n[Tahap 1 - screening] PF bulanan={pf:.2f}  win rate bulan={wr:.1f}%  "
      f"n bulan={n_months}  {'LOLOS (PF>1, n>=30)' if pf > 1 and n_months >= 30 else 'TIDAK LOLOS'}")

# --- max drawdown dari equity curve harian ---
equity = CAPITAL0 + np.cumsum(pnl)
peak = np.maximum.accumulate(equity)
dd_series = (peak - equity) / peak
max_dd = dd_series.max() * 100
print(f"Max Drawdown (backtest, bulanan) : {max_dd:.2f}%")

# --- tahap 2: breakdown tahunan ---
df = pd.DataFrame({"date": dates, "pnl": pnl})
df["year"] = df["date"].dt.year
print("\n[Tahap 2 - multi-periode] per tahun:")
print(f"{'Tahun':>6} | {'n bln':>5} | {'PF':>6} | {'WinRate':>7} | {'Net (IDR)':>16}")
n_profitable_years = 0
for y, g in df.groupby("year"):
    p = g["pnl"].values
    gpv, glv = p[p > 0].sum(), -p[p < 0].sum()
    pfv = gpv / glv if glv > 0 else float("inf")
    wrv = (p > 0).mean() * 100
    if p.sum() > 0:
        n_profitable_years += 1
    print(f"{y:>6} | {len(p):>5} | {pfv:>6.2f} | {wrv:>6.1f}% | {p.sum():>16,.0f}")
print(f"-> {n_profitable_years}/{df['year'].nunique()} tahun profitable")

# --- tahap 5: bootstrap + permutasi DD (Bagian 2.3) ---
print("\n[Tahap 5 - bootstrap] (unit = PnL portofolio per bulan, 20.000 iterasi)")
for r in bootstrap_metrics(pnl, n_iter=20_000):
    print("  " + r.line())

dd = permute_drawdown(pnl, CAPITAL0, n_iter=20_000)
print(f"\n  Max Drawdown -- sebaran atas urutan bulan acak:")
print(f"    teramati di backtest : {dd['observed']:.2f}%")
print(f"    median               : {dd['median']:.2f}%")
print(f"    persentil 75 / 95    : {dd['p75']:.2f}% / {dd['p95']:.2f}%")
print(f"    persentil 99 / maks  : {dd['p99']:.2f}% / {dd['max']:.2f}%")

# --- pembanding: equal-weight buy & hold seluruh universe (tanpa rebalance, tanpa filter momentum) ---
monthly = load_monthly_closes()
explore = monthly.loc["2019-01-01":"2023-12-31"]
# saham yang punya harga di awal & akhir periode eksplorasi
start_row = explore.iloc[0]
valid = start_row.dropna().index
bh_ret = (explore[valid].iloc[-1] / explore[valid].iloc[0] - 1).mean()
bh_years = (explore.index[-1] - explore.index[0]).days / 365.25
bh_cagr = (1 + bh_ret) ** (1 / bh_years) - 1
print(f"\n[Pembanding] Equal-weight buy&hold {len(valid)} saham LQ45 (tanpa rebalance, tanpa biaya):")
print(f"  Return total : {bh_ret:>+.1%}   CAGR: {bh_cagr:>+.1%}")

print(f"\n[Strategi momentum] Return total : {total_return:>+.1%}   CAGR: {cagr:>+.1%}")

# --- biaya kumulatif sbg % turnover, utk cek konsistensi dgn asumsi rasio biaya ---
total_cost = sum(r.turnover_cost for r in results)
print(f"\nTotal biaya transaksi 5 tahun: Rp{total_cost:,.0f} "
      f"({total_cost / CAPITAL0:.1%} dari modal awal, {total_cost / n_months:,.0f}/bulan rata-rata)")
