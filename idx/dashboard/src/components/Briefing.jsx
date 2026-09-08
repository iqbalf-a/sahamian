import { useEffect, useState } from "react";

export default function Briefing({ onSelect }) {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(true);
  const [ai, setAi] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    fetch("/api/briefing").then((r) => r.json()).then(setData).catch(() => setData(null));
  }, []);

  const runAi = async () => {
    setAiLoading(true);
    try {
      const r = await fetch("/api/briefing/ai", { method: "POST" });
      setAi(await r.json());
    } catch (e) {
      setAi({ available: false, reason: String(e) });
    } finally {
      setAiLoading(false);
    }
  };

  if (!data) return null;
  const { movers, linked, headlines, ai_available } = data;

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16, marginBottom: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: open ? 14 : 0 }}>
        <span style={{ fontSize: 13, fontWeight: 600 }}>Pergerakan tidak wajar hari ini</span>
        <span style={{ fontSize: 11, color: "var(--text-faint)" }}>
          {movers.length} saham menyimpang &gt;2 simpangan baku dari volatilitas normalnya
        </span>
        <button
          onClick={() => setOpen(!open)}
          style={{ marginLeft: "auto", background: "transparent", border: "1px solid var(--border)", color: "var(--text-dim)", borderRadius: 6, padding: "3px 10px", fontSize: 11, cursor: "pointer" }}
        >
          {open ? "Sembunyikan" : "Tampilkan"}
        </button>
      </div>

      {open && (
        <>
          {movers.length === 0 && (
            <div style={{ fontSize: 12, color: "var(--text-faint)" }}>
              Tidak ada saham yang bergerak di luar kebiasaannya hari ini.
            </div>
          )}

          {movers.map((m) => (
            <div key={m.ticker} style={{ borderTop: "1px solid var(--border)", padding: "10px 0" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                <button
                  onClick={() => onSelect(m.ticker)}
                  className="mono"
                  style={{ background: "transparent", border: "none", color: "var(--text)", fontWeight: 600, fontSize: 14, cursor: "pointer", padding: 0 }}
                >
                  {m.ticker}
                </button>
                <span className="mono" style={{ fontSize: 14, color: m.change_pct >= 0 ? "var(--good)" : "var(--bad)" }}>
                  {m.change_pct > 0 ? "+" : ""}{m.change_pct}%
                </span>
                <span style={{ fontSize: 11, color: "var(--text-faint)" }}>
                  z-score {m.z_score > 0 ? "+" : ""}{m.z_score} · volume {m.volume_ratio}× rata-rata
                </span>
                <span style={{ fontSize: 11, color: "var(--text-dim)", marginLeft: "auto" }}>{m.name}</span>
              </div>

              {linked[m.ticker] ? (
                <div style={{ marginTop: 6, paddingLeft: 2 }}>
                  {linked[m.ticker].map((h) => (
                    <div key={h.title} style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 3 }}>
                      <span style={{ color: "var(--text-faint)" }}>[{h.source}]</span>{" "}
                      {h.link ? <a href={h.link} target="_blank" rel="noreferrer" style={{ color: "var(--accent)", textDecoration: "none" }}>{h.title}</a> : h.title}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ marginTop: 6, fontSize: 11, color: "var(--text-faint)" }}>
                  Tidak ada judul berita di feed yang menyebut saham ini — bukan berarti tidak ada
                  sebabnya, hanya belum tertangkap sumber berita aplikasi.
                </div>
              )}
            </div>
          ))}

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 4 }}>
            {ai_available ? (
              <button
                onClick={runAi}
                disabled={aiLoading}
                style={{ background: "var(--accent)", border: "none", borderRadius: 8, padding: "7px 14px", color: "#fff", fontSize: 12, cursor: aiLoading ? "wait" : "pointer" }}
              >
                {aiLoading ? "Menganalisis…" : "Analisis dengan AI"}
              </button>
            ) : (
              <div style={{ fontSize: 11, color: "var(--text-faint)", lineHeight: 1.7 }}>
                <b style={{ color: "var(--warn)" }}>Analisis AI belum aktif.</b> Set{" "}
                <span className="mono">ANTHROPIC_API_KEY</span> di environment lalu jalankan ulang
                server API. Sampai itu dilakukan, panel ini hanya menampilkan pergerakan statistik
                dan judul berita apa adanya — sengaja tidak menebak sebab, karena menebak alasan
                saham naik adalah cara cepat membuat orang salah ambil keputusan.
              </div>
            )}

            {ai?.analysis && (
              <div style={{ marginTop: 12, fontSize: 12, color: "var(--text-dim)", lineHeight: 1.75, whiteSpace: "pre-wrap" }}>
                {ai.analysis}
                <div style={{ fontSize: 10, color: "var(--text-faint)", marginTop: 8 }}>
                  Dihasilkan {ai.model} dari {headlines.length} judul berita di atas saja.
                </div>
              </div>
            )}
            {ai && ai.available === false && ai.reason && (
              <div style={{ marginTop: 10, fontSize: 11, color: "var(--warn)" }}>{ai.reason}</div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
