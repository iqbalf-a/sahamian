# Eksperimen 001 — Momentum / relative strength lintas saham LQ45

Prioritas #1 dari [`METHODOLOGY.md` 4.7](../../../METHODOLOGY.md).

> **Pembaruan 2026-09-07 (dua hal penting):**
> 1. **Brankas 2024–2026 sudah dibuka sekali** dengan parameter beku di bawah. Hasilnya bertahan.
>    Jangan tuning parameter apapun terhadap periode itu lagi.
> 2. **Statistiknya dikoreksi.** Angka versi pertama dokumen ini dihitung dari P&L rupiah absolut
>    memakai `stats.py` warisan riset forex. Itu keliru untuk strategi yang memajemukkan modal —
>    lihat bagian "Koreksi statistik" di bawah. Semua angka di dokumen ini sudah versi ruang return.

## Hipotesis

Saham yang outperform dalam 6 bulan terakhir cenderung terus outperform dalam beberapa bulan
ke depan (efek momentum, terdokumentasi luas di literatur akademik lintas pasar). Cocok untuk
karakter biaya IDX karena berfrekuensi rendah (rebalance bulanan) dan bertarget besar.

## Konfigurasi (lihat `strategy.py`)

- Sinyal: return trailing 6 bulan tiap saham LQ45
- Seleksi: top 20% universe (min 3 saham) **dengan momentum positif saja**; kalau tidak ada
  yang positif, 100% cash bulan itu
- Bobot: equal-weight
- Rebalance: bulanan, long-only
- Biaya: beli 0,20% + jual 0,30% pada bagian yang di-turnover setiap rebalance

## Hasil (2019-2023, 60 bulan)

| Metrik | Strategi | Buy&hold equal-weight (36 saham, tanpa biaya) |
|---|---:|---:|
| Return total | +113,2% | +51,4% |
| CAGR | +16,3% | +8,8% |
| Profit Factor (unit=bulan) | 1,81 | — |
| Win rate bulanan | 53,3% | — |
| Max DD (backtest) | 38,7% | — |
| Total biaya transaksi | Rp12,2 juta (12,2% dari modal awal) | 0 |

**[Tahap 1 — screening]** PF 1,81 > 1, n=60 bulan ≥ 30 → **LOLOS**.

**[Tahap 2 — multi-periode]** 5/5 tahun profitable (2019: +1,5%, 2020: +12,3jt meski ada
crash Maret, 2021: +11,4jt, 2022: +61,5jt, 2023: +26,5jt). Tidak ada tahun rugi — tapi lihat
catatan kehati-hatian di bawah.

**[Tahap 5 — bootstrap, 20.000 iterasi, resample return bulanan]**
```
Profit Factor    obs=1.81    95% CI [0.86, 4.11]      P(PF>1) = 94,2%
Win Rate         obs=53.3%   95% CI [40.0%, 66.7%]
Return/bulan     obs=+1.56%  95% CI [-0.39%, +3.55%]   P(>0) = 94,2%
```

**Max Drawdown — permutasi urutan return bulanan:**
```
teramati backtest : 38,7%
median             : 31,6%
p75 / p95          : 36,8% / 45,2%
p99 / maks          : 50,7% / 60,8%
```
18% dari urutan acak menghasilkan DD lebih buruk dari yang teramati — urutan aslinya tipikal,
bukan kebetulan bagus.

## Tahap 4 — brankas (dibuka 2026-09-07, sekali)

| Periode | Bulan | CAGR | PF | Win rate | DD p95 |
|---|---:|---:|---:|---:|---:|
| Eksplorasi 2019–2023 | 60 | +16,3% | 1,81 | 53,3% | 45,2% |
| **Brankas 2024–2026** | **33** | **+21,3%** | **1,82** | **66,7%** | **48,3%** |
| **Gabungan 2019–2026 (headline)** | **93** | **+17,7%** | **1,79** | **58,1%** | **57,4%** |

CI Profit Factor gabungan: **[1,00 ; 3,54]**, P(PF>1) = **97,4%** — batas bawahnya kini praktis
menyentuh 1,0 dari sisi atas, jadi sedikit lebih meyakinkan daripada periode eksplorasi saja,
tapi tetap bukan bukti kuat.

**Ini hasil yang tidak terduga.** Di riset forex, membuka brankas menjatuhkan PF dari 2,37 ke 1,08.
Di sini PF justru bertahan (1,81 → 1,82). Dua tafsiran yang sama-sama masuk akal:
- efek momentum memang cukup universal dan tidak lahir dari overfitting (baseline ini hanya punya
  2 parameter, jauh lebih sedikit dari 4 lapis filter di riset forex), atau
- 2024–2026 kebetulan rezim yang ramah momentum.

**Yang jelas berbahaya**: return per tahun **2025 +138,6%, lalu 2026 −40,1%**. Rata-rata boleh
bagus, tapi drawdown p95 57% berarti perencanaan risiko harus menganggap kehilangan separuh modal
sebagai skenario normal, bukan ekstrem.

## Koreksi statistik — kenapa angka dokumen ini berubah

Versi pertama memakai `stats.permute_drawdown()` dan `bootstrap_metrics()` langsung dari riset
forex, yang bekerja atas **P&L rupiah absolut**. Di forex itu benar: sizing-nya risiko nominal
tetap per trade, jadi tiap trade sebanding. Di strategi ini modal dimajemukkan — P&L 2026 (modal
~Rp350jt) berskala 3,5× P&L 2019 (modal Rp100jt). Konsekuensinya:

- Permutasi urutan bulan bisa menaruh kerugian besar di awal saat equity masih kecil →
  **Max Drawdown terhitung 177%**, angka yang mustahil. Ini yang menyingkap bug-nya.
- Profit Factor jadi bergantung pada *di mana* bulan bagus/buruk jatuh dalam kurva pertumbuhan:
  periode gabungan terbaca PF 1,48 padahal yang benar 1,79.

Perbaikannya: seluruh metrik dihitung dari deret **return bulanan**
(`stats.permute_drawdown_returns()`, `engine.compute_metrics()`). Untuk periode eksplorasi
dampaknya kecil (DD p95 45,4% → 45,2%) karena pertumbuhan 5 tahun masih moderat; untuk periode
panjang dampaknya besar.

## Interpretasi jujur (mengikuti aturan 2.4)

- ✅ **Edge kemungkinan besar nyata**: P(PF>1) 94,2%, mengungguli buy&hold pasif ~2x lipat
  CAGR-nya di periode yang sama.
- ⚠️ **CI PF menyentuh di bawah 1** (0,86) — belum bisa diklaim pasti profitable dengan
  keyakinan tinggi ala kandidat forex (yang CI-nya [1,05; 2,49], seluruhnya di atas 1). Sample
  60 bulan lebih kecil dari ~73 trade yang dihitung perlu untuk forex; di sini unitnya bulan
  bukan trade individual, jadi angka kebutuhan sample itu tidak langsung berlaku, tapi
  prinsipnya sama: **jangan anggap ini pasti**.
- ⚠️ **Max Drawdown jauh lebih besar** dari kandidat forex (38,7% vs ~4-7%). Sebagian besar
  disebabkan crash Covid Maret 2020 (portofolio kosong total bulan itu, capital jatuh dari
  ~Rp94jt ke ~Rp65jt dalam 2 bulan sebelum sinyal sempat bereaksi). p95 dari permutasi (45,4%)
  seharusnya dipakai untuk perencanaan risiko, **bukan** angka 38,7% mentah.
- ⚠️ **5/5 tahun profitable itu mengesankan tapi n kecil** — 5 titik data tahunan tidak cukup
  untuk klaim konsistensi statistik kuat, terutama karena 2019-2023 semuanya rezim bull market
  IHSG pasca-2020. Belum diuji di rezim turun berkepanjangan.
- ⚠️ **Belum walk-forward** (tahap 3) dan **belum brankas** (tahap 4) — angka di atas semuanya
  dari periode yang juga dipakai untuk merancang strategi (6 bulan lookback, 20% seleksi bukan
  hasil tuning ekstensif, tapi tetap perlu diverifikasi di luar sample).
- ⚠️ Universe LQ45 memakai komposisi **hari ini** (2026), bukan historis — survivorship bias
  dicatat di SETUP.md, belum dikoreksi.

## Verdict tahap validasi

Lolos tahap 1, 2, dan 5 dari tangga di [`METHODOLOGY.md` 2.2](../../../METHODOLOGY.md).
**Belum** menjalani tahap 3 (walk-forward bergulir) dan tahap 4 (brankas 2024-2026) —
itu langkah wajib berikutnya sebelum kandidat ini bisa dianggap final, sesuai pola forex
kemarin (PF turun dari 2,37 ke 1,08 begitu brankas dibuka).

## Langkah berikutnya yang disarankan

1. Walk-forward bergulir (latih 24 bln → uji 12 bln → geser) di dalam periode eksplorasi.
2. Sensitivitas parameter kasar (lookback 3/6/9/12 bulan, top 10%/20%/30%) — HANYA di
   eksplorasi, untuk melihat apakah arah hasil stabil (bukan untuk cherry-pick angka terbaik).
3. Baru buka brankas 2024-2026 **sekali**, laporkan angka gabungan sebagai headline.
