import { useEffect, useState } from "react";
import SectionTitle from "../components/SectionTitle";

const METRICS = [
  { key: "cagr_pct", label: "CAGR", fmt: (v) => `${v.toFixed(1)}%`, higherBetter: true },
  { key: "pf", label: "Profit factor", fmt: (v) => v.toFixed(2), higherBetter: true },
  { key: "max_dd_pct", label: "Max drawdown", fmt: (v) => `${v.toFixed(0)}%`, higherBetter: false },
];

function Heatmap({ rows, metric }) {
  const values = rows.map((r) => r[metric.key]).filter((v) => v != null);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const lookbacks = [...new Set(rows.map((r) => r.lookback))].sort((a, b) => a - b);
  const topNs = [...new Set(rows.map((r) => r.top_n))].sort((a, b) => a - b);

  const shade = (v) => {
    if (v == null) return "transparent";
    let t = (v - min) / (max - min || 1);
    if (!metric.higherBetter) t = 1 - t;
    // satu ramp biru: gelap = lemah, terang = kuat
    return `rgba(79,140,255,${(0.08 + t * 0.55).toFixed(3)})`;
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ fontSize: 13, minWidth: 480 }}>
        <thead>
          <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
            <td style={{ padding: "4px 10px 8px 0" }}>Lookback</td>
            {topNs.map((n) => (
              <td key={n} style={{ padding: "4px 8px 8px", textAlign: "center" }}>{n} saham</td>
            ))}
          </tr>
        </thead>
        <tbody>
          {lookbacks.map((lb) => (
            <tr key={lb}>
              <td className="mono" style={{ padding: "3px 10px 3px 0", color: "var(--text-dim)", whiteSpace: "nowrap" }}>
                {lb} bulan
              </td>
              {topNs.map((n) => {
                const cell = rows.find((r) => r.lookback === lb && r.top_n === n);
                const v = cell?.[metric.key];
                const isDefault = lb === 6 && n === 9;
                return (
                  <td key={n} style={{ padding: 2 }}>
                    <div
                      className="mono"
                      style={{
                        background: shade(v),
                        border: isDefault ? "1px solid var(--accent)" : "1px solid transparent",
                        borderRadius: 5, padding: "7px 4px", textAlign: "center", fontSize: 12,
                        color: "var(--text)",
                      }}
                      title={isDefault ? "konfigurasi default eksperimen 001" : undefined}
                    >
                      {v == null ? "—" : metric.fmt(v)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Sensitivity() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [metricIdx, setMetricIdx] = useState(0);

  useEffect(() => {
    fetch("/api/walkforward")
      .then((r) => (r.ok ? r.json() : r.json().then((b) => Promise.reject(new Error(b.detail)))))
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div style={{ color: "var(--bad)" }}>{error}</div>;
  if (!data) return <div style={{ color: "var(--text-faint)", padding: 40 }}>Memuat…</div>;

  const wf = data.walkforward_explore;
  const metric = METRICS[metricIdx];

  return (
    <div>
      <div style={{ background: "rgba(224,168,62,0.08)", border: "1px solid rgba(224,168,62,0.35)", borderRadius: 10, padding: "12px 14px", marginBottom: 4, fontSize: 12, color: "var(--text-dim)" }}>
        <b style={{ color: "var(--warn)" }}>Halaman ini untuk memahami, bukan untuk memilih.</b> Walk-forward
        di bawah menunjukkan memilih parameter dari data masa lalu justru kalah dari mematoknya tetap —
        jadi jangan pakai grid ini untuk mencari sel terbaik lalu memakainya. Semua angka periode
        eksplorasi 2019–2023.
      </div>

      <SectionTitle note="Latih 24 bulan → uji 12 bulan → geser">Walk-forward bergulir</SectionTitle>
      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
        <table style={{ fontSize: 13 }}>
          <thead>
            <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
              <td style={{ padding: "4px 12px 8px 0" }}>Jendela uji</td>
              <td style={{ padding: "4px 12px 8px", textAlign: "right" }}>Lookback dipilih</td>
              <td style={{ padding: "4px 12px 8px", textAlign: "right" }}>Hasil tuned</td>
              <td style={{ padding: "4px 0 8px", textAlign: "right" }}>Hasil patok 6 bulan</td>
            </tr>
          </thead>
          <tbody>
            {wf.windows.map((w) => (
              <tr key={w.test} style={{ borderTop: "1px solid var(--border)" }}>
                <td className="mono" style={{ padding: "7px 12px 7px 0" }}>{w.test}</td>
                <td className="mono" style={{ padding: "7px 12px", textAlign: "right", color: "var(--text-dim)" }}>{w.picked_lookback} bulan</td>
                <td className="mono" style={{ padding: "7px 12px", textAlign: "right", color: w.tuned.total_return_pct >= 0 ? "var(--good)" : "var(--bad)" }}>
                  {w.tuned.total_return_pct > 0 ? "+" : ""}{w.tuned.total_return_pct}%
                </td>
                <td className="mono" style={{ padding: "7px 0", textAlign: "right", color: w.fixed.total_return_pct >= 0 ? "var(--good)" : "var(--bad)" }}>
                  {w.fixed.total_return_pct > 0 ? "+" : ""}{w.fixed.total_return_pct}%
                </td>
              </tr>
            ))}
            <tr style={{ borderTop: "1px solid var(--border-strong, var(--border))" }}>
              <td style={{ padding: "9px 12px 0 0", fontWeight: 600 }}>Total majemuk</td>
              <td />
              <td className="mono" style={{ padding: "9px 12px 0", textAlign: "right", fontWeight: 600 }}>+{wf.tuned_total_pct}%</td>
              <td className="mono" style={{ padding: "9px 0 0", textAlign: "right", fontWeight: 600, color: "var(--good)" }}>+{wf.fixed_total_pct}%</td>
            </tr>
          </tbody>
        </table>
        <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 12, lineHeight: 1.6 }}>
          Mematok lookback 6 bulan mengalahkan memilihnya dari data latih (+{wf.fixed_total_pct}% vs
          +{wf.tuned_total_pct}%). Temuan yang sama muncul di riset forex sebelumnya — lihat METHODOLOGY 3.3.
        </div>
      </div>

      <SectionTitle note="36 kombinasi, periode eksplorasi · kotak bergaris biru = konfigurasi default">
        Sensitivitas parameter
      </SectionTitle>
      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
          {METRICS.map((m, i) => (
            <button
              key={m.key}
              onClick={() => setMetricIdx(i)}
              style={{
                background: metricIdx === i ? "var(--accent-dim)" : "transparent",
                border: `1px solid ${metricIdx === i ? "var(--accent)" : "var(--border)"}`,
                color: metricIdx === i ? "var(--text)" : "var(--text-dim)",
                borderRadius: 6, padding: "4px 12px", fontSize: 12, cursor: "pointer",
              }}
            >
              {m.label}
            </button>
          ))}
        </div>
        <Heatmap rows={data.sensitivity_explore} metric={metric} />
        <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 14, lineHeight: 1.7 }}>
          Dua pola: (1) lookback 2–3 bulan gagal sementara 6–12 bulan bekerja — bentuk yang cocok dengan
          literatur momentum klasik, bukan puncak acak; (2) makin sedikit saham dipegang makin tinggi
          return, mulus dan monoton. Konfigurasi terkonsentrasi (3 saham) bahkan punya CI Profit Factor
          yang tidak menyentuh 1 — tapi angka itu hasil menyisir 36 sel, jadi belum layak dipakai untuk
          berpindah konfigurasi. Lihat eksperimen 002 untuk alasan lengkapnya.
        </div>
      </div>
    </div>
  );
}
