const VERDICT_STYLE = {
  aman: { label: "Aman (<5%)", color: "var(--good)" },
  berat: { label: "Berat (5–15%)", color: "var(--warn)" },
  tidak_layak: { label: "Tidak layak (>15%)", color: "var(--bad)" },
};

export default function CostTable({ costTable }) {
  const max = Math.max(...costTable.map((r) => r.ratio_pct));
  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 14 }}>
        Rasio biaya vs target profit &middot; biaya bolak-balik 0,50% (beli 0,20% + jual 0,30%)
      </div>
      {costTable.map((r) => {
        const v = VERDICT_STYLE[r.verdict];
        return (
          <div key={r.target_pct} style={{ display: "grid", gridTemplateColumns: "56px 1fr 90px 140px", alignItems: "center", gap: 12, marginBottom: 8 }}>
            <span className="mono" style={{ fontSize: 13, color: "var(--text)" }}>{r.target_pct}%</span>
            <div style={{ position: "relative", height: 8, background: "var(--panel-2)", borderRadius: 4 }}>
              <div style={{ position: "absolute", inset: 0, width: `${Math.min(100, (r.ratio_pct / max) * 100)}%`, background: v.color, borderRadius: 4, opacity: 0.7 }} />
            </div>
            <span className="mono" style={{ fontSize: 13, textAlign: "right", color: "var(--text-dim)" }}>{r.ratio_pct}%</span>
            <span style={{ fontSize: 12, color: v.color, textAlign: "right" }}>{v.label}</span>
          </div>
        );
      })}
      <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 10 }}>
        Target profit ≥15% dibutuhkan agar rasio biaya di bawah 5% — mengunci desain ke
        swing/position trading, bukan day trading.
      </div>
    </div>
  );
}
