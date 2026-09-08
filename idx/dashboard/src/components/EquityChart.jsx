import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, ComposedChart } from "recharts";

const fmtRp = (v) => `Rp${(v / 1e6).toFixed(0)}jt`;

export default function EquityChart({ equity }) {
  const rows = equity.dates.map((d, i) => ({
    date: d,
    strategi: equity.strategy[i],
    benchmark: equity.benchmark[i],
  }));

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: "16px 8px 8px" }}>
      <div style={{ display: "flex", gap: 16, padding: "0 12px 8px", fontSize: 12, color: "var(--text-dim)" }}>
        <span><span style={{ display: "inline-block", width: 10, height: 2, background: "var(--accent)", marginRight: 6, verticalAlign: "middle" }} />Strategi momentum</span>
        <span><span style={{ display: "inline-block", width: 10, height: 2, background: "var(--bench)", marginRight: 6, verticalAlign: "middle", borderTop: "1px dashed var(--bench)" }} />Equal-weight buy&amp;hold (tanpa biaya)</span>
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="stratFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4f8cff" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#4f8cff" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--border)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "var(--text-faint)", fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
            interval={5}
          />
          <YAxis
            tickFormatter={(v) => `${(v / 1e6).toFixed(0)}jt`}
            tick={{ fill: "var(--text-faint)", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip
            contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "var(--text-dim)" }}
            formatter={(v, name) => [fmtRp(v), name === "strategi" ? "Strategi momentum" : "Buy&hold"]}
          />
          <Area type="monotone" dataKey="strategi" stroke="var(--accent)" strokeWidth={2} fill="url(#stratFill)" dot={false} />
          <Line type="monotone" dataKey="benchmark" stroke="var(--bench)" strokeWidth={1.5} strokeDasharray="5 4" dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
