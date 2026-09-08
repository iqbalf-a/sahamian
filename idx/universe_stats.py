"""Statistik dasar universe (periode eksplorasi 2019-2023 saja, brankas 2024+ tidak disentuh)
dan tabel rasio biaya untuk beberapa kandidat target profit (aturan 1.3 / 4.2)."""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
EXPLORE_START, EXPLORE_END = "2019-01-01", "2023-12-31"

rows = []
for f in sorted(DATA_DIR.glob("*.csv")):
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    df = df.loc[EXPLORE_START:EXPLORE_END]
    if len(df) < 60:
        continue
    ret = df["Close"].pct_change().dropna()
    monthly = df["Close"].resample("ME").last().pct_change().dropna()
    avg_daily_value = (df["Close"] * df["Volume"]).mean()
    rows.append({
        "ticker": f.stem,
        "n_days": len(df),
        "daily_vol_%": ret.std() * 100,
        "avg_monthly_move_%": monthly.abs().mean() * 100,
        "avg_daily_value_IDR_bn": avg_daily_value / 1e9,
    })

stats = pd.DataFrame(rows).set_index("ticker").sort_values("avg_daily_value_IDR_bn", ascending=False)
pd.set_option("display.width", 120)
print("=== Statistik dasar universe LQ45, periode eksplorasi 2019-2023 ===\n")
print(stats.round(2))
print()
print("--- Agregat (median lintas ticker) ---")
print(stats.median(numeric_only=True).round(2))

print()
print("=== Rasio biaya vs target profit (aturan 1.3) ===")
print("Biaya bolak-balik diasumsikan 0,50% (beli 0,20% + jual 0,30%, per SETUP.md)\n")
roundtrip_cost = 0.50
print(f"{'Target profit':>15} | {'Rasio biaya':>12} | Verdict")
for target in [1, 2, 3, 5, 8, 10, 15, 20]:
    ratio = roundtrip_cost / target * 100
    verdict = "AMAN (<5%)" if ratio < 5 else ("BERAT (5-15%)" if ratio < 15 else "TIDAK LAYAK (>15%)")
    print(f"{target:>13}% | {ratio:>11.1f}% | {verdict}")
