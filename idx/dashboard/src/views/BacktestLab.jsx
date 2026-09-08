import { useState } from "react";
import { runBacktest } from "../api";
import KpiCard from "../components/KpiCard";
import SectionTitle from "../components/SectionTitle";
import EquityChart from "../components/EquityChart";
import YearlyChart from "../components/YearlyChart";
import BootstrapPanel from "../components/BootstrapPanel";

const PERIODS = [
  { label: "Eksplorasi 2019–2023", start: "2019-01-01", end: "2023-12-31", vault: false },
  { label: "Brankas 2024–2026", start: "2024-01-01", end: "2026-12-31", vault: true },
  { label: "Gabungan 2019–2026", start: "2019-01-01", end: "2026-12-31", vault: true },
];

function Field({ label, hint, children }) {
  return (
    <div>
      <label style={{ display: "block", fontSize: 11, color: "var(--text-dim)", marginBottom: 5 }}>{label}</label>
      {children}
      {hint && <div style={{ fontSize: 10, color: "var(--text-faint)", marginTop: 4 }}>{hint}</div>}
    </div>
  );
}

const inputStyle = {
  background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8,
  padding: "8px 10px", color: "var(--text)", fontSize: 13, width: "100%",
  fontFamily: "var(--mono)",
};

export default function BacktestLab() {
  const [lookback, setLookback] = useState(6);
  const [topN, setTopN] = useState(9);
  const [costBuy, setCostBuy] = useState(0.20);
  const [costSell, setCostSell] = useState(0.30);
  const [capital, setCapital] = useState(100_000_000);
  const [periodIdx, setPeriodIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const period = PERIODS[periodIdx];

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await runBacktest({
        lookback_months: lookback,
        top_n: topN,
        cost_buy_pct: costBuy,
        cost_sell_pct: costSell,
        capital0: capital,
        start: period.start,
        end: period.end,
      });
      setResult(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const equity = result && {
    dates: result.months.map((m) => m.date),
    strategy: result.months.map((m) => m.capital),
    benchmark: result.benchmark,
  };

  return (
    <div>
      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 14 }}>
          <Field label="Lookback momentum" hint="berapa bulan return diukur">
            <select value={lookback} onChange={(e) => setLookback(Number(e.target.value))} style={inputStyle}>
              {[1, 2, 3, 6, 9, 12].map((m) => <option key={m} value={m}>{m} bulan</option>)}
            </select>
          </Field>
          <Field label="Jumlah saham" hint="dipegang tiap bulan">
            <select value={topN} onChange={(e) => setTopN(Number(e.target.value))} style={inputStyle}>
              {[3, 5, 9, 12, 15, 20].map((n) => <option key={n} value={n}>{n} saham</option>)}
            </select>
          </Field>
          <Field label="Biaya beli (%)">
            <input type="number" step="0.05" value={costBuy} onChange={(e) => setCostBuy(Number(e.target.value))} style={inputStyle} />
          </Field>
          <Field label="Biaya jual (%)" hint="termasuk pajak 0,1%">
            <input type="number" step="0.05" value={costSell} onChange={(e) => setCostSell(Number(e.target.value))} style={inputStyle} />
          </Field>
          <Field label="Modal awal">
            <input type="number" step="10000000" value={capital} onChange={(e) => setCapital(Number(e.target.value))} style={inputStyle} />
          </Field>
          <Field label="Periode">
            <select value={periodIdx} onChange={(e) => setPeriodIdx(Number(e.target.value))} style={inputStyle}>
              {PERIODS.map((p, i) => <option key={p.label} value={i}>{p.label}</option>)}
            </select>
          </Field>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 16 }}>
          <button
            onClick={run}
            disabled={loading}
            style={{
              background: "var(--accent)", border: "none", borderRadius: 8, padding: "9px 20px",
              color: "#fff", fontSize: 13, fontWeight: 600, cursor: loading ? "wait" : "pointer",
            }}
          >
            {loading ? "Menghitung…" : "Jalankan backtest"}
          </button>
          {error && <span style={{ color: "var(--bad)", fontSize: 12 }}>{error}</span>}
        </div>
      </div>

      {period.vault && (
        <div style={{ background: "rgba(224,168,62,0.08)", border: "1px solid rgba(224,168,62,0.35)", borderRadius: 10, padding: "12px 14px", marginTop: 14, fontSize: 12, color: "var(--text-dim)" }}>
          <b style={{ color: "var(--warn)" }}>Periode ini menyentuh brankas.</b> Menurut METHODOLOGY 1.1, data
          2024–2026 disisihkan untuk satu kali uji akhir. Setiap kali Anda menyetel parameter sambil melihat
          hasil periode ini, nilai brankasnya berkurang — hasil jadi terlalu optimistis tanpa terasa.
        </div>
      )}

      {result && (
        <>
          <SectionTitle note={`${result.metrics.n_months} bulan · lookback ${result.params.lookback_months}b · ${result.params.top_n} saham`}>
            Hasil
          </SectionTitle>
          <div className="kpi-grid">
            <KpiCard label="CAGR" value={`${result.metrics.cagr_pct > 0 ? "+" : ""}${result.metrics.cagr_pct}%`} tone={result.metrics.cagr_pct > 0 ? "good" : "bad"} />
            <KpiCard label="Return total" value={`${result.metrics.total_return_pct > 0 ? "+" : ""}${result.metrics.total_return_pct}%`} tone={result.metrics.total_return_pct > 0 ? "good" : "bad"} />
            <KpiCard label="Profit factor" value={result.metrics.pf ?? "—"} tone={result.metrics.pf > 1 ? "good" : "bad"} sub="unit = bulan" />
            <KpiCard label="Win rate" value={`${result.metrics.win_rate_pct}%`} sub="bulanan" />
            <KpiCard label="Max DD (p95)" value={`${result.drawdown_permutation.p95.toFixed(1)}%`} tone="warn" sub={`backtest: ${result.metrics.max_dd_pct}%`} />
            <KpiCard label="Modal akhir" value={`Rp${(result.metrics.final_capital / 1e6).toFixed(0)}jt`} sub={`dari Rp${(result.params.capital0 / 1e6).toFixed(0)}jt`} />
          </div>

          <SectionTitle note="Garis putus-putus = equal-weight buy&hold tanpa biaya">Equity curve</SectionTitle>
          <EquityChart equity={equity} />

          <SectionTitle>Performa per tahun</SectionTitle>
          <YearlyChart yearly={result.yearly} />

          <SectionTitle note="Bootstrap 5.000 iterasi · permutasi DD 2.000 iterasi">Seberapa pasti hasil ini?</SectionTitle>
          <BootstrapPanel bootstrap={result.bootstrap} ddPermutation={result.drawdown_permutation} />

          <SectionTitle>Riwayat rebalance</SectionTitle>
          <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
            <div className="scrollbar-thin" style={{ maxHeight: 320, overflowY: "auto" }}>
              <table style={{ fontSize: 12 }}>
                <thead style={{ position: "sticky", top: 0, background: "var(--panel)" }}>
                  <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
                    <td style={{ padding: "4px 10px 4px 0" }}>Bulan</td>
                    <td style={{ padding: "4px 10px", textAlign: "right" }}>P&L</td>
                    <td style={{ padding: "4px 10px", textAlign: "right" }}>Modal</td>
                    <td style={{ padding: "4px 0" }}>Portofolio</td>
                  </tr>
                </thead>
                <tbody>
                  {result.months.map((m) => (
                    <tr key={m.date} style={{ borderTop: "1px solid var(--border)" }}>
                      <td className="mono" style={{ padding: "5px 10px 5px 0", whiteSpace: "nowrap" }}>{m.date}</td>
                      <td className="mono" style={{ padding: "5px 10px", textAlign: "right", color: m.pnl >= 0 ? "var(--good)" : "var(--bad)" }}>
                        {m.pnl >= 0 ? "+" : ""}{(m.pnl / 1e6).toFixed(1)}jt
                      </td>
                      <td className="mono" style={{ padding: "5px 10px", textAlign: "right", color: "var(--text-dim)" }}>{(m.capital / 1e6).toFixed(0)}jt</td>
                      <td className="mono" style={{ padding: "5px 0", color: "var(--text-dim)", fontSize: 11 }}>
                        {m.holdings.length ? m.holdings.join(" · ") : "cash"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
