import { useEffect, useRef, useState } from "react";
import { addTicker } from "../api";

const BADGE = {
  universe: { label: "universe", color: "var(--accent)", bg: "var(--accent-dim)" },
  lokal: { label: "ada data", color: "var(--text-dim)", bg: "var(--panel-2)" },
  tarik: { label: "perlu ditarik", color: "var(--warn)", bg: "rgba(224,168,62,0.12)" },
};

const badgeFor = (r) => (r.in_universe ? BADGE.universe : r.cached ? BADGE.lokal : BADGE.tarik);

export default function TickerSearch({ onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [busy, setBusy] = useState(null);
  const [searching, setSearching] = useState(false);
  const boxRef = useRef(null);

  useEffect(() => {
    const q = query.trim();
    if (q.length < 1) {
      setResults([]);
      return;
    }
    setSearching(true);
    const timer = setTimeout(() => {
      fetch(`/api/search?q=${encodeURIComponent(q)}`)
        .then((r) => r.json())
        .then((d) => {
          setResults(d.results || []);
          setActive(0);
          setOpen(true);
        })
        .catch(() => setResults([]))
        .finally(() => setSearching(false));
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const onDocClick = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const choose = async (r) => {
    if (!r) return;
    setOpen(false);
    if (!r.cached) {
      setBusy(r.ticker);
      try {
        await addTicker(r.ticker);
      } catch {
        setBusy(null);
        return;
      }
      setBusy(null);
    }
    setQuery("");
    setResults([]);
    onSelect(r.ticker);
  };

  const onKeyDown = (e) => {
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(a + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(a - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(results[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={boxRef} style={{ position: "relative", minWidth: 260, flex: "0 1 340px" }}>
      <input
        value={busy ? `Menarik data ${busy}…` : query}
        disabled={!!busy}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
        onKeyDown={onKeyDown}
        placeholder="Cari kode atau nama emiten…"
        style={{
          width: "100%", background: "var(--panel-2)", border: "1px solid var(--border)",
          borderRadius: 8, padding: "7px 10px", color: "var(--text)", fontSize: 13,
        }}
      />

      {open && query.trim() && (
        <div
          className="scrollbar-thin"
          style={{
            position: "absolute", top: "calc(100% + 4px)", right: 0, zIndex: 50,
            width: "max(100%, 420px)",
            background: "var(--panel)", border: "1px solid var(--border-strong, var(--border))",
            borderRadius: 8, maxHeight: 320, overflowY: "auto",
            boxShadow: "0 8px 24px rgba(0,0,0,0.45)",
          }}
        >
          {results.length === 0 && (
            <div style={{ padding: "12px 12px", fontSize: 12, color: "var(--text-faint)" }}>
              {searching ? "Mencari…" : `Tidak ada emiten cocok dengan "${query.trim()}"`}
            </div>
          )}
          {results.map((r, i) => {
            const b = badgeFor(r);
            return (
              <div
                key={r.ticker}
                onMouseEnter={() => setActive(i)}
                onClick={() => choose(r)}
                style={{
                  padding: "8px 12px", cursor: "pointer",
                  background: i === active ? "var(--panel-2)" : "transparent",
                  borderTop: i === 0 ? "none" : "1px solid var(--border)",
                  display: "flex", alignItems: "center", gap: 10,
                }}
              >
                <span className="mono" style={{ fontWeight: 600, fontSize: 13, minWidth: 48 }}>{r.ticker}</span>
                <span style={{ fontSize: 12, color: "var(--text-dim)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {r.name}
                </span>
                <span style={{ fontSize: 9, padding: "1px 6px", borderRadius: 4, background: b.bg, color: b.color, textTransform: "uppercase", whiteSpace: "nowrap" }}>
                  {b.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
