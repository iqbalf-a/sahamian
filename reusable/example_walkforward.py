"""
Walk-forward BERGULIR — validasi anti-overfitting yang jauh lebih ketat daripada
satu split tunggal.

Riset ini sebelumnya cuma memakai satu pembagian (2022-23 latih / 2024-25 uji),
lalu satu periode terpisah (2018-2021). Walk-forward bergulir menguji berkali-kali:
    latih 24 bulan -> uji 12 bulan -> geser 12 bulan -> ulangi

Dua hal diukur:
A. Stabilitas konfigurasi TETAP (kandidat final) sepanjang waktu — apakah
   performanya konsisten atau bergantung periode tertentu.
B. Apakah TUNING menggeneralisasi: threshold ADX terbaik dipilih di data latih,
   lalu dipakai di data uji yang belum dilihat. Kalau tuning berguna, hasil uji
   dari threshold pilihan seharusnya mengalahkan threshold sembarang.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from qengine.engine import SymbolSpec, run_backtest
from qengine.strategy import StrategyParams, generate_signals

DATA = Path(__file__).parent / "data" / "EURUSDm_M15_tester.csv"
SPEC = SymbolSpec(tick_value=16691.2429)
DEPOSIT = 10_000_000.0

ADX_GRID = [20.0, 25.0, 30.0, 35.0, 40.0]
TRAIN_MONTHS = 24
TEST_MONTHS = 12


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M:%S")
    df = df.set_index("time").sort_index()
    return df[~df.index.duplicated(keep="last")]


def evaluate(df: pd.DataFrame, sig: pd.DataFrame, start, end) -> dict:
    """Backtest pada jendela [start, end) memakai sinyal yang sudah dihitung."""
    mask = (df.index >= start) & (df.index < end)
    if mask.sum() < 100:
        return {}
    # sertakan warm-up sebelum jendela agar indikator sudah matang,
    # tapi matikan sinyal di bagian warm-up
    pre = df.index[df.index < start][-400:]
    idx = df.index.isin(pre) | mask
    d = df[idx]
    s = sig[idx].copy()
    s.loc[s.index < start, ["long", "short"]] = False

    r = run_backtest(d, s, SPEC, DEPOSIT, 1.0)
    if r.total_trades == 0:
        return {"trades": 0, "wr": np.nan, "pf": np.nan, "net": 0.0}
    return {
        "trades": r.total_trades,
        "wr": r.win_rate,
        "pf": r.profit_factor,
        "net": r.net_profit,
    }


def main() -> None:
    df = load()
    df = df[(df.index >= "2017-06-01") & (df.index < "2026-01-01")]

    # precompute sinyal untuk tiap threshold ADX (mahal, jadi sekali saja)
    print("Menghitung sinyal untuk tiap threshold ADX...")
    sigs: dict[float, pd.DataFrame] = {}
    for adx in ADX_GRID:
        sigs[adx] = generate_signals(df, StrategyParams(adx_threshold=adx))
    print("selesai.\n")

    # --- bangun jendela bergulir ---
    windows = []
    cur = pd.Timestamp("2018-01-01")
    end_all = pd.Timestamp("2026-01-01")
    while True:
        tr_start = cur
        tr_end = tr_start + pd.DateOffset(months=TRAIN_MONTHS)
        te_end = tr_end + pd.DateOffset(months=TEST_MONTHS)
        if te_end > end_all:
            break
        windows.append((tr_start, tr_end, te_end))
        cur = cur + pd.DateOffset(months=TEST_MONTHS)

    # ================= A. konfigurasi TETAP =================
    print("=" * 92)
    print("A. Stabilitas konfigurasi TETAP (ADX>30) — performa per jendela uji 12 bulan")
    print("=" * 92)
    print(f"{'Jendela uji':<26} {'Trades':>7} {'WinRate':>9} {'PF':>7} {'Net (IDR)':>15}")
    print("-" * 92)

    fixed_rows = []
    for _, tr_end, te_end in windows:
        m = evaluate(df, sigs[30.0], tr_end, te_end)
        if not m:
            continue
        fixed_rows.append(m)
        pf = f"{m['pf']:.2f}" if np.isfinite(m["pf"]) else "inf"
        print(f"{str(tr_end.date()) + ' .. ' + str(te_end.date()):<26} "
              f"{m['trades']:>7} {m['wr']:>8.1f}% {pf:>7} {m['net']:>15,.0f}")

    if fixed_rows:
        tot_tr = sum(r["trades"] for r in fixed_rows)
        tot_net = sum(r["net"] for r in fixed_rows)
        prof = sum(1 for r in fixed_rows if r["net"] > 0)
        print("-" * 92)
        print(f"{'GABUNGAN':<26} {tot_tr:>7} {'':>9} {'':>7} {tot_net:>15,.0f}")
        print(f"  Jendela profitable: {prof}/{len(fixed_rows)}")

    # ================= B. walk-forward dengan tuning =================
    print()
    print("=" * 92)
    print("B. Walk-forward dengan tuning — threshold ADX dipilih di data LATIH, diuji di data UJI")
    print("=" * 92)
    print(f"{'Latih':<24} {'pilih':>6} | {'Uji':<24} {'Trades':>7} {'WinRate':>9} {'PF':>7}")
    print("-" * 92)

    wf_rows = []
    for tr_start, tr_end, te_end in windows:
        # pilih threshold dengan PF terbaik di data latih (minimal 10 trade)
        best_adx, best_pf = None, -np.inf
        for adx in ADX_GRID:
            m = evaluate(df, sigs[adx], tr_start, tr_end)
            if not m or m["trades"] < 10:
                continue
            pf = m["pf"] if np.isfinite(m["pf"]) else 99.0
            if pf > best_pf:
                best_pf, best_adx = pf, adx
        if best_adx is None:
            continue

        te = evaluate(df, sigs[best_adx], tr_end, te_end)
        if not te:
            continue
        wf_rows.append((best_adx, te))
        pf_s = f"{te['pf']:.2f}" if np.isfinite(te["pf"]) else "inf"
        print(f"{str(tr_start.date()) + '..' + str(tr_end.date()):<24} "
              f"{best_adx:>6.0f} | "
              f"{str(tr_end.date()) + '..' + str(te_end.date()):<24} "
              f"{te['trades']:>7} {te['wr']:>8.1f}% {pf_s:>7}")

    if wf_rows:
        tot_tr = sum(r["trades"] for _, r in wf_rows)
        tot_net = sum(r["net"] for _, r in wf_rows)
        prof = sum(1 for _, r in wf_rows if r["net"] > 0)
        chosen = [a for a, _ in wf_rows]
        print("-" * 92)
        print(f"  Total trade OOS   : {tot_tr}")
        print(f"  Net profit OOS    : {tot_net:,.0f} IDR")
        print(f"  Jendela profitable: {prof}/{len(wf_rows)}")
        print(f"  Threshold terpilih: {chosen}  (stabil = tuning konsisten)")

    # ================= C. pembanding: tiap threshold, seluruh OOS =================
    print()
    print("=" * 92)
    print("C. Pembanding — kalau threshold DIPATOK saja (tanpa tuning), di jendela uji yang sama")
    print("=" * 92)
    print(f"{'ADX':>5} {'Trades':>8} {'WinRate':>9} {'PF':>7} {'Net (IDR)':>15} {'Jendela profit':>16}")
    print("-" * 92)
    for adx in ADX_GRID:
        rows = [evaluate(df, sigs[adx], tr_end, te_end) for _, tr_end, te_end in windows]
        rows = [r for r in rows if r]
        if not rows:
            continue
        tot_tr = sum(r["trades"] for r in rows)
        tot_net = sum(r["net"] for r in rows)
        wins = sum(r["trades"] * r["wr"] / 100 for r in rows if r["trades"])
        wr = wins / tot_tr * 100 if tot_tr else np.nan
        gp = sum(max(r["net"], 0) for r in rows)
        prof = sum(1 for r in rows if r["net"] > 0)
        print(f"{adx:>5.0f} {tot_tr:>8} {wr:>8.1f}% {'':>7} {tot_net:>15,.0f} "
              f"{str(prof) + '/' + str(len(rows)):>16}")


if __name__ == "__main__":
    main()
