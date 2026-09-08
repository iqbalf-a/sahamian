import { useState } from "react";
import Home from "./views/Home";
import Screener from "./views/Screener";
import StockDetail from "./views/StockDetail";
import BacktestLab from "./views/BacktestLab";
import Sensitivity from "./views/Sensitivity";
import Calendar from "./views/Calendar";
import Research from "./views/Research";
import TickerSearch from "./components/TickerSearch";

const TABS = [
  { id: "utama", label: "Utama" },
  { id: "screener", label: "Screener" },
  { id: "kalender", label: "Kalender" },
  { id: "backtest", label: "Lab backtest" },
  { id: "sensitivitas", label: "Sensitivitas" },
  { id: "riset", label: "Riset" },
];

export default function App() {
  const [tab, setTab] = useState("utama");
  const [ticker, setTicker] = useState(null);

  // Detail saham adalah OVERLAY di atas tab yang sedang aktif, bukan tab tersendiri —
  // navigasi tetap berisi tujuan tetap, dan menutup detail mengembalikan ke tempat semula.
  const closeDetail = () => setTicker(null);

  return (
    <div style={{ minHeight: "100vh" }}>
      <header style={{ borderBottom: "1px solid var(--border)", background: "var(--panel)", position: "sticky", top: 0, zIndex: 20 }}>
        <div style={{ maxWidth: 1180, margin: "0 auto", padding: "0 20px", display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap" }}>
          <div style={{ padding: "14px 0", fontWeight: 600, fontSize: 14, whiteSpace: "nowrap" }}>
            Analisis Saham <span style={{ color: "var(--accent)" }}>IDX</span>
          </div>
          <nav style={{ display: "flex", gap: 2 }}>
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => { setTab(t.id); setTicker(null); }}
                style={{
                  background: "transparent", border: "none", cursor: "pointer",
                  padding: "16px 10px", fontSize: 13,
                  color: tab === t.id && !ticker ? "var(--text)" : "var(--text-dim)",
                  borderBottom: `2px solid ${tab === t.id && !ticker ? "var(--accent)" : "transparent"}`,
                }}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div style={{ marginLeft: "auto", padding: "8px 0" }}>
            <TickerSearch onSelect={setTicker} />
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1180, margin: "0 auto", padding: "24px 20px 60px" }}>
        {ticker ? (
          <StockDetail ticker={ticker} onBack={closeDetail} onSelect={setTicker} />
        ) : (
          <>
            {tab === "utama" && <Home onSelect={setTicker} />}
            {tab === "screener" && <Screener onSelect={setTicker} />}
            {tab === "kalender" && <Calendar />}
            {tab === "backtest" && <BacktestLab />}
            {tab === "sensitivitas" && <Sensitivity />}
            {tab === "riset" && <Research />}
          </>
        )}
      </main>

      <footer style={{ maxWidth: 1180, margin: "0 auto", padding: "0 20px 40px", fontSize: 11, color: "var(--text-faint)" }}>
        Bukan rekomendasi investasi. Data harian yfinance (harga sudah disesuaikan split &amp; dividen).
        Hanya strategi momentum yang sudah melewati validasi — lihat tab Riset.
      </footer>
    </div>
  );
}
