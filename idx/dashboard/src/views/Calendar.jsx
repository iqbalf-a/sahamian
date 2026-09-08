import { useEffect, useMemo, useState } from "react";
import TickerSearch from "../components/TickerSearch";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];
const DOW = ["Sen", "Sel", "Rab", "Kam", "Jum"];

function shade(v, scale) {
  if (v == null) return "transparent";
  const t = Math.min(Math.abs(v) / scale, 1);
  const alpha = (0.12 + t * 0.65).toFixed(3);
  return v >= 0 ? `rgba(52,192,133,${alpha})` : `rgba(229,88,79,${alpha})`;
}

const fmtChange = (v) => {
  const abs = Math.abs(v);
  const digits = abs >= 100 ? 0 : abs >= 10 ? 1 : 2;
  return `${v > 0 ? "+" : v < 0 ? "−" : ""}${abs.toLocaleString("id-ID", {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  })}`;
};

function MonthGrid({ month, days, scale }) {
  const cells = useMemo(() => {
    const byDate = new Map(days.map((d) => [d.date, d]));
    const year = days.length ? Number(days[0].date.slice(0, 4)) : new Date().getFullYear();
    const first = new Date(year, month - 1, 1);
    const last = new Date(year, month, 0);
    const out = [];
    // padding sampai hari Senin pertama (kolom = Senin..Jumat)
    let lead = (first.getDay() + 6) % 7;
    if (lead > 4) lead = 0;
    for (let i = 0; i < lead; i++) out.push(null);
    for (let d = 1; d <= last.getDate(); d++) {
      const dt = new Date(year, month - 1, d);
      const dow = dt.getDay();
      if (dow === 0 || dow === 6) continue;
      const key = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      out.push({ day: d, date: key, data: byDate.get(key) || null });
    }
    return out;
  }, [month, days]);

  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)", marginBottom: 8 }}>
        {MONTHS[month - 1]}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 4 }}>
        {DOW.map((d) => (
          <div key={d} style={{ fontSize: 10, color: "var(--text-faint)", textAlign: "center", paddingBottom: 2 }}>
            {d}
          </div>
        ))}
        {cells.map((c, i) => {
          const v = c?.data;
          return (
            <div
              key={i}
              title={c ? (v ? `${c.date} · tutup ${v.close.toLocaleString("id-ID")}` : `${c.date}: libur / tidak ada data`) : ""}
              style={{
                minHeight: 66, borderRadius: 6, padding: "6px 8px",
                background: c ? shade(v?.return_pct ?? null, scale) : "transparent",
                border: c && !v ? "1px dashed var(--border)" : "none",
                display: c ? "flex" : "block",
                flexDirection: "column", justifyContent: "space-between",
              }}
            >
              {c && (
                <>
                  <div style={{ fontSize: 10, color: v ? "rgba(255,255,255,0.55)" : "var(--text-faint)", lineHeight: 1 }}>
                    {c.day}
                  </div>
                  {v ? (
                    <div style={{ textAlign: "right", lineHeight: 1.25 }}>
                      {/* warna latar sudah menandai arah; teksnya netral supaya tetap terbaca
                          di sel yang pekat */}
                      <div className="mono" style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>
                        {v.return_pct > 0 ? "+" : ""}{v.return_pct}%
                      </div>
                      <div className="mono" style={{ fontSize: 11, color: "rgba(255,255,255,0.62)" }}>
                        {fmtChange(v.change)}
                      </div>
                    </div>
                  ) : (
                    <div style={{ fontSize: 9, color: "var(--text-faint)", textAlign: "right" }}>—</div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const pagerBtn = (disabled) => ({
  background: "transparent",
  border: "1px solid var(--border)",
  color: disabled ? "var(--text-faint)" : "var(--text)",
  borderRadius: 6, padding: "3px 11px", fontSize: 13,
  cursor: disabled ? "default" : "pointer",
  opacity: disabled ? 0.4 : 1,
});

export default function Calendar() {
  const [symbol, setSymbol] = useState("IHSG");
  const [year, setYear] = useState(null);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);   // 0 = Jan–Feb … 5 = Nov–Des

  useEffect(() => {
    setError(null);
    const q = year ? `&year=${year}` : "";
    fetch(`/api/calendar?symbol=${symbol}${q}`)
      .then((r) => (r.ok ? r.json() : r.json().then((b) => Promise.reject(new Error(b.detail)))))
      .then((d) => {
        setData(d);
        setYear(d.year);
        // buka di bulan terakhir yang ada datanya, bukan selalu Januari
        const last = d.days?.[d.days.length - 1]?.date;
        if (last) setPage(Math.floor((Number(last.slice(5, 7)) - 1) / 2));
      })
      .catch((e) => setError(e.message));
  }, [symbol, year]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "ArrowLeft") setPage((p) => Math.max(p - 1, 0));
      if (e.key === "ArrowRight") setPage((p) => Math.min(p + 1, 5));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const scale = useMemo(() => {
    if (!data?.days?.length) return 2;
    const abs = data.days.map((d) => Math.abs(d.return_pct)).sort((a, b) => a - b);
    return Math.max(abs[Math.floor(abs.length * 0.9)] || 2, 0.5);
  }, [data]);

  const s = data?.summary;

  return (
    <div>
      <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 18 }}>
        <div>
          <label style={{ display: "block", fontSize: 11, color: "var(--text-dim)", marginBottom: 5 }}>Instrumen</label>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              onClick={() => { setSymbol("IHSG"); setYear(null); }}
              style={{
                background: symbol === "IHSG" ? "var(--accent-dim)" : "transparent",
                border: `1px solid ${symbol === "IHSG" ? "var(--accent)" : "var(--border)"}`,
                color: "var(--text)", borderRadius: 7, padding: "7px 14px", fontSize: 13, cursor: "pointer",
              }}
            >
              IHSG
            </button>
            {symbol !== "IHSG" && (
              <span className="mono" style={{ border: "1px solid var(--accent)", background: "var(--accent-dim)", borderRadius: 7, padding: "7px 14px", fontSize: 13 }}>
                {symbol}
              </span>
            )}
          </div>
        </div>

        <div style={{ flex: "0 1 320px" }}>
          <label style={{ display: "block", fontSize: 11, color: "var(--text-dim)", marginBottom: 5 }}>Ganti ke saham</label>
          <TickerSearch onSelect={(t) => { setSymbol(t); setYear(null); }} />
        </div>

        {data?.years && (
          <div>
            <label style={{ display: "block", fontSize: 11, color: "var(--text-dim)", marginBottom: 5 }}>Tahun</label>
            <select
              value={year || ""}
              onChange={(e) => setYear(Number(e.target.value))}
              style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 10px", color: "var(--text)", fontSize: 13 }}
            >
              {data.years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
        )}
      </div>

      {error && <div style={{ color: "var(--bad)" }}>{error}</div>}

      {data && (
        <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: "14px 16px" }}>
          <div style={{
            display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap",
            paddingBottom: 12, marginBottom: 12, borderBottom: "1px solid var(--border)",
          }}>
            <span className="mono" style={{ fontSize: 17, fontWeight: 600 }}>{data.symbol}</span>
            {data.name && (
              <span style={{ fontSize: 13, color: "var(--text-dim)" }}>{data.name}</span>
            )}
            <span className="mono" style={{ fontSize: 17, marginLeft: "auto" }}>
              {data.is_index
                ? data.price?.toLocaleString("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                : Math.round(data.price).toLocaleString("id-ID")}
            </span>
            {data.price_change_pct != null && (
              <span className="mono" style={{ fontSize: 13, color: data.price_change_pct >= 0 ? "var(--good)" : "var(--bad)" }}>
                {data.price_change_pct > 0 ? "+" : ""}{data.price_change_pct}%
              </span>
            )}
            <span style={{ fontSize: 11, color: "var(--text-faint)" }}>per {data.price_date}</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
            <button onClick={() => setPage((p) => Math.max(p - 1, 0))} disabled={page === 0} style={pagerBtn(page === 0)}>←</button>
            <span className="mono" style={{ fontSize: 13, fontWeight: 600, minWidth: 108, textAlign: "center" }}>
              {MONTHS[page * 2]} – {MONTHS[page * 2 + 1]}
            </span>
            <button onClick={() => setPage((p) => Math.min(p + 1, 5))} disabled={page === 5} style={pagerBtn(page === 5)}>→</button>

            <div style={{ display: "flex", gap: 3, marginLeft: 8 }}>
              {[0, 1, 2, 3, 4, 5].map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  style={{
                    background: page === p ? "var(--accent-dim)" : "transparent",
                    border: `1px solid ${page === p ? "var(--accent)" : "var(--border)"}`,
                    color: page === p ? "var(--text)" : "var(--text-dim)",
                    borderRadius: 5, padding: "2px 8px", fontSize: 10, cursor: "pointer",
                  }}
                >
                  {MONTHS[p * 2].slice(0, 3)}
                </button>
              ))}
            </div>

            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 7, fontSize: 10, color: "var(--text-faint)" }}>
              <span>Rugi</span>
              {[-1, -0.55, -0.2, 0.2, 0.55, 1].map((t) => (
                <span key={t} style={{ width: 14, height: 10, borderRadius: 3, background: shade(t * scale, scale) }} />
              ))}
              <span>Untung</span>
              <span style={{ marginLeft: 6 }}>skala ±{scale.toFixed(1)}%</span>
            </div>
          </div>

          <div className="calendar-grid">
            <MonthGrid month={page * 2 + 1} days={data.days} scale={scale} />
            <MonthGrid month={page * 2 + 2} days={data.days} scale={scale} />
          </div>
        </div>
      )}

      {s && data?.monthly && (
        <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: "14px 16px", marginTop: 14 }}>
          <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "baseline", marginBottom: 12 }}>
            <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Ringkasan {data.year}</span>
            <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
              Return{" "}
              <span className="mono" style={{ fontSize: 15, fontWeight: 600, color: s.total_return_pct >= 0 ? "var(--good)" : "var(--bad)" }}>
                {s.total_return_pct > 0 ? "+" : ""}{s.total_return_pct}%
              </span>
            </span>
            <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
              Naik/turun <span className="mono" style={{ color: "var(--good)" }}>{s.up_days}</span>
              <span> / </span><span className="mono" style={{ color: "var(--bad)" }}>{s.down_days}</span>
            </span>
            <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
              Win rate <span className="mono" style={{ color: "var(--text)" }}>{s.win_rate_pct}%</span>
            </span>
            {s.best_day && (
              <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
                Terbaik <span className="mono" style={{ color: "var(--good)" }}>+{s.best_day.return_pct}%</span> {s.best_day.date}
              </span>
            )}
            {s.worst_day && (
              <span style={{ fontSize: 12, color: "var(--text-faint)" }}>
                Terburuk <span className="mono" style={{ color: "var(--bad)" }}>{s.worst_day.return_pct}%</span> {s.worst_day.date}
              </span>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(12, 1fr)", gap: 5 }}>
            {Array.from({ length: 12 }, (_, i) => i + 1).map((mo) => {
              const m = data.monthly.find((x) => x.month === mo);
              const onPage = Math.floor((mo - 1) / 2) === page;
              return (
                <button
                  key={mo}
                  onClick={() => setPage(Math.floor((mo - 1) / 2))}
                  title={m ? `${m.up_days} hari naik / ${m.down_days} hari turun` : "belum ada data"}
                  style={{
                    background: m ? shade(m.return_pct, Math.max(scale * 4, 3)) : "transparent",
                    border: `1px solid ${onPage ? "var(--accent)" : "transparent"}`,
                    borderRadius: 6, padding: "7px 4px", cursor: "pointer", textAlign: "center",
                  }}
                >
                  <div style={{ fontSize: 10, color: "var(--text-dim)" }}>{MONTHS[mo - 1]}</div>
                  <div className="mono" style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>
                    {m ? `${m.return_pct > 0 ? "+" : ""}${m.return_pct}%` : "—"}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
