"""
Audit statistik atas klaim-klaim kunci di experiments/INDEX.md.

Latar: bootstrap menunjukkan Win Rate 58.4% punya 95% CI [48.3%, 68.5%]. Banyak
kesimpulan riset dibangun di atas selisih 2-3 poin win rate atau 0.1-0.2 profit
factor — berada dalam rentang noise. Skrip ini menguji mana yang bertahan.

Dua jenis uji dipakai:

1. FILTER BERTINGKAT (B adalah himpunan bagian dari A, karena filter membuang
   trade). Uji yang tepat: periksa langsung trade yang DIBUANG. Kalau trade yang
   dibuang punya ekspektasi jauh lebih buruk dari yang dipertahankan, filternya
   memang bekerja. Ini lebih kuat daripada membandingkan dua PF, karena
   memanfaatkan struktur nested-nya.

2. KONFIGURASI TERPISAH (tidak bertingkat, mis. ADX>30 vs ADX>35). Bootstrap dua
   sampel independen atas selisih metrik.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from qengine.engine import SymbolSpec, run_backtest
from qengine.strategy import StrategyParams, generate_signals

DATA = Path(__file__).parent / "data" / "EURUSDm_M15_tester.csv"
SPEC = SymbolSpec(tick_value=16691.2429)
DEPOSIT = 10_000_000.0
START, END = pd.Timestamp("2018-01-01"), pd.Timestamp("2026-01-01")
N_BOOT = 20_000
RNG = np.random.default_rng(7)

OFF = dict(atr_ratio_min=0.0, atr_ratio_max=99.0, slope_min_atr=-99.0, swing_min_room_atr=0.0)


@dataclass
class Run:
    label: str
    profits: np.ndarray
    entries: np.ndarray   # waktu entry, untuk mencocokkan trade antar konfigurasi

    @property
    def n(self) -> int:
        return len(self.profits)

    @property
    def pf(self) -> float:
        gp = self.profits[self.profits > 0].sum()
        gl = -self.profits[self.profits < 0].sum()
        return gp / gl if gl > 0 else float("inf")

    @property
    def wr(self) -> float:
        return (self.profits > 0).mean() * 100 if self.n else float("nan")


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df["time"] = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M:%S")
    df = df.set_index("time").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    pre = df[df.index < START].tail(400)
    return pd.concat([pre, df[(df.index >= START) & (df.index < END)]])


def do_run(df: pd.DataFrame, label: str, **overrides) -> Run:
    p = StrategyParams(**overrides)
    sig = generate_signals(df, p)
    sig.loc[sig.index < START, ["long", "short"]] = False
    r = run_backtest(df, sig, SPEC, DEPOSIT, 1.0)
    return Run(label,
               np.array([t.profit for t in r.trades]),
               np.array([t.entry_time for t in r.trades]))


def boot_mean_diff(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """Bootstrap selisih rata-rata (b - a). Kembalikan (obs, ci_low, ci_high)."""
    obs = b.mean() - a.mean()
    if len(a) == 0 or len(b) == 0:
        return obs, float("nan"), float("nan")
    ia = RNG.integers(0, len(a), size=(N_BOOT, len(a)))
    ib = RNG.integers(0, len(b), size=(N_BOOT, len(b)))
    d = b[ib].mean(axis=1) - a[ia].mean(axis=1)
    return obs, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def audit_nested(base: Run, filtered: Run, claim: str) -> None:
    """Filter membuang trade: periksa langsung trade yang dibuang."""
    kept_times = set(filtered.entries.tolist())
    mask_removed = np.array([t not in kept_times for t in base.entries])
    removed = base.profits[mask_removed]
    kept = filtered.profits

    print(f"\n  {claim}")
    print(f"    {base.label:<28} n={base.n:>3}  PF={base.pf:>5.2f}  WR={base.wr:>5.1f}%")
    print(f"    {filtered.label:<28} n={filtered.n:>3}  PF={filtered.pf:>5.2f}  WR={filtered.wr:>5.1f}%")

    if len(removed) == 0:
        print("    -> filter tidak membuang trade apapun (tidak berefek)")
        return

    rem_wr = (removed > 0).mean() * 100
    print(f"    trade yang DIBUANG           n={len(removed):>3}  "
          f"rata2={removed.mean():>12,.0f}  WR={rem_wr:>5.1f}%")
    print(f"    trade yang DIPERTAHANKAN     n={len(kept):>3}  "
          f"rata2={kept.mean():>12,.0f}  WR={filtered.wr:>5.1f}%")

    obs, lo, hi = boot_mean_diff(removed, kept)
    verdict = "BERMAKNA" if lo > 0 else ("tidak terbedakan" if hi > 0 else "MERUGIKAN")
    print(f"    selisih rata2 (kept - dibuang) = {obs:>12,.0f}   "
          f"95% CI [{lo:>11,.0f}, {hi:>11,.0f}]")
    print(f"    -> {verdict}")


def audit_independent(a: Run, b: Run, claim: str) -> None:
    print(f"\n  {claim}")
    print(f"    {a.label:<28} n={a.n:>3}  PF={a.pf:>5.2f}  WR={a.wr:>5.1f}%  "
          f"rata2={a.profits.mean():>12,.0f}")
    print(f"    {b.label:<28} n={b.n:>3}  PF={b.pf:>5.2f}  WR={b.wr:>5.1f}%  "
          f"rata2={b.profits.mean():>12,.0f}")
    obs, lo, hi = boot_mean_diff(a.profits, b.profits)
    verdict = "BERMAKNA" if lo > 0 else ("tidak terbedakan" if hi > 0 else "arah sebaliknya")
    print(f"    selisih rata2 (B - A) = {obs:>12,.0f}   95% CI [{lo:>11,.0f}, {hi:>11,.0f}]")
    print(f"    -> {verdict}")


def main() -> None:
    df = load()
    print("Audit klaim riset — EURUSDm M15, 2018-2025, bootstrap 20.000 resample")
    print("=" * 96)

    base_noadx = do_run(df, "tanpa ADX (ADX>0)", **{**OFF, "adx_threshold": 0.0})
    adx30 = do_run(df, "ADX>30", **OFF)
    vol = do_run(df, "+ filter volatilitas",
                 **{**OFF, "atr_ratio_min": 0.7, "atr_ratio_max": 1.8})
    slope = do_run(df, "+ filter kemiringan",
                   **{**OFF, "atr_ratio_min": 0.7, "atr_ratio_max": 1.8, "slope_min_atr": 0.0})
    swing = do_run(df, "+ filter ruang swing",
                   atr_ratio_min=0.7, atr_ratio_max=1.8, slope_min_atr=0.0,
                   swing_min_room_atr=2.0)

    print("\n" + "-" * 96)
    print("BAGIAN 1 — tumpukan filter (uji: apakah trade yang dibuang memang lebih buruk?)")
    print("-" * 96)
    audit_nested(base_noadx, adx30,
                 "KLAIM #9: 'ADX adalah filter paling berdampak, memperbaiki SEMUA metrik'")
    audit_nested(adx30, vol,
                 "KLAIM #18: 'filter volatilitas menang di semua metrik sekaligus'")
    audit_nested(vol, slope,
                 "KLAIM #20: 'filter kemiringan MA menang di semua metrik'")
    audit_nested(slope, swing,
                 "KLAIM #24: 'filter ruang swing menaikkan WR 65.57%->67.24%, PF 2.28->2.37'")

    print("\n" + "-" * 96)
    print("BAGIAN 2 — konfigurasi terpisah (bootstrap dua sampel)")
    print("-" * 96)
    adx35 = do_run(df, "ADX>35", **{**OFF, "atr_ratio_min": 0.7, "atr_ratio_max": 1.8,
                                    "slope_min_atr": 0.0, "swing_min_room_atr": 2.0,
                                    "adx_threshold": 35.0})
    audit_independent(swing, adx35,
                      "KLAIM (walk-forward): 'ADX>35 lebih konsisten daripada ADX>30'")

    # rezim: 2018-2021 vs 2022-2025 memakai konfigurasi final
    p_final = StrategyParams()
    sig = generate_signals(df, p_final)
    early_mask = (swing.entries >= pd.Timestamp("2018-01-01")) & (swing.entries < pd.Timestamp("2022-01-01"))
    early = Run("2018-2021", swing.profits[early_mask], swing.entries[early_mask])
    late = Run("2022-2025", swing.profits[~early_mask], swing.entries[~early_mask])
    audit_independent(early, late,
                      "KLAIM #27: 'edge regime-dependent — 2022-2025 jauh lebih baik'")

    audit_independent(base_noadx, swing,
                      "KLAIM KUMULATIF: 'seluruh tumpukan filter mengubah strategi "
                      "dari breakeven jadi profitable'")

    # Berapa banyak data yang dibutuhkan agar efek sebesar ini bisa terbukti?
    print("\n" + "-" * 96)
    print("BAGIAN 3 — berapa banyak trade yang DIBUTUHKAN agar efek ini terbukti?")
    print("-" * 96)
    for name, r in [("kandidat final", swing)]:
        m, s = r.profits.mean(), r.profits.std(ddof=1)
        if m > 0:
            # n agar 95% CI rata-rata tidak menyentuh 0: n > (1.96*s/m)^2
            need = (1.96 * s / m) ** 2
            print(f"  {name}: rata2={m:,.0f}  simpangan baku={s:,.0f}")
            print(f"    -> butuh ~{need:.0f} trade agar profitabilitasnya sendiri "
                  f"signifikan (punya {r.n})")
            print(f"    -> pada ~{r.n/8:.0f} trade/tahun, itu setara ~{need/(r.n/8):.0f} tahun data")

    print("\n" + "=" * 96)
    print("Catatan: 'tidak terbedakan' BUKAN berarti filternya tidak berguna — hanya berarti")
    print("data yang ada belum cukup untuk membuktikannya. Untuk strategi ~12 trade/tahun,")
    print("membuktikan efek kecil butuh data jauh lebih panjang dari 8 tahun.")


if __name__ == "__main__":
    main()
