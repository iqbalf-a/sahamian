import { useMemo, useState } from "react";

export const fmtValue = (v, col) => {
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
    case "text":
    case "ticker":
      return v;
    default:
      return typeof v === "number" ? v.toFixed(col.digits ?? 2) : v;
  }
};

export const valueColor = (v, col) => {
  if (v == null) return "var(--text-faint)";
  if (col.format === "bool") return v ? "var(--good)" : "var(--bad)";
  if (col.format === "text") return "var(--text-dim)";
  if (!col.good) return "var(--text)";
  if (col.good === "high") return v > 0 ? "var(--good)" : v < 0 ? "var(--bad)" : "var(--text-dim)";
  return "var(--text-dim)";
};

export default function DataTable({ columns, rows, onRowClick, maxHeight = 560, defaultSort = null, emptyText }) {
  const [sort, setSort] = useState(defaultSort);

  const sorted = useMemo(() => {
    if (!sort) return rows;
    return [...rows].sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key];
      if (av == null) return 1;
      if (bv == null) return -1;
      return (av > bv ? 1 : av < bv ? -1 : 0) * (sort.asc ? 1 : -1);
    });
  }, [rows, sort]);

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden" }}>
      <div className="scrollbar-thin" style={{ maxHeight, overflow: "auto" }}>
        <table style={{ fontSize: 13 }}>
          <thead style={{ position: "sticky", top: 0, background: "var(--panel)", zIndex: 1 }}>
            <tr style={{ color: "var(--text-faint)", fontSize: 10, textTransform: "uppercase" }}>
              {columns.map((c) => (
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
            {sorted.length === 0 && (
              <tr><td colSpan={columns.length} style={{ padding: 24, textAlign: "center", color: "var(--text-faint)" }}>
                {emptyText || "Tidak ada data"}
              </td></tr>
            )}
            {sorted.map((r) => (
              <tr
                key={r.ticker}
                onClick={() => onRowClick?.(r.ticker)}
                style={{
                  borderTop: "1px solid var(--border)",
                  cursor: onRowClick ? "pointer" : "default",
                  background: r.signal ? "rgba(79,140,255,0.06)" : "transparent",
                }}
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={c.format === "text" ? "" : "mono"}
                    style={{
                      padding: "8px 10px", textAlign: c.align || "right",
                      color: c.format === "ticker" ? "var(--text)" : valueColor(r[c.key], c),
                      fontWeight: c.format === "ticker" ? 600 : 400,
                      whiteSpace: "nowrap",
                      maxWidth: c.format === "text" ? 220 : undefined,
                      overflow: c.format === "text" ? "hidden" : undefined,
                      textOverflow: c.format === "text" ? "ellipsis" : undefined,
                      fontSize: c.format === "text" ? 12 : undefined,
                    }}
                  >
                    {fmtValue(r[c.key], c)}
                    {c.format === "ticker" && r.signal && (
                      <span style={{ marginLeft: 8, fontSize: 10, padding: "1px 6px", borderRadius: 4, background: "rgba(52,192,133,0.15)", color: "var(--good)" }}>
                        SINYAL
                      </span>
                    )}
                    {c.format === "ticker" && r.in_universe === false && (
                      <span style={{ marginLeft: 6, fontSize: 9, color: "var(--text-faint)" }}>·</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
