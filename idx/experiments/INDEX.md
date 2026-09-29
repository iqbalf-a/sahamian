# INDEX — Progres riset IDX

Sumber kebenaran progres. Baca ini duluan di sesi manapun sebelum mengulang eksperimen.

## Cara menjalankan aplikasi

Dua server, keduanya terdaftar di `.claude/launch.json`:

```
idx-api   backend FastAPI  :8000   (uvicorn app.server:api)
idx-app   frontend Vite    :5173   (npm run dev, proxy /api -> :8000)
```

Buka `http://localhost:5173`. Tab: **Utama** (IHSG, pergerakan tak wajar + berita, top
gainer/loser/trending/teraktif/52m), **Screener** (7 template — lihat di bawah), **Kalender**
(heatmap untung-rugi harian IHSG atau per saham), **Lab backtest**, **Sensitivitas**, **Riset**.

Detail saham dibuka lewat klik baris atau pencarian, tampil sebagai overlay — **bukan tab
navigasi**, supaya navigasi tetap berisi tujuan tetap. Isinya: chart garis/candle dengan
SMA20/50/200 + panel RSI (bisa diperbesar), penilaian terhadap kriteria strategi, kelayakan
target profit di harga sekarang, dan corporate action (dividen + split + dividend yield).

**Data**: 82 saham (LQ45 + IDX80) di `data/`, indeks IHSG di `data_index/`, corporate action
di-cache di `data_actions/`, judul berita di `data_news/`.

**Panel berita & AI** (di tab Utama): mendeteksi saham yang bergerak >2 simpangan baku dari
volatilitasnya sendiri, lalu mencocokkan judul berita dari RSS (CNBC Indonesia, Kontan,
IDX Channel). Analisis AI opsional — aktif hanya kalau `ANTHROPIC_API_KEY` dipasang, dan
prompt-nya secara eksplisit melarang model menebak sebab di luar judul yang benar-benar
diambil. Tanpa kunci, panel tetap berguna dan tidak mengarang apapun.

Template screener (`screeners.py`), dengan status kejujuran di tiap kartu:

| Template | Status | Catatan |
|---|---|---|
| Momentum lintas saham | tervalidasi sebagian | eksperimen 001–003, satu-satunya yang lolos |
| Beli sore → jual pagi | gagal: biaya | efek nyata (+0,27%/hari) tapi bersihnya negatif semua |
| Beli pagi → jual sore | gagal: sinyal | kotornya saja sudah −0,17%/hari |
| Akumulasi (proxy bandarmology) | gagal: backtest | +1,6% vs buy&hold +8,8%; **bukan bandarmology asli** |
| Breakout konsolidasi | gagal: backtest | −5,7%, PF 0,83 — mereplikasi kegagalan di forex |
| Trend-following | gagal: backtest | −1,9%, PF 1,05 |
| Koreksi dalam tren naik | gagal: backtest | −0,4%, win rate bulanan 35% |

Template yang gagal sengaja **tetap ditampilkan** beserta angka kegagalannya — menghapusnya
akan menyembunyikan pelajaran bahwa layar screener yang rapi belum tentu menghasilkan uang.

Backend memakai venv `idx/.venv` (dibuat dari `idx/requirements.txt`). Data harian ada di `data/*.csv`. Setup lengkap ada di [README proyek](../../README.md).

**Pencarian emiten** (kotak di kanan atas): mengetik kode ATAU nama perusahaan ("bank",
"asuransi", "unilever") memunculkan saran. Sumber nama: `ticker_names.json`, di-cache dari
yfinance lewat `build_ticker_names.py` — sengaja tidak diketik manual supaya tidak ada nama
perusahaan yang salah. Emiten di luar data lokal dicari live lewat `yf.Search` dan ditandai
"perlu ditarik"; memilihnya akan menarik datanya dulu (`POST /api/fetch/{ticker}`) lalu membuka
halaman analisisnya. Saham hasil tarikan masuk sebagai `extra_tickers()`, **tidak** ikut ke
universe riset (lihat temuan 8).

Catatan: `engine.py` adalah versi berparameter yang dipakai aplikasi; `experiments/NNN/strategy.py`
tetap snapshot beku sesuai METHODOLOGY 2.1. Keduanya sudah diverifikasi menghasilkan angka identik
untuk parameter default eksperimen 001.

## Status

- **Universe**: LQ45 komposisi Agu-Okt 2026 (44 ticker), lihat `SETUP.md`. Data terverifikasi
  bebas artefak split/dividen (scan seluruh universe, tidak ada lompatan 1-hari >40%; BBCA
  dicek manual di sekitar split 1:5 Juni 2021, mulus).
- **Rasio biaya** (aturan 1.3): dengan biaya bolak-balik 0,50%, target profit perlu **≥15%**
  agar rasio biaya di bawah 5% (di 10% rasionya masih 5,0%, kategori "berat"). Ini mengunci
  desain ke swing/position trading, sesuai prediksi METHODOLOGY 4.2.
- **Brankas**: 2024-01-01 s/d 2026-09-07 — **SUDAH DIBUKA 2026-09-07**, sekali, dengan parameter
  default eksperimen 001 yang sudah beku (lookback 6 bln, top 9, biaya 0,20/0,30%). Mulai sekarang
  **jangan tuning parameter apapun sambil melihat periode ini** — nilainya sebagai uji independen
  sudah terpakai. Kalau butuh brankas baru, sisihkan rentang lain (mis. data 2027 ke depan).

## Tabel eksperimen

| # | Nama | Ide | Tahap tercapai | Verdict |
|---|---|---|---|---|
| 001 | [momentum_baseline](001_momentum_baseline/analysis.md) | Momentum lintas saham, top 9 return 6bln, rebalance bulanan | 1, 2, 4, 5 | Brankas bertahan (PF 1,81 → 1,82). Gabungan: CAGR 17,7%, PF 1,79 CI[1,00;3,54]. Tapi DD p95 57% dan 2026 −40,1% |
| 002 | [walkforward](002_walkforward/analysis.md) | Walk-forward bergulir + sensitivitas parameter 36 sel | 3 | 3/3 jendela profitable dengan patokan tetap. **Tuning per jendela KALAH** (+59,3% vs +87,3%) — mereplikasi temuan forex. Arah konsentrasi (top 3) terlihat lebih kuat tapi belum layak dipakai |
| 003 | [template_validation](003_template_validation/analysis.md) | Backtest 4 template screener lain sebagai portofolio bulanan | 1, 2 | **Semuanya gagal.** Tidak ada yang mengalahkan buy&hold (+8,8%); breakout −5,7%, trend −1,9%, pullback −0,4%, akumulasi +1,6%. Hanya momentum yang lolos |

### Hasil per periode (eksperimen 001, parameter default)

| Periode | Bulan | CAGR | PF | Win rate | DD p95 |
|---|---:|---:|---:|---:|---:|
| Eksplorasi 2019–2023 | 60 | +16,3% | 1,81 | 53,3% | 45,2% |
| Brankas 2024–2026 | 33 | +21,3% | 1,82 | 66,7% | 48,3% |
| **Gabungan 2019–2026 (headline)** | **93** | **+17,7%** | **1,79** | **58,1%** | **57,4%** |

Return per tahun: 2019 +1,5% · 2020 +12,1% · 2021 +10,0% · 2022 +49,1% · 2023 +14,2% ·
2024 +16,2% · 2025 **+138,6%** · 2026 **−40,1%**.

## Temuan

1. LQ45 saat ini (44 ticker) dipakai sebagai proxy universe historis 2019-2023 — survivorship
   bias, dicatat eksplisit, belum dikoreksi dengan komposisi historis riil.
2. Rasio biaya IDX mengonfirmasi prediksi METHODOLOGY 4.2: target realistis ≥15%, jauh dari
   swing trading target 2-3% ala forex.
3. Strategi momentum baseline (exp 001) mengungguli buy&hold pasif (CAGR 16,3% vs 8,8%,
   2019-2023) tapi dengan Max DD jauh lebih tinggi dari kandidat forex (p95 45% vs ~7%),
   didominasi oleh crash Covid Maret 2020. Edge kemungkinan nyata (P(PF>1)=94,3%) tapi CI
   masih menyentuh di bawah 1 — **belum cukup bukti untuk klaim final**.

4. ⚠️ **`stats.py` warisan riset forex tidak bisa dipakai apa adanya untuk strategi portofolio.**
   `permute_drawdown()` dan `bootstrap_metrics()` di sana bekerja atas **P&L rupiah absolut** —
   asumsi yang benar di forex karena risikonya nominal tetap per trade. Di strategi ini modal
   dimajemukkan, jadi P&L bulan-bulan akhir jauh lebih besar secara nominal; begitu urutannya
   diacak, kerugian besar bisa jatuh di awal dan menghasilkan **Max Drawdown 177%** — angka
   yang mustahil. Ditemukan lewat aplikasi saat menjalankan periode gabungan.
   **Perbaikan**: seluruh metrik (PF, win rate, DD, bootstrap) kini dihitung di **ruang return**,
   lewat `stats.permute_drawdown_returns()` dan `engine.compute_metrics()`.
   Dampak ke angka lama: DD p95 eksplorasi 45,4% → 45,2% (nyaris sama, karena 5 tahun
   pertumbuhannya moderat), tapi PF periode gabungan 1,48 (salah) → 1,79 (benar).
   **Pelajaran umum: cek satuan statistik cocok dengan mekanika sizing strategi sebelum memakai
   ulang alat statistik lintas pasar.**

5. Brankas IDX **bertahan**, berbeda dari riset forex (PF 2,37 → 1,08). Tapi ini bukan berarti
   strateginya lebih kokoh: sebagian besar hasil brankas datang dari satu tahun ekstrem
   (2025 +138,6%) yang langsung diikuti −40,1% di 2026. Rata-rata bagus, perjalanannya brutal.

6. ✅ **"Jangan tuning ulang parameter per periode" (METHODOLOGY 3.3) TEREPLIKASI di IDX.**
   Walk-forward bergulir: memilih lookback dari data latih menghasilkan +59,3% majemuk,
   mematoknya di 6 bulan menghasilkan +87,3%. Pola kegagalannya terlihat jelas di jendela 2023
   (data latih bilang lookback 9 → hasilnya −10,3%, sementara patokan 6 → +14,2%).
   Ini temuan lintas-pasar pertama yang bertahan dari forex M15 ke saham harian —
   kemungkinan besar pelajaran paling transferable dari seluruh riset ini.
   **Implikasi produk: jangan pernah menambahkan fitur "auto-optimize" ke aplikasi.**

7. Permukaan parameter **tidak datar sepanjang lookback**: 2–3 bulan gagal (CAGR 0–7%),
   6–12 bulan bekerja (CAGR 12–43%). Bentuk ini cocok dengan literatur momentum klasik
   (formasi 6–12 bulan), jadi berstruktur, bukan puncak acak — tapi artinya kalau lookback awal
   yang dipilih kebetulan 3 bulan, riset ini akan menyimpulkan "momentum tidak bekerja di IDX".
   **Pilihan parameter awal bisa menentukan kesimpulan seluruh riset.**

8. 🐛 **Universe bocor lewat folder data (sudah diperbaiki).** `close_panel()` dulu memakai
   "semua CSV di `data/`" sebagai universe, jadi saham yang ditambahkan user lewat tombol
   "Tambah" di aplikasi (MEDS, 2026-09-07 13:34) otomatis ikut ke backtest dan screener —
   mengubah hasil riset tanpa terlihat. Eksperimen 001 (13:13) dan 002 (13:21) ditulis sebelum
   itu, jadi **keduanya bersih**. Perbaikan: daftar `UNIVERSE` eksplisit di `engine.py`,
   `universe_tickers()` untuk riset, `extra_tickers()` untuk saham tambahan.
   **Pelajaran: universe yang "dikunci" di dokumen tidak terkunci sampai dikunci di kode.**

9. **Anomali overnight ada dan kuat di LQ45, tapi tidak bisa ditradingkan.** Rata-rata
    lintas 44 saham (2 tahun terakhir): return semalam (tutup→buka) **+0,272%/hari** dengan
    win rate 58%, sementara return intraday (buka→tutup) **−0,168%/hari** dengan win rate 38%.
    Jadi hampir seluruh kenaikan saham IDX terjadi saat bursa tutup — pola yang juga
    terdokumentasi di pasar lain. Tapi friksinya (komisi 0,5% + 1 fraksi harga tiap sisi)
    berkisar 0,93%–2,48% per transaksi, yaitu **2–5× ukuran efeknya**. Hasil bersih:
    **0 dari 44 saham** positif; yang terbaik pun −74%/tahun.
    Ini contoh paling telanjang dari aturan 1.3: efeknya nyata, edge-nya nyata, dan tetap
    tidak bisa dipakai. Saham murah paling parah — di BUMI (Rp224) satu fraksi harga = 0,45%.

11. **Empat template screener lain semuanya gagal (eksperimen 003).** Breakout paling buruk
    (PF 0,83) — dan ini **mereplikasi riset forex**, di mana 14 konfigurasi breakout menghasilkan
    PF terbaik 0,91. Trend-following gagal (−1,9%) padahal paling terasa "masuk akal". Proxy
    bandarmology tidak punya edge (+1,6%, CI menyentuh nol) — yang terbukti gagal adalah *jejak
    akumulasi di OHLCV*, bukan bandarmology sungguhan yang butuh broker summary.
    **Momentum menang justru karena paling sedikit strukturnya**: tanpa indikator apapun, hanya
    peringkat return 6 bulan. Empat yang kalah semuanya memakai lebih banyak indikator.

10. Konsentrasi (pegang 3 saham, bukan 9) memberi CI Profit Factor yang **tidak menyentuh 1**
   ([1,31 ; 5,61] vs [0,86 ; 4,11]) dengan drawdown setara. Menggoda, tapi ditemukan lewat
   menyisir 36 sel tanpa koreksi perbandingan-berganda, CI-nya tumpang tindih lebar, dan 3 saham
   berarti 33% modal per emiten (risiko suspensi belum dimodelkan). **Ditahan sebagai hipotesis
   pra-terdaftar, bukan perubahan konfigurasi.**

## Checklist anti-duplikasi

- [x] Setup harness + kunci brankas
- [x] Verifikasi split/dividend
- [x] Hitung rasio biaya
- [x] Strategi baseline #1 (momentum) — screening + multi-periode + bootstrap
- [x] Buka brankas (SEKALI — dilakukan 2026-09-07, hasil di tabel di atas)
- [x] Aplikasi analisis (screener + detail saham + lab backtest) — `sahamian/idx/app` + `dashboard`
- [x] Walk-forward bergulir untuk exp 001 (exp 002)
- [x] Sensitivitas parameter + uji tuning-vs-patokan (exp 002)
- [ ] **Tetapkan brankas BARU** — brankas lama sudah terpakai. Kandidat: data 2027 ke depan,
      atau universe terpisah (IDX80 di luar LQ45). Wajib sebelum menguji hipotesis di bawah.
- [ ] Hipotesis pra-terdaftar #1: konsentrasi (top 3) lebih baik dari top 9 — lihat temuan 8
- [ ] Hipotesis pra-terdaftar #2: filter rezim (mis. tren IHSG) meredam tahun buruk seperti
      2026 (−40,1%) tanpa merusak edge
- [ ] Strategi baseline #2 (trend-following harian, prioritas 4.7 poin 2)
- [ ] Modelkan suspensi & slippage (belum ada di engine — makin penting kalau konsentrasi dipakai)
- [ ] Forward test / validasi live
