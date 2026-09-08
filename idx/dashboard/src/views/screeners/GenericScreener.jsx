import { useEffect, useMemo, useState } from "react";

const fmtValue = (v, col) => {
  if (v == null) return "—";
  switch (col.format) {
    case "pct":
      return `${v > 0 && col.good ? "+" : ""}${v.toFixed(col.digits ?? 1)}%`;
    case "price":
      return v.toLocaleString("id-ID");
    case "ratio":
      return `${v.toFixed(col.digits ?? 2)}×`;
    case "bool":
      return v ? "✓" : "✕";
    case "ticker":
      return v;
    default:
      return typeof v === "number" ? v.toFixed(col.digits ?? 2) : v;
  }
};

const valueColor = (v, col) => {
  if (v == null) return "var(--text-faint)";
  if (col.format === "bool") return v ? "var(--good)" : "var(--bad)";
  if (!col.good) return "var(--text)";
  if (col.format === "pct" || col.format === "ratio" || col.format === "num") {
    if (col.good === "high") return v > 0 ? "var(--good)" : v < 0 ? "var(--bad)" : "var(--text-dim)";
    if (col.good === "low") return "var(--text-dim)";
  }
  return "var(--text)";
};

export default function GenericScreener({ templateId, onSelect }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sort, setSort] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setSort(null);
    fetch(`/api/screen/run/${templateId}`)
      .then((r) => (r.ok ? r.json() : r.json().then((b) => Promise.reject(new Error(b.detail)))))
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [templateId]);

  const rows = useMemo(() => {
    if (!data) return [];
    if (!sort) return data.rows;
    return [...data.rows].sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key];
      if (av == null) return 1;
      if (bv == null) return -1;
      return (av > bv ? 1 : av < bv ? -1 : 0) * (sort.asc ? 1 : -1);
    });
  }, [data, sort]);

  if (loading) return <div style={{ color: "var(--text-faint)", padding: 40 }}>Menghitung…</div>;
  if (error) return <div style={{ color: "var(--bad)", padding: 20 }}>{error}</div>;
  if (!data) return null;

  return (
    <div>
      {data.warning && (
        <div style={{ background: "rgba(224,168,62,0.08)", border: "1px solid rgba(224,168,62,0.35)", borderRadius: 10, padding: "12px 14px", marginBottom: 14, fontSize: 12, color: "var(--text-dim)", lineHeight: 1.65 }}>
          {data.warning}
        </div>
      )}

      {data.summary && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 16 }}>
          {Object.entries(data.summary).map(([k, v]) => (
            <div key={k} style={{ background: "var(--panel-2)", borderRadius: 8, padding: "10px 12px" }}>
              <div style={{ fontSize: 11, color: "var(--text-faint)", marginBottom: 3 }}>{k}</div>
              <div className="mono" style={{ fontSize: 14, color: "var(--text)" }}>{v}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden" }}>
        <div className="scrollbar-thin" style={{ maxHeight: 560, overflow: "auto" }}>
          <table style={{ fontSize: 13 }}>
            <thead style={{ position: "sticky", top: 0, background: "var(--panel)", zIndex: 1 }}>
              <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
                {data.columns.map((c) => (
                  <td
                    key={c.key}
                    title={c.hint || undefined}
                    onClick={() => setSort((s) => ({ key: c.key, asc: s?.key === c.key ? !s.asc : false }))}
                    style={{
                      padding: "10px", textAlign: c.align || "right", cursor: "pointer",
                      userSelect: "none", whiteSpace: "nowrap", borderBottom: "1px solid var(--border)",
                    }}
                  >
                    {c.label}{sort?.key === c.key ? (sort.asc ? " ▲" : " ▼") : ""}
                    {c.hint && <span style={{ color: "var(--accent)", marginLeft: 3 }}>·</span>}
                  </td>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.ticker}
                  onClick={() => onSelect(r.ticker)}
                  style={{
                    borderTop: "1px solid var(--border)", cursor: "pointer",
                    background: r.signal ? "rgba(79,140,255,0.06)" : "transparent",
                  }}
                >
                  {data.columns.map((c) => (
                    <td
                      key={c.key}
                      className="mono"
                      style={{
                        padding: "8px 10px", textAlign: c.align || "right",
                        color: c.format === "ticker" ? "var(--text)" : valueColor(r[c.key], c),
                        fontWeight: c.format === "ticker" ? 600 : 400,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {fmtValue(r[c.key], c)}
                      {c.format === "ticker" && r.signal && (
                        <span style={{ marginLeft: 8, fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(52,192,133,0.15)", color: "var(--good)" }}>
                          SINYAL
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 10 }}>
        Klik judul kolom untuk mengurutkan · klik baris untuk analisis detail · kolom bertanda
        <span style={{ color: "var(--accent)" }}> · </span>punya penjelasan saat disorot
      </div>
    </div>
  );
}
