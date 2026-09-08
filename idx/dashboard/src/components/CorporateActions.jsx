import { useEffect, useState } from "react";

export default function CorporateActions({ ticker }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    fetch(`/api/actions/${ticker}`)
      .then((r) => (r.ok ? r.json() : r.json().then((b) => Promise.reject(new Error(b.detail)))))
      .then(setData)
      .catch((e) => setError(e.message));
  }, [ticker]);

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
        <span style={{ fontSize: 12, color: "var(--text-dim)" }}>Corporate action</span>
        {data?.dividend_yield_pct != null && (
          <span style={{ fontSize: 11, color: "var(--text-faint)" }}>
            Dividend yield 12 bulan:{" "}
            <span className="mono" style={{ color: "var(--good)", fontSize: 13 }}>{data.dividend_yield_pct}%</span>
          </span>
        )}
      </div>

      {error && <div style={{ color: "var(--bad)", fontSize: 12 }}>{error}</div>}
      {!data && !error && <div style={{ fontSize: 12, color: "var(--text-faint)" }}>Memuat…</div>}

      {data && (
        <>
          {data.splits?.length > 0 && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: "var(--text-faint)", marginBottom: 6 }}>Stock split</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {data.splits.map((s) => (
                  <span key={s.date} className="mono" style={{ fontSize: 12, background: "var(--panel-2)", borderRadius: 6, padding: "4px 9px" }}>
                    {s.date} · 1:{s.ratio}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={{ fontSize: 11, color: "var(--text-faint)", marginBottom: 6 }}>
            Dividen {data.dividends?.length ? `(${data.dividends.length} terakhir)` : ""}
          </div>
          {data.dividends?.length ? (
            <div className="scrollbar-thin" style={{ maxHeight: 190, overflowY: "auto" }}>
              <table style={{ fontSize: 12 }}>
                <tbody>
                  {data.dividends.map((d) => (
                    <tr key={d.date} style={{ borderTop: "1px solid var(--border)" }}>
                      <td className="mono" style={{ padding: "5px 0", color: "var(--text-dim)" }}>{d.date}</td>
                      <td className="mono" style={{ padding: "5px 0", textAlign: "right", color: "var(--good)" }}>
                        Rp{d.amount.toLocaleString("id-ID")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ fontSize: 12, color: "var(--text-faint)" }}>Tidak ada catatan dividen.</div>
          )}

          <div style={{ fontSize: 10, color: "var(--text-faint)", marginTop: 12, lineHeight: 1.6 }}>
            Tanggal yang tercatat adalah tanggal ex-dividend menurut yfinance, bukan tanggal
            pembayaran. Harga di chart sudah disesuaikan terhadap dividen &amp; split, jadi tidak
            terlihat turun di tanggal ex — itu memang disengaja supaya indikator tidak rusak.
          </div>
        </>
      )}
    </div>
  );
}
