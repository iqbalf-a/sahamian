import { useEffect, useState } from "react";
import {
  ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Area,
} from "recharts";
import { getStock } from "../api";
import SectionTitle from "../components/SectionTitle";
import PriceChart from "../components/PriceChart";
import CorporateActions from "../components/CorporateActions";
import StockSummary from "../components/StockSummary";

const RANGES = [
  { label: "6B", bars: 126 },
  { label: "1T", bars: 252 },
  { label: "2T", bars: 500 },
  { label: "5T", bars: 1250 },
];

const fmtPct = (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(1)}%`);

function Verdict({ stats, price }) {
  const checks = [
    {
      ok: stats.above_sma200,
      label: "Tren jangka panjang",
      detail: stats.above_sma200 ? "Harga di atas SMA200 — tren naik" : "Harga di bawah SMA200 — tren turun",
    },
    {
      ok: stats.above_sma50,
      label: "Tren menengah",
      detail: stats.above_sma50 ? "Harga di atas SMA50" : "Harga di bawah SMA50",
    },
    {
      ok: stats.momentum_pct > 0,
      label: `Momentum ${stats.lookback_months} bulan`,
      detail: `${fmtPct(stats.momentum_pct)} — ${stats.momentum_pct > 0 ? "memenuhi syarat seleksi momentum" : "negatif, tidak dipilih strategi"}`,
    },
    {
      ok: stats.avg_value_bn >= 10,
      label: "Likuiditas",
      detail: `Rp${stats.avg_value_bn?.toFixed(1)} M/hari — ${stats.avg_value_bn >= 10 ? "cukup likuid" : "tipis, slippage bisa besar"}`,
    },
    {
      ok: stats.rsi < 70,
      label: "RSI",
      detail: `${stats.rsi} — ${stats.rsi > 70 ? "overbought, rawan koreksi" : stats.rsi < 30 ? "oversold" : "netral"}`,
    },
  ];

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 12 }}>
        Penilaian menurut kriteria strategi momentum
      </div>
      {checks.map((c) => (
        <div key={c.label} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "7px 0", borderTop: "1px solid var(--border)" }}>
          <span style={{ color: c.ok ? "var(--good)" : "var(--bad)", fontSize: 13, lineHeight: 1.5 }}>{c.ok ? "✓" : "✕"}</span>
          <div>
            <div style={{ fontSize: 13 }}>{c.label}</div>
            <div style={{ fontSize: 11, color: "var(--text-faint)" }}>{c.detail}</div>
          </div>
        </div>
      ))}
      <div style={{ borderTop: "1px solid var(--border)", marginTop: 8, paddingTop: 10, fontSize: 11, color: "var(--text-faint)" }}>
        1 lot = Rp{stats.lot_price?.toLocaleString("id-ID")} · fraksi harga Rp{stats.tick_size} ·
        biaya bolak-balik 0,5% = Rp{Math.round(price * 100 * 0.005).toLocaleString("id-ID")}/lot
      </div>
    </div>
  );
}

function CostRatio({ price }) {
  const rows = [3, 5, 10, 15, 20].map((target) => {
    const ratio = (0.5 / target) * 100;
    return {
      target,
      ratio,
      exit: Math.round(price * (1 + target / 100)),
      verdict: ratio < 5 ? ["Aman", "var(--good)"] : ratio < 15 ? ["Berat", "var(--warn)"] : ["Tidak layak", "var(--bad)"],
    };
  });

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 12 }}>
        Kelayakan target profit di harga sekarang
      </div>
      <table style={{ fontSize: 12 }}>
        <thead>
          <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
            <td style={{ padding: "4px 0" }}>Target</td>
            <td style={{ padding: "4px 8px", textAlign: "right" }}>Harga jual</td>
            <td style={{ padding: "4px 8px", textAlign: "right" }}>Rasio biaya</td>
            <td style={{ padding: "4px 0", textAlign: "right" }}>Verdict</td>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.target} style={{ borderTop: "1px solid var(--border)" }}>
              <td className="mono" style={{ padding: "6px 0" }}>+{r.target}%</td>
              <td className="mono" style={{ padding: "6px 8px", textAlign: "right" }}>{r.exit.toLocaleString("id-ID")}</td>
              <td className="mono" style={{ padding: "6px 8px", textAlign: "right", color: "var(--text-dim)" }}>{r.ratio.toFixed(1)}%</td>
              <td style={{ padding: "6px 0", textAlign: "right", color: r.verdict[1] }}>{r.verdict[0]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function StockDetail({ ticker, onBack }) {
  const [bars, setBars] = useState(500);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState("line");
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && setExpanded(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    setData(null);
    setError(null);
    getStock(ticker, bars).then(setData).catch((e) => setError(e.message));
  }, [ticker, bars]);

  if (error) return <div style={{ color: "var(--bad)" }}>{error}</div>;
  if (!data) return <div style={{ color: "var(--text-faint)", padding: 40 }}>Memuat {ticker}…</div>;

  const { stats, series, price } = data;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4, flexWrap: "wrap" }}>
        <button
          onClick={onBack}
          style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--text-dim)", borderRadius: 6, padding: "4px 10px", fontSize: 12, cursor: "pointer" }}
        >
          ← Kembali
        </button>
        <h2 className="mono" style={{ fontSize: 22, margin: 0, fontWeight: 600 }}>{data.ticker}</h2>
        <span className="mono" style={{ fontSize: 20 }}>{price.toLocaleString("id-ID")}</span>
        <span style={{ fontSize: 12, color: pctToneColor(stats.ret_1m_pct) }}>{fmtPct(stats.ret_1m_pct)} (1 bulan)</span>
        <span style={{ fontSize: 11, color: "var(--text-faint)", marginLeft: "auto" }}>data s/d {data.last_date}</span>
      </div>

      <div style={{ marginTop: 16 }}>
        <StockSummary data={data} />
      </div>

      <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap", alignItems: "center" }}>
        {RANGES.map((r) => (
          <button
            key={r.label}
            onClick={() => setBars(r.bars)}
            style={{
              background: bars === r.bars ? "var(--accent-dim)" : "transparent",
              border: `1px solid ${bars === r.bars ? "var(--accent)" : "var(--border)"}`,
              color: bars === r.bars ? "var(--text)" : "var(--text-dim)",
              borderRadius: 6, padding: "3px 10px", fontSize: 12, cursor: "pointer",
            }}
          >
            {r.label}
          </button>
        ))}

        <span style={{ width: 1, height: 18, background: "var(--border)", margin: "0 6px" }} />

        {[["line", "Garis"], ["candle", "Candle"]].map(([m, label]) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            style={{
              background: mode === m ? "var(--accent-dim)" : "transparent",
              border: `1px solid ${mode === m ? "var(--accent)" : "var(--border)"}`,
              color: mode === m ? "var(--text)" : "var(--text-dim)",
              borderRadius: 6, padding: "3px 10px", fontSize: 12, cursor: "pointer",
            }}
          >
            {label}
          </button>
        ))}

        <button
          onClick={() => setExpanded(true)}
          style={{
            marginLeft: "auto", background: "transparent", border: "1px solid var(--border)",
            color: "var(--text-dim)", borderRadius: 6, padding: "3px 10px", fontSize: 12, cursor: "pointer",
          }}
        >
          ⤢ Perbesar
        </button>
      </div>

      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: "16px 8px 8px" }}>
        <div style={{ display: "flex", gap: 14, padding: "0 12px 8px", fontSize: 11, color: "var(--text-dim)", flexWrap: "wrap" }}>
          {[["Harga", "#e6e9f0"], ["SMA20", "#4f8cff"], ["SMA50", "#e0a83e"], ["SMA200", "#e5584f"]].map(([l, c]) => (
            <span key={l}><span style={{ display: "inline-block", width: 10, height: 2, background: c, marginRight: 5, verticalAlign: "middle" }} />{l}</span>
          ))}
        </div>
        <PriceChart series={series} mode={mode} height={300} />

        <div style={{ padding: "4px 12px 0", fontSize: 11, color: "var(--text-dim)" }}>RSI (14)</div>
        <ResponsiveContainer width="100%" height={110}>
          <ComposedChart data={series} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="date" hide />
            <YAxis domain={[0, 100]} ticks={[30, 70]} tick={{ fill: "var(--text-faint)", fontSize: 10 }} tickLine={false} axisLine={false} width={56} />
            <ReferenceLine y={70} stroke="var(--warn)" strokeDasharray="3 3" />
            <ReferenceLine y={30} stroke="var(--accent)" strokeDasharray="3 3" />
            <Tooltip contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
            <Area type="monotone" dataKey="rsi" name="RSI" stroke="#8992a8" fill="rgba(137,146,168,0.12)" strokeWidth={1.4} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <SectionTitle>Analisis</SectionTitle>
      <div className="two-col">
        <Verdict stats={stats} price={price} />
        <CostRatio price={price} />
      </div>

      <SectionTitle note="Dividen & stock split dari yfinance">Corporate action</SectionTitle>
      <CorporateActions ticker={data.ticker} />

      {expanded && (
        <div
          onClick={(e) => e.target === e.currentTarget && setExpanded(false)}
          style={{
            position: "fixed", inset: 0, zIndex: 100, background: "rgba(6,8,13,0.92)",
            display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
          }}
        >
          <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, width: "100%", maxWidth: 1400 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 12, flexWrap: "wrap" }}>
              <span className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{data.ticker}</span>
              <span className="mono" style={{ fontSize: 16 }}>{price.toLocaleString("id-ID")}</span>
              <div style={{ display: "flex", gap: 6 }}>
                {RANGES.map((r) => (
                  <button
                    key={r.label}
                    onClick={() => setBars(r.bars)}
                    style={{
                      background: bars === r.bars ? "var(--accent-dim)" : "transparent",
                      border: `1px solid ${bars === r.bars ? "var(--accent)" : "var(--border)"}`,
                      color: "var(--text)", borderRadius: 6, padding: "3px 10px", fontSize: 12, cursor: "pointer",
                    }}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                {[["line", "Garis"], ["candle", "Candle"]].map(([m, label]) => (
                  <button
                    key={m}
                    onClick={() => setMode(m)}
                    style={{
                      background: mode === m ? "var(--accent-dim)" : "transparent",
                      border: `1px solid ${mode === m ? "var(--accent)" : "var(--border)"}`,
                      color: "var(--text)", borderRadius: 6, padding: "3px 10px", fontSize: 12, cursor: "pointer",
                    }}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setExpanded(false)}
                style={{
                  marginLeft: "auto", background: "transparent", border: "1px solid var(--border)",
                  color: "var(--text-dim)", borderRadius: 6, padding: "4px 12px", fontSize: 12, cursor: "pointer",
                }}
              >
                Tutup (Esc)
              </button>
            </div>
            <PriceChart series={series} mode={mode} height={Math.max(window.innerHeight - 220, 320)} />
          </div>
        </div>
      )}
    </div>
  );
}

function pctToneColor(v) {
  return v == null ? "var(--text-faint)" : v > 0 ? "var(--good)" : "var(--bad)";
}
