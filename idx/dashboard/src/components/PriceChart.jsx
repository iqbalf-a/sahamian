import { ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const UP = "#34c085";
const DOWN = "#e5584f";

/** Lilin digambar sendiri: Recharts tidak punya candlestick bawaan.
 *  Bar memakai rentang [low, high], sehingga y = harga tertinggi dan y+height = terendah;
 *  posisi open/close diinterpolasi dari rentang itu. */
function Candle(props) {
  const { x, y, width, height, payload } = props;
  const { open, close, high, low } = payload;
  if ([open, close, high, low].some((v) => v == null)) return null;

  const span = high - low;
  const toY = (v) => (span === 0 ? y : y + ((high - v) / span) * height);
  const up = close >= open;
  const color = up ? UP : DOWN;
  const bodyTop = toY(Math.max(open, close));
  const bodyH = Math.max(Math.abs(toY(close) - toY(open)), 1);
  const cx = x + width / 2;
  const bodyW = Math.max(width * 0.62, 1);

  return (
    <g>
      <line x1={cx} x2={cx} y1={y} y2={y + height} stroke={color} strokeWidth={1} />
      <rect x={cx - bodyW / 2} y={bodyTop} width={bodyW} height={bodyH} fill={up ? "none" : color} stroke={color} strokeWidth={1} />
    </g>
  );
}

export default function PriceChart({ series, mode = "line", height = 300, showMa = true }) {
  const data = series.map((d) => ({ ...d, range: [d.low, d.high] }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="date" tick={{ fill: "var(--text-faint)", fontSize: 10 }} tickLine={false}
          axisLine={{ stroke: "var(--border)" }} minTickGap={60} />
        <YAxis domain={["auto", "auto"]} tick={{ fill: "var(--text-faint)", fontSize: 10 }} tickLine={false}
          axisLine={false} width={58} tickFormatter={(v) => v.toLocaleString("id-ID")} />
        <Tooltip
          contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "var(--text-dim)" }}
          formatter={(v, n) => {
            if (n === "range" || v == null) return [null, null];
            return [Array.isArray(v) ? null : v.toLocaleString("id-ID"), n];
          }}
        />
        {mode === "candle"
          ? <Bar dataKey="range" shape={<Candle />} isAnimationActive={false} name="OHLC" />
          : <Line type="monotone" dataKey="close" name="Harga" stroke="#e6e9f0" strokeWidth={1.8} dot={false} />}
        {showMa && <>
          <Line type="monotone" dataKey="sma20" name="SMA20" stroke="#4f8cff" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="sma50" name="SMA50" stroke="#e0a83e" strokeWidth={1} dot={false} />
          <Line type="monotone" dataKey="sma200" name="SMA200" stroke="#e5584f" strokeWidth={1} dot={false} />
        </>}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
