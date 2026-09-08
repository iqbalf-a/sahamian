import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function YearlyChart({ yearly }) {
  return (
    <div className="two-col">
      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: "16px 8px 8px" }}>
        <div style={{ padding: "0 12px 8px", fontSize: 12, color: "var(--text-dim)" }}>Net P&amp;L per tahun (IDR)</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={yearly} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: "var(--text-faint)", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
            <YAxis tickFormatter={(v) => `${(v / 1e6).toFixed(0)}jt`} tick={{ fill: "var(--text-faint)", fontSize: 11 }} tickLine={false} axisLine={false} width={44} />
            <Tooltip
              contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
              formatter={(v) => [`Rp${(v / 1e6).toFixed(1)}jt`, "Net"]}
            />
            <Bar dataKey="net" radius={[4, 4, 0, 0]}>
              {yearly.map((y, i) => (
                <Cell key={i} fill={y.net >= 0 ? "var(--good)" : "var(--bad)"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16, overflowX: "auto" }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>Detail per tahun</div>
        <table style={{ fontSize: 13 }}>
          <thead>
            <tr style={{ color: "var(--text-faint)", fontSize: 11, textTransform: "uppercase" }}>
              <td style={{ padding: "4px 8px 4px 0" }}>Tahun</td>
              <td style={{ padding: "4px 8px", textAlign: "right" }}>PF</td>
              <td style={{ padding: "4px 8px", textAlign: "right" }}>Win rate</td>
              <td style={{ padding: "4px 0", textAlign: "right" }}>Net</td>
            </tr>
          </thead>
          <tbody>
            {yearly.map((y) => (
              <tr key={y.year} style={{ borderTop: "1px solid var(--border)" }}>
                <td className="mono" style={{ padding: "6px 8px 6px 0" }}>{y.year}</td>
                <td className="mono" style={{ padding: "6px 8px", textAlign: "right" }}>{y.pf?.toFixed(2) ?? "—"}</td>
                <td className="mono" style={{ padding: "6px 8px", textAlign: "right" }}>{y.win_rate.toFixed(0)}%</td>
                <td className="mono" style={{ padding: "6px 0", textAlign: "right", color: y.net >= 0 ? "var(--good)" : "var(--bad)" }}>
                  {y.net >= 0 ? "+" : ""}
                  {(y.net / 1e6).toFixed(1)}jt
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
