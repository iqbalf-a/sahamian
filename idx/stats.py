"""
Analisis statistik atas hasil backtest.

Sepanjang riset ini pertanyaan "hasilnya nyata atau kebetulan?" dijawab dengan
intuisi ukuran sample. Modul ini menjawabnya secara kuantitatif.

Dua metode:
1. Bootstrap (resample trade dengan pengembalian) -> selang kepercayaan untuk
   Profit Factor, Win Rate, expectancy. Menjawab: "kalau periode yang sama
   dijalani ulang, seberapa jauh hasilnya bisa berbeda?"
2. Permutasi urutan trade -> distribusi Max Drawdown. DD sangat bergantung pada
   URUTAN menang/kalah, bukan cuma komposisinya; DD yang terlihat di satu backtest
   adalah satu penarikan dari distribusi yang lebar.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BootstrapResult:
    metric: str
    observed: float
    mean: float
    ci_low: float
    ci_high: float
    prob_above: float | None = None      # P(metrik > ambang), mis. PF > 1
    threshold: float | None = None

    def line(self) -> str:
        s = (f"{self.metric:<16} obs={self.observed:>8.3f}   "
             f"95% CI [{self.ci_low:>7.3f}, {self.ci_high:>7.3f}]")
        if self.prob_above is not None:
            s += f"   P(>{self.threshold:g}) = {self.prob_above:>6.1%}"
        return s


def _pf(profits: np.ndarray) -> float:
    gp = profits[profits > 0].sum()
    gl = -profits[profits < 0].sum()
    return gp / gl if gl > 0 else np.inf


def _max_dd_pct(profits: np.ndarray, deposit: float) -> float:
    """Max drawdown relatif dari kurva equity berbasis urutan trade."""
    equity = deposit + np.cumsum(profits)
    peak = np.maximum.accumulate(np.concatenate([[deposit], equity]))[1:]
    return float(((peak - equity) / peak).max() * 100.0)


def bootstrap_metrics(
    profits: np.ndarray,
    n_iter: int = 20_000,
    seed: int = 42,
    ci: float = 95.0,
) -> list[BootstrapResult]:
    """Resample trade dengan pengembalian; hitung sebaran metrik."""
    rng = np.random.default_rng(seed)
    n = len(profits)
    lo_q, hi_q = (100 - ci) / 2, 100 - (100 - ci) / 2

    idx = rng.integers(0, n, size=(n_iter, n))
    samples = profits[idx]

    pos = np.where(samples > 0, samples, 0.0).sum(axis=1)
    neg = -np.where(samples < 0, samples, 0.0).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        pf = np.where(neg > 0, pos / neg, np.inf)
    pf_finite = pf[np.isfinite(pf)]

    wr = (samples > 0).mean(axis=1) * 100.0
    exp_payoff = samples.mean(axis=1)

    out = [
        BootstrapResult("Profit Factor", _pf(profits), float(pf_finite.mean()),
                        float(np.percentile(pf_finite, lo_q)),
                        float(np.percentile(pf_finite, hi_q)),
                        float((pf > 1.0).mean()), 1.0),
        BootstrapResult("Win Rate (%)", float((profits > 0).mean() * 100), float(wr.mean()),
                        float(np.percentile(wr, lo_q)), float(np.percentile(wr, hi_q))),
        BootstrapResult("Expectancy", float(profits.mean()), float(exp_payoff.mean()),
                        float(np.percentile(exp_payoff, lo_q)),
                        float(np.percentile(exp_payoff, hi_q)),
                        float((exp_payoff > 0).mean()), 0.0),
    ]
    return out


def _max_dd_pct_returns(returns: np.ndarray) -> float:
    """Max drawdown dari deret RETURN yang dimajemukkan (bukan P&L absolut)."""
    equity = np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(np.concatenate([[1.0], equity]))[1:]
    return float(((peak - equity) / peak).max() * 100.0)


def permute_drawdown_returns(
    returns: np.ndarray,
    n_iter: int = 20_000,
    seed: int = 42,
) -> dict:
    """
    Versi berbasis RETURN dari `permute_drawdown`, untuk strategi yang memajemukkan
    modal (portofolio dengan sizing % — bukan risiko nominal tetap seperti EA forex).

    Kenapa perlu: `permute_drawdown` menjumlahkan P&L rupiah di atas deposit tetap.
    Kalau modal tumbuh 3x, P&L bulan-bulan akhir jauh lebih besar secara nominal;
    begitu urutannya diacak, kerugian besar bisa jatuh di awal saat equity masih kecil
    dan menghasilkan drawdown > 100% — angka yang mustahil. Di ruang return, hasilnya
    selalu terbatas di bawah 100% dan tidak bergantung urutan pertumbuhan modal.
    """
    rng = np.random.default_rng(seed)
    observed = _max_dd_pct_returns(returns)

    dds = np.empty(n_iter)
    for i in range(n_iter):
        dds[i] = _max_dd_pct_returns(rng.permutation(returns))

    return {
        "observed": observed,
        "median": float(np.median(dds)),
        "p75": float(np.percentile(dds, 75)),
        "p95": float(np.percentile(dds, 95)),
        "p99": float(np.percentile(dds, 99)),
        "max": float(dds.max()),
        "pct_worse_than_observed": float((dds > observed).mean() * 100),
    }


def permute_drawdown(
    profits: np.ndarray,
    deposit: float,
    n_iter: int = 20_000,
    seed: int = 42,
) -> dict:
    """
    Acak URUTAN trade (tanpa mengubah komposisinya) -> distribusi Max Drawdown.

    Berguna untuk menjawab: "DD 3.98% yang terlihat di backtest itu tipikal,
    atau kebetulan urutannya sedang bagus?"
    """
    rng = np.random.default_rng(seed)
    observed = _max_dd_pct(profits, deposit)

    dds = np.empty(n_iter)
    for i in range(n_iter):
        dds[i] = _max_dd_pct(rng.permutation(profits), deposit)

    return {
        "observed": observed,
        "median": float(np.median(dds)),
        "p75": float(np.percentile(dds, 75)),
        "p95": float(np.percentile(dds, 95)),
        "p99": float(np.percentile(dds, 99)),
        "max": float(dds.max()),
        "pct_worse_than_observed": float((dds > observed).mean() * 100),
    }
