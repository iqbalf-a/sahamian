import { useMemo, useState } from "react";

const COLS = [
  { key: "ticker", label: "Ticker", align: "left" },
  { key: "avg_daily_value_bn", label: "Nilai transaksi/hari (Rp M)", align: "right" },
  { key: "daily_vol_pct", label: "Volatilitas harian", align: "right" },
  { key: "avg_monthly_move_pct", label: "Pergerakan bulanan rata²", align: "right" },
];

export default function UniverseTable({ rows }) {
  const [sortKey, setSortKey] = useState("avg_daily_value_bn");
  const [asc, setAsc] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => (a[sortKey] > b[sortKey] ? 1 : -1) * (asc ? 1 : -1));
    return copy;
  }, [rows, sortKey, asc]);

  const onSort = (key) => {
    if (key === sortKey) setAsc(!asc);
    else {
      setSortKey(key);
      setAsc(false);
    }
  };

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 12 }}>
        Statistik dasar universe LQ45 &middot; periode eksplorasi 2019–2023 &middot; {rows.length} saham
      </div>
      <div className="scrollbar-thin" style={{ maxHeight: 380, overflowY: "auto" }}>
        <table style={{ fontSize: 13 }}>
          <thead style={{ position: "sticky", top: 0, background: "var(--panel)" }}>
            <tr style={{ color: "var(--text-faint)", fontSize: 11, textTransform: "uppercase" }}>
              {COLS.map((c) => (
                <td
                  key={c.key}
                  onClick={() => onSort(c.key)}
                  style={{ padding: "6px 10px 6px 0", textAlign: c.align, cursor: "pointer", userSelect: "none" }}
                >
                  {c.label}{sortKey === c.key ? (asc ? " ▲" : " ▼") : ""}
                </td>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.ticker} style={{ borderTop: "1px solid var(--border)" }}>
                <td className="mono" style={{ padding: "6px 10px 6px 0", fontWeight: 600 }}>{r.ticker}</td>
                <td className="mono" style={{ padding: "6px 10px 6px 0", textAlign: "right" }}>{r.avg_daily_value_bn.toFixed(1)}</td>
                <td className="mono" style={{ padding: "6px 10px 6px 0", textAlign: "right" }}>{r.daily_vol_pct.toFixed(2)}%</td>
                <td className="mono" style={{ padding: "6px 0", textAlign: "right" }}>{r.avg_monthly_move_pct.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
