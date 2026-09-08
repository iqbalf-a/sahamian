const pct = (v, d = 1) => (v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(d)}%`);

/** Kalimat ringkasan disusun dari fakta yang ada di data — bukan prediksi.
 *  Eksperimen 003 menunjukkan indikator teknikal (SMA, RSI, volume) tidak memprediksi
 *  return, jadi panel ini hanya menggambarkan keadaan sekarang. */
function narrative(stats, strategy, name) {
  const parts = [];

  if (stats.above_sma200 && stats.above_sma50) parts.push("berada di atas SMA50 dan SMA200");
  else if (stats.above_sma200) parts.push("masih di atas SMA200 tapi sudah turun di bawah SMA50");
  else if (stats.above_sma50) parts.push("di atas SMA50 tapi masih di bawah SMA200");
  else parts.push("berada di bawah SMA50 dan SMA200");

  const m = strategy?.momentum_pct;
  if (m != null) {
    parts.push(`momentum ${strategy.lookback ?? 6} bulan ${pct(m)}`);
  }

  if (stats.rsi >= 70) parts.push(`RSI ${stats.rsi} (overbought)`);
  else if (stats.rsi <= 30) parts.push(`RSI ${stats.rsi} (oversold)`);
  else parts.push(`RSI ${stats.rsi} (netral)`);

  const liq = stats.avg_value_bn;
  if (liq != null) {
    parts.push(liq >= 50 ? "likuiditas tebal"
      : liq >= 10 ? "likuiditas memadai"
      : "likuiditas tipis — slippage bisa jauh lebih besar dari asumsi");
  }

  return `${name || "Saham ini"} ${parts.join(", ")}.`;
}

// harga saham IDX selalu bulat; desimal pada low/high adalah artefak penyesuaian dividen
const rp = (v) => (v == null ? "—" : Math.round(v).toLocaleString("id-ID"));

function RangeBar({ low, high, price, position }) {
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--text-faint)", marginBottom: 5 }}>
        <span className="mono">{rp(low)}</span>
        <span>rentang 52 minggu</span>
        <span className="mono">{rp(high)}</span>
      </div>
      <div style={{ position: "relative", height: 8, background: "var(--panel-2)", borderRadius: 4 }}>
        <div style={{
          position: "absolute", left: `${Math.min(Math.max(position ?? 0, 0), 100)}%`,
          top: -4, width: 3, height: 16, background: "var(--accent)", borderRadius: 2,
          transform: "translateX(-1.5px)",
        }} />
      </div>
      <div style={{ fontSize: 10, color: "var(--text-faint)", marginTop: 5, textAlign: "center" }}>
        Harga sekarang <span className="mono" style={{ color: "var(--text)" }}>{rp(price)}</span>
        {" "}— di posisi <span className="mono" style={{ color: "var(--text)" }}>{position?.toFixed(0)}%</span> dari rentang setahun
      </div>
    </div>
  );
}

export default function StockSummary({ data }) {
  const { stats, strategy, price, name, ticker } = data;

  const strategyLine = !strategy ? null
    : strategy.selected ? {
        color: "var(--good)", bg: "rgba(52,192,133,0.1)", border: "rgba(52,192,133,0.35)",
        text: `Masuk ${strategy.top_n} besar momentum LQ45 (peringkat ${strategy.rank} dari ${strategy.universe_size}) — saat ini termasuk yang akan dipegang strategi momentum.`,
      }
    : strategy.in_universe ? {
        color: "var(--text-dim)", bg: "var(--panel-2)", border: "var(--border)",
        text: `Peringkat momentum ${strategy.rank} dari ${strategy.universe_size} di LQ45 — di luar ${strategy.top_n} besar, jadi tidak dipegang strategi momentum.`,
      }
    : {
        color: "var(--text-dim)", bg: "var(--panel-2)", border: "var(--border)",
        text: `Di luar universe LQ45 yang dipakai riset. Seandainya ikut diperingkat, momentumnya ada di posisi ~${strategy.rank} dari ${strategy.universe_size} — angka pembanding saja, bukan sinyal.`,
      };

  const facts = [
    ["1 bulan", pct(stats.ret_1m_pct)],
    ["3 bulan", pct(stats.ret_3m_pct)],
    ["12 bulan", pct(stats.ret_12m_pct)],
    ["Volatilitas harian", `${stats.volatility_pct}%`],
    ["Nilai transaksi", `Rp${stats.avg_value_bn?.toFixed(1)} M`],
    ["Harga 1 lot", `Rp${stats.lot_price?.toLocaleString("id-ID")}`],
  ];

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16, marginBottom: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>Ringkasan {ticker}</div>

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.5fr) minmax(0, 1fr)", gap: 20, alignItems: "start" }} className="summary-grid">
        <div>
          <p style={{ margin: "0 0 12px", fontSize: 13, lineHeight: 1.7, color: "var(--text)" }}>
            {narrative(stats, strategy, name)}
          </p>

          {strategyLine && (
            <div style={{
              background: strategyLine.bg, border: `1px solid ${strategyLine.border}`,
              borderRadius: 8, padding: "9px 12px", fontSize: 12, color: strategyLine.color, lineHeight: 1.6,
            }}>
              {strategyLine.text}
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(96px, 1fr))", gap: 8, marginTop: 12 }}>
            {facts.map(([label, val]) => (
              <div key={label}>
                <div style={{ fontSize: 10, color: "var(--text-faint)" }}>{label}</div>
                <div className="mono" style={{ fontSize: 13, color: "var(--text)" }}>{val}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: "var(--panel-2)", borderRadius: 8, padding: "14px 14px 12px" }}>
          <RangeBar
            low={stats.low_52w}
            high={stats.high_52w}
            price={price}
            position={stats.range_position_pct}
          />
          <div style={{ borderTop: "1px solid var(--border)", marginTop: 12, paddingTop: 10, fontSize: 10, color: "var(--text-faint)", lineHeight: 1.6 }}>
            Panel ini menggambarkan keadaan sekarang, bukan ramalan. Dari tujuh template yang
            diuji, hanya momentum yang terbukti mengalahkan buy&amp;hold — SMA, RSI, dan volume
            tidak terbukti memprediksi return (eksperimen 003).
          </div>
        </div>
      </div>
    </div>
  );
}
