import { useEffect, useMemo, useState } from "react";
import { getScreen } from "../../api";

const COLS = [
  { key: "rank", label: "#", align: "left", w: 40 },
  { key: "ticker", label: "Saham", align: "left" },
  { key: "price", label: "Harga", align: "right" },
  { key: "momentum_pct", label: "Momentum", align: "right" },
  { key: "ret_1m_pct", label: "1B", align: "right" },
  { key: "ret_3m_pct", label: "3B", align: "right" },
  { key: "ret_12m_pct", label: "12B", align: "right" },
  { key: "rsi", label: "RSI", align: "right" },
  { key: "trend", label: "Tren", align: "left" },
  { key: "avg_value_bn", label: "Likuiditas", align: "right" },
];

const pctColor = (v) => (v == null ? "var(--text-faint)" : v > 0 ? "var(--good)" : v < 0 ? "var(--bad)" : "var(--text-dim)");
const fmtPct = (v) => (v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(1)}%`);

function TrendBadge({ row }) {
  const items = [
    { on: row.above_sma50, label: "50" },
    { on: row.above_sma200, label: "200" },
  ];
  return (
    <span style={{ display: "inline-flex", gap: 4 }}>
      {items.map((it) => (
        <span
          key={it.label}
          title={`Harga ${it.on ? "di atas" : "di bawah"} SMA${it.label}`}
          style={{
            fontSize: 10, padding: "1px 5px", borderRadius: 4,
            background: it.on ? "rgba(52,192,133,0.15)" : "rgba(229,88,79,0.12)",
            color: it.on ? "var(--good)" : "var(--bad)",
          }}
        >
          {it.label}
        </span>
      ))}
    </span>
  );
}

export default function Screener({ onSelect }) {
  const [lookback, setLookback] = useState(6);
  const [topN, setTopN] = useState(9);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState({ key: "rank", asc: true });

  const load = () => {
    setLoading(true);
    setError(null);
    getScreen(lookback, topN)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [lookback, topN]);

  const rows = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toUpperCase();
    const filtered = q ? data.rows.filter((r) => r.ticker.includes(q)) : data.rows;
    const { key, asc } = sort;
    return [...filtered].sort((a, b) => {
      const av = a[key], bv = b[key];
      if (av == null) return 1;
      if (bv == null) return -1;
      return (av > bv ? 1 : av < bv ? -1 : 0) * (asc ? 1 : -1);
    });
  }, [data, query, sort]);

  const notFound = data && query.trim() && rows.length === 0;

  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "flex-end", marginBottom: 16 }}>
        <div style={{ flex: "1 1 220px" }}>
          <label style={{ display: "block", fontSize: 11, color: "var(--text-dim)", marginBottom: 5 }}>
            Filter tabel
          </label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value.toUpperCase())}
            placeholder="mis. BBCA — cari emiten lain lewat kotak di kanan atas"
            style={{
              width: "100%", background: "var(--panel-2)", border: "1px solid var(--border)",
              borderRadius: 8, padding: "8px 10px", color: "var(--text)", fontSize: 13,
              fontFamily: "var(--mono)",
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: 11, color: "var(--text-dim)", marginBottom: 5 }}>
            Lookback momentum
          </label>
          <select
            value={lookback}
            onChange={(e) => setLookback(Number(e.target.value))}
            style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 10px", color: "var(--text)", fontSize: 13 }}
          >
            {[1, 3, 6, 9, 12].map((m) => (
              <option key={m} value={m}>{m} bulan</option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: 11, color: "var(--text-dim)", marginBottom: 5 }}>
            Jumlah dipegang
          </label>
          <select
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 10px", color: "var(--text)", fontSize: 13 }}
          >
            {[3, 5, 9, 12, 15].map((n) => (
              <option key={n} value={n}>{n} saham</option>
            ))}
          </select>
        </div>
      </div>

      {data && (
        <div style={{ background: "rgba(79,140,255,0.07)", border: "1px solid var(--accent-dim)", borderRadius: 10, padding: "12px 14px", marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 6 }}>
            Sinyal per {data.as_of} — {topN} saham momentum {lookback} bulan tertinggi yang masih positif
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {data.picks.map((t) => (
              <button
                key={t}
                onClick={() => onSelect(t)}
                className="mono"
                style={{
                  background: "var(--accent-dim)", border: "1px solid var(--accent)", color: "var(--text)",
                  borderRadius: 6, padding: "3px 9px", fontSize: 12, cursor: "pointer", fontWeight: 600,
                }}
              >
                {t}
              </button>
            ))}
            {data.picks.length === 0 && (
              <span style={{ fontSize: 12, color: "var(--warn)" }}>
                Tidak ada saham dengan momentum positif — strategi memilih 100% cash.
              </span>
            )}
          </div>
        </div>
      )}

      {error && (
        <div style={{ color: "var(--bad)", fontSize: 13, marginBottom: 12 }}>{error}</div>
      )}

      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden" }}>
        <div className="scrollbar-thin" style={{ maxHeight: 560, overflowY: "auto" }}>
          <table style={{ fontSize: 13 }}>
            <thead style={{ position: "sticky", top: 0, background: "var(--panel)", zIndex: 1 }}>
              <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
                {COLS.map((c) => (
                  <td
                    key={c.key}
                    onClick={() => c.key !== "trend" && setSort((s) => ({ key: c.key, asc: s.key === c.key ? !s.asc : c.key === "rank" }))}
                    style={{
                      padding: "10px 10px", textAlign: c.align, width: c.w,
                      cursor: c.key === "trend" ? "default" : "pointer", userSelect: "none",
                      borderBottom: "1px solid var(--border)",
                    }}
                  >
                    {c.label}{sort.key === c.key ? (sort.asc ? " ▲" : " ▼") : ""}
                  </td>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={COLS.length} style={{ padding: 24, textAlign: "center", color: "var(--text-faint)" }}>Memuat…</td></tr>
              )}
              {!loading && rows.map((r) => (
                <tr
                  key={r.ticker}
                  onClick={() => onSelect(r.ticker)}
                  style={{ borderTop: "1px solid var(--border)", cursor: "pointer", background: r.selected ? "rgba(79,140,255,0.06)" : "transparent" }}
                >
                  <td className="mono" style={{ padding: "8px 10px", color: "var(--text-faint)" }}>{r.rank ?? "—"}</td>
                  <td style={{ padding: "8px 10px" }}>
                    <span className="mono" style={{ fontWeight: 600 }}>{r.ticker}</span>
                    {r.selected && (
                      <span style={{ marginLeft: 8, fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(52,192,133,0.15)", color: "var(--good)" }}>
                        SINYAL
                      </span>
                    )}
                  </td>
                  <td className="mono" style={{ padding: "8px 10px", textAlign: "right" }}>{r.price?.toLocaleString("id-ID")}</td>
                  <td className="mono" style={{ padding: "8px 10px", textAlign: "right", color: pctColor(r.momentum_pct), fontWeight: 600 }}>{fmtPct(r.momentum_pct)}</td>
                  <td className="mono" style={{ padding: "8px 10px", textAlign: "right", color: pctColor(r.ret_1m_pct) }}>{fmtPct(r.ret_1m_pct)}</td>
                  <td className="mono" style={{ padding: "8px 10px", textAlign: "right", color: pctColor(r.ret_3m_pct) }}>{fmtPct(r.ret_3m_pct)}</td>
                  <td className="mono" style={{ padding: "8px 10px", textAlign: "right", color: pctColor(r.ret_12m_pct) }}>{fmtPct(r.ret_12m_pct)}</td>
                  <td className="mono" style={{ padding: "8px 10px", textAlign: "right", color: r.rsi > 70 ? "var(--warn)" : r.rsi < 30 ? "var(--accent)" : "var(--text-dim)" }}>{r.rsi ?? "—"}</td>
                  <td style={{ padding: "8px 10px" }}><TrendBadge row={r} /></td>
                  <td className="mono" style={{ padding: "8px 10px", textAlign: "right", color: "var(--text-dim)" }}>{r.avg_value_bn?.toFixed(1)} M</td>
                </tr>
              ))}
              {notFound && !loading && (
                <tr><td colSpan={COLS.length} style={{ padding: 24, textAlign: "center", color: "var(--text-faint)" }}>
                  {query} tidak ada di universe LQ45 — pakai kotak pencarian di kanan atas untuk
                  menganalisis emiten di luar universe.
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 10 }}>
        Klik baris untuk analisis detail. Likuiditas = rata-rata nilai transaksi harian 60 hari terakhir (Rp miliar).
      </div>
    </div>
  );
}
