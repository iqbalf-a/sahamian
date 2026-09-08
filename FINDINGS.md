# Hasil Riset EA Forex — Konsolidasi Angka

Rekap seluruh hasil numerik dari riset EURUSDm M15 (32 eksperimen, Agustus–September 2026).
Pendamping [`METHODOLOGY.md`](METHODOLOGY.md), yang berisi *cara*-nya; dokumen ini berisi *apa*-nya.

Disertakan agar sesi baru punya konteks lengkap tanpa harus membuka folder riset asal.

---

## 1. Kandidat final

**Konfigurasi** (EURUSDm M15, long & short, SL=3,5×ATR, TP=4,0×ATR, risiko 1%/trade):

```
MA20/100 SMA cross   -> sinyal dasar
                        ⚠️ arah efektifnya COUNTER-TREND: beli saat MA memotong
                        ke bawah, jual saat memotong ke atas (lihat METHODOLOGY 1.4)
RSI(14)              -> buang entry di titik ekstrem (70/30)
Parabolic SAR        -> konfirmasi: BUY hanya kalau SAR di bawah harga
ADX(14) > 30         -> filter kekuatan tren
ATR(14)/SMA50(ATR)   -> filter rezim volatilitas, harus dalam [0,7 ; 1,8]
Kemiringan slowMA    -> slowMA harus bergerak searah sinyal selama 10 bar
Ruang swing          -> butuh ≥2,0×ATR ruang ke swing high/low dalam 100 bar
Daily limit          -> (sudah jadi kode mati; tidak pernah aktif)
```

**Performa — angka resmi (2018–2025, rentang maksimum yang tersedia):**

| Metrik | Nilai | 95% CI |
|---|---:|---|
| Profit Factor | 1,73 (MQL5) / 1,59 (Python) | **[1,05 ; 2,49]** |
| Win Rate | 59,79% / 58,43% | [48,3% ; 68,5%] |
| Max Drawdown (backtest) | 3,98% | — |
| **Max Drawdown (p95, untuk perencanaan)** | — | **~6,8%** |
| Sharpe | 5,72 | — |
| Total trade | 97 / 89 | ~11–12 per tahun |
| Net profit 8 tahun | +2.483.229 IDR dari modal 10 juta | +24,8% |
| **P(Profit Factor > 1)** | — | **98,4%** |

## 2. Perbandingan per periode — bukti regime-dependence

| Periode | Peran | Trade | Win Rate | PF |
|---|---|---:|---:|---:|
| 2022–2025 | data riset (bias optimis) | 58 | 67,24% | 2,37 |
| 2018–2021 | brankas, belum tersentuh | 39 | 48,72% | 1,08 |
| **2018–2025** | **gabungan (resmi)** | **97** | **59,79%** | **1,73** |

Angka 2022–2025 adalah periode tempat semua filter dipilih — karenanya bias optimis. Selisih
antar periode besar (PF 2,37 vs 1,08) tapi **secara statistik belum signifikan**
(CI selisih [−6.519 ; +67.606]).

## 3. Evolusi kandidat

| Tahap | Trade | Win Rate | PF | Max DD |
|---|---:|---:|---:|---:|
| Baseline MA cross saja | 553 | 46,1% | 0,99 | — |
| + ADX>30 | 209 | 49,8% | 1,10 | — |
| + filter volatilitas | 138 | 53,6% | 1,31 | — |
| + filter kemiringan MA | 98 | 57,1% | 1,52 | — |
| **+ filter ruang swing (final)** | **89** | **58,4%** | **1,59** | 3,85% |

*(angka dari engine Python di rentang 2018–2025; MQL5 memberi angka sedikit lebih tinggi)*

## 4. Audit statistik — mana yang benar-benar terbukti

| Klaim | Selisih rata-rata | 95% CI | Verdict |
|---|---:|---|---|
| **Seluruh tumpukan filter vs tanpa filter** | +21.081 | **[+1.492 ; +40.465]** | ✅ **BERMAKNA** |
| Kontribusi ADX sendirian | +5.801 | [−8.372 ; +19.963] | ⚠️ tidak terbedakan |
| Kontribusi filter volatilitas | +17.244 | [−7.624 ; +42.108] | ⚠️ tidak terbedakan |
| Kontribusi filter kemiringan | +21.090 | [−11.131 ; +52.487] | ⚠️ tidak terbedakan |
| Kontribusi filter ruang swing | +23.502 | [−36.076 ; +80.806] | ⚠️ tidak terbedakan |
| ADX>35 vs ADX>30 | +11.481 | [−18.095 ; +41.284] | ⚠️ tidak terbedakan |
| Regime 2018-21 vs 2022-25 | +30.899 | [−6.519 ; +67.606] | ⚠️ nyaris |

**Kesimpulan**: tumpukan filter bekerja sebagai **paket** (terbukti), tapi kredit tidak bisa
dibagi ke komponen individual. Keempat filter menunjuk arah yang benar, jadi kemungkinan besar
memang bekerja — datanya saja belum cukup.

**Daya statistik**: butuh ~73 trade untuk membuktikan profitabilitas dasar; tersedia 89.

## 5. Walk-forward bergulir (latih 24 bln → uji 12 bln → geser)

| Jendela uji | Trade | Win Rate | PF | Net (IDR) |
|---|---:|---:|---:|---:|
| 2020 | 11 | 54,5% | 0,98 | −8.214 |
| 2021 | 7 | 57,1% | 1,51 | +119.915 |
| 2022 | 16 | 62,5% | 1,73 | +388.834 |
| 2023 | 13 | 61,5% | 1,81 | +316.853 |
| 2024 | 10 | 60,0% | 1,62 | +212.408 |
| 2025 | 14 | 71,4% | 3,16 | +642.303 |
| **Total** | **71** | | | **+1.672.099** |

5/6 jendela profitable, dengan tren membaik dari waktu ke waktu.

**Tuning vs patok tetap** (temuan penting):

| Pendekatan | Net OOS |
|---|---:|
| Pilih threshold ADX dari data latih | +1.179.046 |
| **Patok ADX>30** | **+1.672.099** |

## 6. Pendekatan yang GAGAL — dan kenapa

### 6.1 Filter yang ditolak

| Filter | Hasil | Sebab |
|---|---|---|
| RSI 70/30 klasik | netral total | MA lambat sudah menyerap info momentum |
| Filter trend H4 (MA50) | PF 0,81 | redundan — sama-sama mengukur arah |
| Trailing stop ATR | PF 0,67, DD 42% | memotong winner terlalu cepat |
| Triple MA 10/20/50 EMA | PF 0,93 | terlalu responsif untuk M15 |
| Konfirmasi MACD | PF 1,76→1,51 | redundan dengan MA cross |
| ADX di timeframe H4 | PF 1,50, DD naik | terlalu lag untuk sinyal M15 |
| Filter sesi waktu (5 jendela) | tidak ada yang menang | sinyal sudah menangkapnya tidak langsung |
| Filter extension | PF 1,99→1,89 | sudah tertutup filter volatilitas |
| Circuit breaker kalah beruntun | PF 2,24→2,13 | kalah beruntun tidak memprediksi kalah berikutnya |

### 6.2 Trading harian — tiga keluarga strategi, semuanya gagal

| Pendekatan | Konfigurasi diuji | PF terbaik | Max DD terburuk |
|---|---:|---:|---:|
| Trend-following MA cepat (M5/M1) | 12 | 0,81 | 98,95% |
| Mean-reversion Bollinger | — | 0,86 | 79,73% |
| Breakout Donchian | 14 | 0,91 | 99,34% |

**Penyebab struktural: biaya spread.** Di M15 spread ~2,5% dari target; di M5 ~6%. Frekuensi
harian tercapai (~1.900 trade / 8 tahun) tapi expectancy negatif.

Diagnosis presisi lewat win rate breakeven — breakout meleset konsisten 3–6 poin di bawah
ambang impas di **semua** rasio SL:TP yang diuji.

### 6.3 Uji multi-simbol (konfigurasi ADX-murni versi lama)

| Simbol | PF terbaik | Catatan |
|---|---:|---|
| EURUSDm | 1,64 | pola kuat & konsisten |
| GBPUSDm | 1,07 | pola mirip tapi lemah, sample tipis |
| XAUUSDm | 1,31 | tanpa pola konsisten; polanya bahkan terbalik |
| USDJPYm | 0,88 | gagal total, tidak ada pola |

Pola geografis: cocok untuk pair Eropa vs USD, tidak cocok untuk JPY (carry trade/BOJ) atau
komoditas (safe-haven/geopolitik).

⚠️ Belum diulang dengan konfigurasi final — hasil di atas memakai versi lama.

## 7. Analisis modal

| Modal | Net 8 thn | Return | Rata-rata/hari bursa | Max DD |
|---|---:|---:|---:|---:|
| 10 juta | +2.483.229 | 24,8% | ~1.200 | 3,98% |
| 50 juta | +14.034.078 | 28,1% | ~5.600 | 4,60% |
| 100 juta | +28.991.415 | 29,0% | ~11.500 | 4,62% |
| 450 juta | +132.748.969 | 29,5% | ~52.700 | 4,68% |

Dua catatan:
- **Modal kecil sedikit kurang efisien** (24,8% vs 29,5%) karena pembulatan lot memakan
  sebagian risiko yang direncanakan.
- Angka "rata-rata per hari" menyesatkan: dengan ~12 trade/tahun, **mayoritas hari nol**.
  Ini bukan model penghasilan harian.

## 8. Validasi silang Python vs MQL5

| Periode | MQL5 | Python | Selisih |
|---|---|---|---|
| 2018–2025 | 97 · 59,79% · 1,73 | 89 · 58,43% · 1,59 | −8 · −1,4pp · −0,14 |
| 2022–2025 | 58 · 67,24% · 2,37 | 53 · 64,15% · 2,10 | −5 · −3,1pp · −0,27 |
| 2018–2021 | 39 · 48,72% · 1,08 | 36 · 50,00% · 1,06 | −3 · +1,3pp · −0,02 |

Selisih tersisa berasal dari resolusi intrabar (MT5 memakai data M1; engine Python hanya M15).

Proses validasi ini menemukan 3 bug/kesalahpahaman yang tidak akan terlihat dari satu
implementasi saja — termasuk arah crossing yang terbalik.

---

## Ringkasan satu paragraf

Strategi MA-crossover counter-trend dengan empat lapis filter di EURUSDm M15 menghasilkan
Profit Factor ~1,6–1,7 selama 8 tahun (2018–2025) dengan 97 trade, win rate ~59%, dan drawdown
perencanaan ~7%. Edge-nya terbukti nyata (98,4% yakin PF>1) tapi tipis dan tidak pasti besarnya
(CI 1,05–2,49). Kontribusi masing-masing filter tidak bisa dibuktikan terpisah — tumpukan itu
bekerja sebagai paket. Upaya membuatnya jadi strategi harian gagal total di tiga keluarga
strategi berbeda karena biaya transaksi, dan frekuensi rendahnya justru bagian dari alasan ia
bekerja. Belum pernah diuji forward di akun live.
