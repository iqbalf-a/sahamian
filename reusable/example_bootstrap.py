"""
Selang kepercayaan untuk metrik kandidat final, lewat bootstrap.

Menjawab pertanyaan yang menggantung sepanjang riset: PF 1.73 dari 97 trade itu
seberapa pasti? Kalau selang kepercayaannya melebar sampai di bawah 1.0, artinya
data yang ada belum cukup untuk menyimpulkan strateginya profitable.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from qengine.engine import SymbolSpec, run_backtest
from qengine.stats import bootstrap_metrics, permute_drawdown
from qengine.strategy import StrategyParams, generate_signals

DATA = Path(__file__).parent / "data" / "EURUSDm_M15_tester.csv"
SPEC = SymbolSpec(tick_value=16691.2429)
DEPOSIT = 10_000_000.0

PERIODS = {
    "2018-2025 (8 thn)": ("2018-01-01", "2026-01-01"),
    "2022-2025 (periode riset)": ("2022-01-01", "2026-01-01"),
    "2018-2021 (belum tersentuh)": ("2018-01-01", "2022-01-01"),
}


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M:%S")
    df = df.set_index("time").sort_index()
    return df[~df.index.duplicated(keep="last")]


def main() -> None:
    df_all = load()
    p = StrategyParams()

    for label, (start, end) in PERIODS.items():
        s_ts, e_ts = pd.Timestamp(start), pd.Timestamp(end)
        pre = df_all[df_all.index < s_ts].tail(400)
        df = pd.concat([pre, df_all[(df_all.index >= s_ts) & (df_all.index < e_ts)]])
        sig = generate_signals(df, p)
        sig.loc[sig.index < s_ts, ["long", "short"]] = False
        res = run_backtest(df, sig, SPEC, DEPOSIT, 1.0)

        profits = np.array([t.profit for t in res.trades])
        if len(profits) == 0:
            continue

        print("=" * 78)
        print(f"{label}   —   {len(profits)} trade")
        print("=" * 78)

        for r in bootstrap_metrics(profits, n_iter=20_000):
            print("  " + r.line())

        dd = permute_drawdown(profits, DEPOSIT, n_iter=5_000)
        print()
        print(f"  Max Drawdown — sebaran atas urutan trade acak:")
        print(f"    teramati di backtest : {dd['observed']:>6.2f}%")
        print(f"    median               : {dd['median']:>6.2f}%")
        print(f"    persentil 75 / 95    : {dd['p75']:>6.2f}% / {dd['p95']:>6.2f}%")
        print(f"    persentil 99 / maks  : {dd['p99']:>6.2f}% / {dd['max']:>6.2f}%")
        print(f"    urutan yang lebih buruk dari yang teramati: "
              f"{dd['pct_worse_than_observed']:.1f}%")
        print()


if __name__ == "__main__":
    main()
