import { useEffect, useRef, useState } from "react";

const fmtTanggal = (iso) => {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  const bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
  return `${Number(d)} ${bulan[Number(m) - 1]} ${y}`;
};

export default function DataFreshness({ onUpdated }) {
  const [fresh, setFresh] = useState(null);
  const [job, setJob] = useState(null);
  const [dismissed, setDismissed] = useState(false);
  const poll = useRef(null);

  const load = () =>
    fetch("/api/data/freshness").then((r) => r.json()).then(setFresh).catch(() => {});

  useEffect(() => {
    load();
    return () => clearInterval(poll.current);
  }, []);

  const mulai = async () => {
    const r = await fetch("/api/data/update", { method: "POST" }).then((x) => x.json());
    setJob(r);
    clearInterval(poll.current);
    poll.current = setInterval(async () => {
      const s = await fetch("/api/data/update/status").then((x) => x.json());
      setJob(s);
      if (!s.running) {
        clearInterval(poll.current);
        setFresh(s.freshness);
        onUpdated?.();
      }
    }, 1200);
  };

  if (!fresh) return null;

  const sedangJalan = job?.running;
  const baruSelesai = job && !job.running && job.finished_at;

  // tidak ada yang perlu diberitahu: data segar, tidak sedang update, tidak baru selesai
  if (!fresh.stale && !sedangJalan && !baruSelesai) return null;
  if (dismissed && !sedangJalan) return null;

  const persen = job?.total ? Math.round((job.done / job.total) * 100) : 0;

  const nada = sedangJalan
    ? { bg: "rgba(79,140,255,0.09)", border: "rgba(79,140,255,0.4)", warna: "var(--accent)" }
    : baruSelesai
      ? { bg: "rgba(52,192,133,0.09)", border: "rgba(52,192,133,0.4)", warna: "var(--good)" }
      : { bg: "rgba(224,168,62,0.09)", border: "rgba(224,168,62,0.4)", warna: "var(--warn)" };

  return (
    <div style={{
      background: nada.bg, border: `1px solid ${nada.border}`, borderRadius: 10,
      padding: "12px 16px", marginBottom: 16,
      display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap",
    }}>
      {sedangJalan ? (
        <>
          <span style={{ fontSize: 13, color: nada.warna, fontWeight: 600 }}>
            Memperbarui data…
          </span>
          <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
            {job.done} dari {job.total}
            {job.current && <span className="mono"> · {job.current}</span>}
          </span>
          <div style={{ flex: "1 1 140px", minWidth: 120, height: 6, background: "var(--panel-2)", borderRadius: 3, overflow: "hidden" }}>
            <div style={{ width: `${persen}%`, height: "100%", background: "var(--accent)", transition: "width .4s" }} />
          </div>
          <span className="mono" style={{ fontSize: 12, color: "var(--text-dim)" }}>{persen}%</span>
        </>
      ) : baruSelesai ? (
        <>
          <span style={{ fontSize: 13, color: nada.warna, fontWeight: 600 }}>Data diperbarui</span>
          <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
            {job.updated} berkas disegarkan · data terakhir{" "}
            <span className="mono">{fmtTanggal(fresh.last_date)}</span>
          </span>
          <button onClick={() => window.location.reload()} style={tombolUtama}>
            Muat ulang tampilan
          </button>
          <button onClick={() => setJob(null)} style={tombolSekunder}>Tutup</button>
        </>
      ) : (
        <>
          <span style={{ fontSize: 13, color: nada.warna, fontWeight: 600 }}>
            Data yang tampil bukan yang terbaru
          </span>
          <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
            Data terakhir <span className="mono">{fmtTanggal(fresh.last_date)}</span>
            {fresh.calendar_days_ago > 0 && ` (${fresh.calendar_days_ago} hari lalu)`}
            {fresh.trading_days_behind > 0 && ` — tertinggal ${fresh.trading_days_behind} hari bursa`}
          </span>
          <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
            <button onClick={mulai} style={tombolUtama}>Perbarui sekarang</button>
            <button onClick={() => setDismissed(true)} style={tombolSekunder}>Nanti saja</button>
          </div>
        </>
      )}
    </div>
  );
}

const tombolUtama = {
  background: "var(--accent)", border: "none", borderRadius: 7,
  padding: "7px 14px", color: "#fff", fontSize: 12, fontWeight: 600, cursor: "pointer",
  whiteSpace: "nowrap",
};

const tombolSekunder = {
  background: "transparent", border: "1px solid var(--border)", borderRadius: 7,
  padding: "7px 12px", color: "var(--text-dim)", fontSize: 12, cursor: "pointer",
  whiteSpace: "nowrap",
};
