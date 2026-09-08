export default function CaveatBanner() {
  const items = [
    "Brankas 2024–2026 sudah dibuka sekali (2026-09-07) dan hasilnya bertahan (PF 1,81 → 1,82). Mulai sekarang parameter TIDAK boleh disetel sambil melihat periode itu — nilainya sebagai uji independen sudah terpakai.",
    "95% CI Profit Factor periode eksplorasi menyentuh di bawah 1 (0,86) — edge kemungkinan besar nyata tapi besarnya belum pasti. Di periode gabungan CI-nya [1,00 ; 3,54], P(PF>1) 97,4%.",
    "Sebaran tahunan sangat timpang: 2025 +138,6% lalu 2026 −40,1%. CAGR yang mulus di atas kertas tidak berarti perjalanannya mulus.",
    "Universe memakai komposisi LQ45 hari ini, dipakai mundur ke 2019 — survivorship bias, belum dikoreksi.",
    "Belum walk-forward bergulir dan belum pernah dijalankan di akun nyata.",
  ];
  return (
    <div style={{ background: "rgba(224,168,62,0.08)", border: "1px solid rgba(224,168,62,0.35)", borderRadius: 10, padding: "14px 16px", marginBottom: 20 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--warn)", marginBottom: 8 }}>
        Belum kandidat final — baca sebelum menyimpulkan apapun
      </div>
      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--text-dim)", lineHeight: 1.7 }}>
        {items.map((t, i) => (
          <li key={i}>{t}</li>
        ))}
      </ul>
    </div>
  );
}
