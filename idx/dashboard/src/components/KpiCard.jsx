export default function KpiCard({ label, value, sub, tone = "neutral" }) {
  const toneColor = {
    good: "var(--good)",
    bad: "var(--bad)",
    warn: "var(--warn)",
    neutral: "var(--text)",
  }[tone];

  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        padding: "14px 16px",
        minWidth: 0,
      }}
    >
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 6 }}>{label}</div>
      <div className="mono" style={{ fontSize: 22, fontWeight: 600, color: toneColor }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 12, color: "var(--text-faint)", marginTop: 4 }}>{sub}</div>
      )}
    </div>
  );
}
