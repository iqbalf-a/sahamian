"""
Eksperimen 001 — Momentum / relative strength lintas saham (prioritas #1 di METHODOLOGY 4.7).

Logika:
  - Tiap akhir bulan, hitung return trailing 6 bulan tiap saham di universe LQ45.
  - Pilih top 20% (min 3 saham) DENGAN momentum positif -> equal weight.
  - Rebalance bulanan, long-only, biaya beli 0,20% + jual 0,30% dikenakan ke turnover.
  - Kalau tidak ada saham dengan momentum positif, portofolio 100% cash bulan itu.

HANYA periode eksplorasi (2019-01 s/d 2023-12) yang dipakai di sini. Brankas 2024+ TIDAK
disentuh -- lihat SETUP.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LOOKBACK_MONTHS = 6
TOP_FRACTION = 0.20
MIN_HOLDINGS = 3
COST_BUY = 0.0020
COST_SELL = 0.0030
CAPITAL0 = 100_000_000.0


def load_monthly_closes() -> pd.DataFrame:
    closes = {}
    for f in sorted(DATA_DIR.glob("*.csv")):
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        closes[f.stem] = df["Close"]
    panel = pd.DataFrame(closes)
    monthly = panel.resample("ME").last()
    return monthly


@dataclass
class MonthResult:
    date: pd.Timestamp
    capital_start: float
    capital_end: float
    pnl: float
    n_holdings: int
    holdings: list[str]
    turnover_cost: float


def run(explore_start="2019-01-01", explore_end="2023-12-31") -> list[MonthResult]:
    monthly = load_monthly_closes()
    mom = monthly.pct_change(LOOKBACK_MONTHS)

    dates = monthly.index
    explore_dates = dates[(dates >= pd.Timestamp(explore_start)) & (dates <= pd.Timestamp(explore_end))]

    capital = CAPITAL0
    prev_weights: dict[str, float] = {}
    results: list[MonthResult] = []

    for i, dt in enumerate(explore_dates):
        loc = dates.get_loc(dt)
        if loc == 0:
            continue
        prev_dt = dates[loc - 1]

        # --- return realized this month from PREVIOUS month-end holdings ---
        month_pnl = 0.0
        if prev_weights:
            for tkr, w in prev_weights.items():
                p0 = monthly.loc[prev_dt, tkr]
                p1 = monthly.loc[dt, tkr]
                if pd.isna(p0) or pd.isna(p1) or p0 <= 0:
                    continue
                month_pnl += capital * w * (p1 / p0 - 1.0)

        capital_before_rebalance = capital + month_pnl

        # --- pick new holdings based on momentum known AT this month-end ---
        row = mom.loc[dt].dropna()
        row = row[row > 0]
        row = row.sort_values(ascending=False)
        n_select = max(MIN_HOLDINGS, int(np.ceil(len(monthly.columns) * TOP_FRACTION)))
        selected = row.head(n_select).index.tolist()

        new_weights = {t: 1.0 / len(selected) for t in selected} if selected else {}

        # --- turnover cost: compare new vs old weights ---
        all_tkrs = set(prev_weights) | set(new_weights)
        turnover_cost = 0.0
        for t in all_tkrs:
            w_old = prev_weights.get(t, 0.0)
            w_new = new_weights.get(t, 0.0)
            delta = w_new - w_old
            if delta > 0:
                turnover_cost += capital_before_rebalance * delta * COST_BUY
            elif delta < 0:
                turnover_cost += capital_before_rebalance * (-delta) * COST_SELL

        capital_after = capital_before_rebalance - turnover_cost

        results.append(MonthResult(
            date=dt,
            capital_start=capital,
            capital_end=capital_after,
            pnl=capital_after - capital,
            n_holdings=len(selected),
            holdings=selected,
            turnover_cost=turnover_cost,
        ))

        capital = capital_after
        prev_weights = new_weights

    return results


if __name__ == "__main__":
    res = run()
    for r in res:
        print(f"{r.date.date()}  cap={r.capital_end:>15,.0f}  pnl={r.pnl:>+13,.0f}  "
              f"n={r.n_holdings:2d}  cost={r.turnover_cost:>9,.0f}  {r.holdings}")
