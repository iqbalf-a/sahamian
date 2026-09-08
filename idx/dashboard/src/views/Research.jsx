import data from "../data.json";
import KpiCard from "../components/KpiCard";
import SectionTitle from "../components/SectionTitle";
import EquityChart from "../components/EquityChart";
import YearlyChart from "../components/YearlyChart";
import BootstrapPanel from "../components/BootstrapPanel";
import CostTable from "../components/CostTable";
import UniverseTable from "../components/UniverseTable";
import CaveatBanner from "../components/CaveatBanner";

const PERIOD_LABELS = {
  explore: ["Eksplorasi 2019–2023", "periode perancangan — bias optimis"],
  vault: ["Brankas 2024–2026", "belum tersentuh saat strategi dirancang"],
  combined: ["Gabungan 2019–2026", "angka headline yang sebaiknya dipakai"],
};

function PeriodComparison({ periods }) {
  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16, overflowX: "auto" }}>
      <table style={{ fontSize: 13 }}>
        <thead>
          <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
            <td style={{ padding: "4px 12px 8px 0" }}>Periode</td>
            <td style={{ padding: "4px 12px 8px", textAlign: "right" }}>Bulan</td>
            <td style={{ padding: "4px 12px 8px", textAlign: "right" }}>CAGR</td>
            <td style={{ padding: "4px 12px 8px", textAlign: "right" }}>PF</td>
            <td style={{ padding: "4px 12px 8px", textAlign: "right" }}>Win rate</td>
            <td style={{ padding: "4px 0 8px", textAlign: "right" }}>DD p95</td>
          </tr>
        </thead>
        <tbody>
          {Object.entries(PERIOD_LABELS).map(([key, [label, note]]) => {
            const p = periods[key];
            if (!p) return null;
            const strong = key === "combined";
            return (
              <tr key={key} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ padding: "8px 12px 8px 0" }}>
                  <div style={{ fontWeight: strong ? 600 : 400 }}>{label}</div>
                  <div style={{ fontSize: 11, color: "var(--text-faint)" }}>{note}</div>
                </td>
                <td className="mono" style={{ padding: "8px 12px", textAlign: "right", color: "var(--text-dim)" }}>{p.metrics.n_months}</td>
                <td className="mono" style={{ padding: "8px 12px", textAlign: "right", color: p.metrics.cagr_pct > 0 ? "var(--good)" : "var(--bad)", fontWeight: strong ? 600 : 400 }}>
                  {p.metrics.cagr_pct > 0 ? "+" : ""}{p.metrics.cagr_pct}%
                </td>
                <td className="mono" style={{ padding: "8px 12px", textAlign: "right" }}>{p.metrics.pf}</td>
                <td className="mono" style={{ padding: "8px 12px", textAlign: "right", color: "var(--text-dim)" }}>{p.metrics.win_rate_pct}%</td>
                <td className="mono" style={{ padding: "8px 0", textAlign: "right", color: "var(--warn)" }}>{p.drawdown_permutation.p95.toFixed(1)}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 12, lineHeight: 1.6 }}>
        Berbeda dari riset forex sebelumnya (PF jatuh 2,37 → 1,08 saat brankas dibuka), di sini PF
        bertahan (1,81 → 1,82). Tapi perhatikan sebarannya per tahun: 2025 {periods.vault?.yearly?.find((y) => y.year === 2025)?.return_pct}% lalu
        2026 {periods.vault?.yearly?.find((y) => y.year === 2026)?.return_pct}% — ini bukan kurva yang mudah dijalani.
      </div>
    </div>
  );
}

export default function Research() {
  const { meta, kpi, equity, yearly, bootstrap, drawdown_permutation, universe_stats, cost_table, periods } = data;

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>
          Eksperimen 001 &mdash; Momentum lintas saham LQ45
        </h2>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>
          {meta.universe} &middot; periode eksplorasi {meta.period} &middot; brankas {meta.vault_period}{" "}
          {meta.vault_opened ? "sudah dibuka" : "belum dibuka"}
        </div>
      </div>

      <CaveatBanner />

      <div className="kpi-grid">
        <KpiCard label="CAGR strategi" value={`+${kpi.cagr_pct}%`} tone="good" sub={`vs +${kpi.bh_cagr_pct}% buy&hold`} />
        <KpiCard label="Return total" value={`+${kpi.total_return_pct}%`} sub={`${kpi.n_months} bulan`} />
        <KpiCard label="Profit factor" value={kpi.pf.toFixed(2)} tone={kpi.pf > 1 ? "good" : "bad"} sub="unit = bulan" />
        <KpiCard label="Win rate" value={`${kpi.win_rate_pct}%`} sub="bulanan" />
        <KpiCard label="Max DD (p95)" value={`${kpi.max_dd_p95_pct.toFixed(1)}%`} tone="warn" sub={`backtest: ${kpi.max_dd_pct}%`} />
        <KpiCard label="Biaya transaksi" value={`${kpi.total_cost_pct}%`} sub={`Rp${(kpi.total_cost / 1e6).toFixed(1)}jt / 5 thn`} />
      </div>

      <SectionTitle note="Brankas sudah dibuka 2026-09-07 — jangan tuning parameter terhadap angka ini">
        Eksplorasi vs brankas
      </SectionTitle>
      <PeriodComparison periods={periods} />

      <SectionTitle note="Periode eksplorasi · modal awal Rp100 juta, rebalance bulanan">Equity curve</SectionTitle>
      <EquityChart equity={equity} />

      <SectionTitle>Performa per tahun</SectionTitle>
      <YearlyChart yearly={yearly} />

      <SectionTitle note="Bagian 2.3 METHODOLOGY.md — analisis statistik wajib">Seberapa pasti hasil ini?</SectionTitle>
      <BootstrapPanel bootstrap={bootstrap} ddPermutation={drawdown_permutation} />

      <SectionTitle note="Aturan 1.3 — cek sebelum menulis kode">Kelayakan biaya transaksi</SectionTitle>
      <CostTable costTable={cost_table} />

      <SectionTitle note="Dasar seleksi momentum bulanan">Universe LQ45</SectionTitle>
      <UniverseTable rows={universe_stats} />
    </div>
  );
}
