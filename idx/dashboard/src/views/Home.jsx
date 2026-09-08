import { useEffect, useState } from "react";
import DataTable from "../components/DataTable";
import Briefing from "../components/Briefing";

export default function Home({ onSelect }) {
  const [tabs, setTabs] = useState([]);
  const [active, setActive] = useState("gainer");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/home/tabs").then((r) => r.json()).then((d) => setTabs(d.tabs)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/home?tab=${active}&limit=30`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [active]);

  const idx = data?.index;

  return (
    <div>
      {idx && (
        <div style={{ display: "flex", alignItems: "baseline", gap: 14, flexWrap: "wrap", marginBottom: 18 }}>
          <span style={{ fontSize: 13, color: "var(--text-dim)" }}>IHSG</span>
          <span className="mono" style={{ fontSize: 26, fontWeight: 600 }}>
            {idx.value.toLocaleString("id-ID")}
          </span>
          <span
            className="mono"
            style={{ fontSize: 15, color: idx.change_pct >= 0 ? "var(--good)" : "var(--bad)" }}
          >
            {idx.change_pct > 0 ? "+" : ""}{idx.change_pct}%
          </span>
          <span style={{ fontSize: 11, color: "var(--text-faint)", marginLeft: "auto" }}>
            data s/d {idx.last_date} · {data.total_tickers} saham
          </span>
        </div>
      )}

      <Briefing onSelect={onSelect} />

      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 12 }}>
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            style={{
              background: active === t.id ? "var(--accent-dim)" : "transparent",
              border: `1px solid ${active === t.id ? "var(--accent)" : "var(--border)"}`,
              color: active === t.id ? "var(--text)" : "var(--text-dim)",
              borderRadius: 7, padding: "6px 13px", fontSize: 13, cursor: "pointer",
            }}
          >
            {t.name}
          </button>
        ))}
      </div>

      {data?.note && (
        <div style={{ fontSize: 11, color: "var(--text-faint)", marginBottom: 14, lineHeight: 1.6 }}>
          {data.note}
        </div>
      )}

      {loading || !data ? (
        <div style={{ color: "var(--text-faint)", padding: 40 }}>Memuat…</div>
      ) : (
        <DataTable
          columns={data.columns}
          rows={data.rows}
          onRowClick={onSelect}
          emptyText="Tidak ada saham"
        />
      )}

      <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 10, lineHeight: 1.6 }}>
        Klik baris untuk membuka analisis detail. Daftar dihitung dari {data?.total_tickers ?? "—"} saham
        yang datanya ada di aplikasi (LQ45 + IDX80), bukan seluruh ~900 emiten IDX — jadi ini bukan
        top gainer bursa sesungguhnya. Cari emiten lain lewat kotak pencarian di kanan atas.
      </div>
    </div>
  );
}
