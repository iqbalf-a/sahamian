export default function SectionTitle({ children, note }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", margin: "28px 0 12px" }}>
      <h2 style={{ fontSize: 15, fontWeight: 600, margin: 0, color: "var(--text)" }}>{children}</h2>
      {note && <span style={{ fontSize: 12, color: "var(--text-faint)" }}>{note}</span>}
    </div>
  );
}
