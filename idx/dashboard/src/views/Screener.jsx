import { useEffect, useState } from "react";
import MomentumScreener from "./screeners/MomentumScreener";
import GenericScreener from "./screeners/GenericScreener";

const STATUS_STYLE = {
  "tervalidasi sebagian": { color: "var(--good)", bg: "rgba(52,192,133,0.12)" },
  "gagal: backtest": { color: "var(--bad)", bg: "rgba(229,88,79,0.12)" },
  "gagal: biaya": { color: "var(--bad)", bg: "rgba(229,88,79,0.12)" },
  "gagal: sinyal": { color: "var(--bad)", bg: "rgba(229,88,79,0.12)" },
  "belum diuji": { color: "var(--text-faint)", bg: "var(--panel-2)" },
};

export default function Screener({ onSelect }) {
  const [templates, setTemplates] = useState([]);
  const [active, setActive] = useState("momentum");

  useEffect(() => {
    fetch("/api/screen/templates")
      .then((r) => r.json())
      .then((d) => setTemplates(d.templates))
      .catch(() => setTemplates([]));
  }, []);

  const current = templates.find((t) => t.id === active);

  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 6 }}>
        {templates.map((t) => {
          const on = t.id === active;
          const st = STATUS_STYLE[t.status] || STATUS_STYLE["belum diuji"];
          return (
            <button
              key={t.id}
              onClick={() => setActive(t.id)}
              style={{
                background: on ? "var(--panel)" : "transparent",
                border: `1px solid ${on ? "var(--accent)" : "var(--border)"}`,
                borderRadius: 8, padding: "8px 12px", cursor: "pointer", textAlign: "left",
                color: "var(--text)", minWidth: 150,
              }}
            >
              <div style={{ fontSize: 13, fontWeight: on ? 600 : 400 }}>{t.name}</div>
              <div style={{ fontSize: 10, color: "var(--text-faint)", marginTop: 2 }}>{t.tagline}</div>
              <span style={{ display: "inline-block", marginTop: 6, fontSize: 9, padding: "1px 6px", borderRadius: 4, background: st.bg, color: st.color, textTransform: "uppercase", letterSpacing: 0.3 }}>
                {t.status}
              </span>
            </button>
          );
        })}
      </div>

      <div style={{ fontSize: 11, color: "var(--text-faint)", margin: "10px 0 14px", lineHeight: 1.6 }}>
        Semua template sudah diuji (eksperimen 001–003). Hanya{" "}
        <span style={{ color: "var(--good)" }}>momentum</span> yang mengalahkan buy&amp;hold — sisanya
        gagal, dan sengaja tetap ditampilkan supaya Anda bisa melihat sendiri bahwa layar yang
        kelihatan meyakinkan belum tentu menghasilkan uang.
      </div>

      {current?.evidence && (
        <div style={{
          background: current.id === "momentum" ? "rgba(52,192,133,0.07)" : "rgba(229,88,79,0.07)",
          border: `1px solid ${current.id === "momentum" ? "rgba(52,192,133,0.3)" : "rgba(229,88,79,0.3)"}`,
          borderRadius: 10, padding: "11px 14px", marginBottom: 16, fontSize: 12,
          color: "var(--text-dim)", lineHeight: 1.6,
        }}>
          <b style={{ color: current.id === "momentum" ? "var(--good)" : "var(--bad)" }}>
            Hasil uji:
          </b>{" "}
          {current.evidence}
        </div>
      )}

      {active === "momentum"
        ? <MomentumScreener onSelect={onSelect} />
        : <GenericScreener key={active} templateId={active} onSelect={onSelect} />}

      {current && current.id !== "momentum" && (
        <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 14 }}>
          Universe: 44 saham LQ45 yang dikunci di SETUP.md. Saham yang Anda tambahkan sendiri tidak
          ikut di sini — hanya template momentum yang punya kotak pencarian.
        </div>
      )}
    </div>
  );
}
