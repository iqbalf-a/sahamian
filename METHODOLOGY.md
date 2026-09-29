# Metodologi Riset Strategi Trading Sistematis

Dokumen serah-terima dari riset EA MetaTrader 5 (EURUSDm M15, 41 temuan, 32 eksperimen,
Agustus–September 2026). Ditulis agar **sesi baru bisa langsung memakainya tanpa membaca
histori percakapan**.

Bagian 1–3 bersifat umum dan berlaku untuk pasar apapun.
Bagian 4 khusus adaptasi ke **saham Indonesia (IDX)**.

Sumber lengkap riset asal:
- [`../ian-skills/mt5-ea/experiments/INDEX.md`](../ian-skills/mt5-ea/experiments/INDEX.md) — 41 temuan bernomor
- [`../ian-skills/mt5-ea/quant-engine/ANALYSIS.md`](../ian-skills/mt5-ea/quant-engine/ANALYSIS.md) — analisis statistik
- [`../ian-skills/mt5-ea/quant-engine/README.md`](../ian-skills/mt5-ea/quant-engine/README.md) — engine & gotcha teknis

---

# BAGIAN 1 — Kesalahan yang paling mahal, dan cara menghindarinya

Empat hal ini ditemukan **setelah** riset dianggap selesai, dan semuanya mengubah kesimpulan.
Kerjakan di awal, bukan di akhir.

## 1.1 Sisihkan periode "brankas" SEBELUM eksperimen pertama

**Yang terjadi:** 26 eksperimen dijalankan di data 2022–2025 yang sama. Walk-forward internal
(membelah 2022-23 vs 2024-25) selalu lolos, jadi terasa aman. Saat akhirnya diuji di 2018–2021
yang belum pernah disentuh, Profit Factor jatuh dari 2.37 ke 1.08.

**Kenapa walk-forward internal tidak menangkapnya:** membelah satu rentang data hanya menguji
stabilitas di dalam rezim pasar yang mirip. Dua paruh dari periode berdekatan punya karakter
serupa.

**Aturan:**
1. Cek dulu berapa jauh histori tersedia (jalankan probe di beberapa periode lama).
2. Sisihkan **sepertiga sampai separuh data paling awal** sebagai brankas. Jangan disentuh
   selama eksplorasi — bahkan untuk mengintip.
3. Buka **sekali saja** di akhir, setelah kandidat final terpilih.
4. Laporkan angka **gabungan seluruh rentang** sebagai headline, bukan angka periode riset.

## 1.2 Hitung daya statistik di awal

```
n_dibutuhkan ≈ (1.96 × simpangan_baku_profit_per_trade / rata_rata_profit_per_trade)²
```

Di riset asal: rata-rata 20.656, simpangan baku 90.169 → **~73 trade** sekadar untuk membuktikan
strateginya profitable. Dengan ~11 trade/tahun itu berarti **~7 tahun data untuk klaim paling
dasar**.

**Kalau angka ini menunjukkan Anda butuh 30 tahun data untuk membedakan dua varian, jangan
rancang riset yang bergantung pada pembedaan itu.** Hitung sebelum mulai.

## 1.3 Cek struktur biaya sebelum menulis kode

Bandingkan biaya transaksi terhadap jarak target:

```
rasio_biaya = biaya_bolak_balik / jarak_TP
```

**Aturan praktis: kalau rasio > ~5%, strategi kemungkinan besar tidak akan profitable berapapun
tuningnya.**

Di riset asal ini menjelaskan kegagalan total ide trading harian: di M15 spread ~2,5% dari
target, di M5 melonjak ke ~6%. Tiga keluarga strategi berbeda (trend-following, mean-reversion,
breakout — total 26+ konfigurasi) semuanya rugi, dan penyebabnya struktural, bukan tuning.

⚠️ **Ini jauh lebih kritis untuk saham Indonesia** — lihat Bagian 4.2.

## 1.4 Verifikasi arah logika lewat trade nyata, bukan dengan membaca kode

**Yang terjadi:** selama berbulan-bulan strategi didokumentasikan sebagai *trend-following MA
crossover*. Ternyata EA-nya **membeli saat MA memotong ke bawah** — sebuah strategi
*counter-trend / beli pullback*. Penyebabnya konvensi indeks buffer MQL5 yang salah dibaca.

Backtest-nya tetap valid (yang diuji adalah perilaku nyata), tapi seluruh narasi tentang cara
kerjanya salah — dan itu mempengaruhi filter apa yang dianggap masuk akal untuk dicoba.

**Aturan:** cetak beberapa trade nyata (waktu entry, arah, harga, nilai indikator di sekitarnya)
dan periksa manual bahwa arahnya sesuai maksud. Lakukan sekali di awal.

---

# BAGIAN 2 — Alur kerja eksperimen

## 2.1 Struktur file

```
<workspace>/
  experiments/
    SETUP.md          harness standar: instrumen, timeframe, rentang tanggal, modal,
                      model simulasi, biaya. DIKUNCI di awal agar antar-eksperimen
                      bisa dibandingkan adil.
    INDEX.md          sumber kebenaran progres: tabel semua eksperimen + metrik +
                      verdict, daftar temuan bernomor, checklist anti-duplikasi.
                      BACA INI DULUAN di sesi manapun.
    NNN_nama/
      strategy.py     kode PERSIS yang diuji (snapshot, bukan referensi)
      analysis.md     hipotesis, parameter, hasil, interpretasi jujur
      *.ini / config  konfigurasi run (audit trail)
```

`INDEX.md` harus berdiri sendiri: sesi baru tanpa histori chat harus bisa membacanya dan
langsung tahu apa yang sudah dicoba dan apa berikutnya.

## 2.2 Tangga validasi

Naik bertahap; jangan lompat ke klaim sebelum melewati tangga di bawahnya.

| Tahap | Tujuan | Kriteria lanjut |
|---|---|---|
| 1. Screening cepat | buang ide yang jelas gagal | PF > 1, trade ≥ 30 |
| 2. Multi-periode | apakah bertahan lintas tahun | profitable di mayoritas tahun |
| 3. Walk-forward bergulir | stabil lintas waktu + apakah tuning menggeneralisasi | mayoritas jendela profitable |
| 4. Brankas (belum tersentuh) | ekspektasi sebenarnya | arah perbaikan bertahan |
| 5. Bootstrap + daya | seberapa pasti | CI tidak menyentuh nol |
| 6. Forward test live | realitas eksekusi | — |

## 2.3 Analisis statistik yang wajib

**a. Bootstrap selang kepercayaan** (resample daftar trade dengan pengembalian, 20.000 iterasi)
→ CI untuk Profit Factor, Win Rate, expectancy.

Di riset asal: PF 1.59 punya CI **[1.05, 2.49]**. Edge-nya hampir pasti ada (P(PF>1) = 98,4%)
tapi besarnya bisa nyaris breakeven. Win Rate 58,4% punya CI [48,3%, 68,5%] — artinya
**membandingkan varian berdasarkan selisih win rate 2–3 poin adalah membandingkan noise.**

**b. Permutasi urutan trade** → distribusi Max Drawdown.

DD sangat bergantung pada URUTAN menang/kalah. Di riset asal DD teramati 3,85% ternyata lebih
baik dari 64% urutan acak; p95-nya **6,82%**. **Laporkan DD persentil 95 untuk perencanaan
risiko, bukan angka backtest mentah.**

**c. Uji khusus filter bertingkat.** Kalau filter hanya *membuang* trade (B ⊂ A), jangan
bandingkan PF A vs PF B — itu membuang informasi. Periksa langsung **trade yang dibuang**:
kalau ekspektasinya signifikan lebih buruk dari yang dipertahankan, filternya bekerja.

## 2.4 Aturan pelaporan yang jujur

| ❌ Jangan | ✅ Sebaliknya |
|---|---|
| "Filter X menang di SEMUA metrik" | "Filter X menunjuk arah yang benar, tapi CI-nya menyentuh nol — dugaan berarah, belum terbukti" |
| Melaporkan Max DD backtest apa adanya | Melaporkan DD persentil 95 |
| Angka tunggal "PF 1.73" | "PF 1.59, 95% CI [1.05, 2.49]" |
| Memakai angka periode riset sebagai ekspektasi | Memakai angka gabungan seluruh rentang |

**"Tidak terbedakan" ≠ "tidak berguna"** — itu pernyataan tentang ukuran sample. Tapi juga
berarti: **jangan berpindah konfigurasi** berdasarkan selisih yang tidak terbedakan.

---

# BAGIAN 3 — Temuan substantif yang kemungkinan transferable

Semua berasal dari forex M15. Perlakukan sebagai **hipotesis awal untuk diuji ulang**, bukan
kebenaran yang otomatis berlaku di saham.

## 3.1 Filter harus menambah dimensi informasi BARU

Pola paling berdampak di riset asal. Sebelum menambah filter, tanya: *informasi apa yang
ditambahkan filter ini yang BELUM ada di sinyal utama?*

| Dimensi | Contoh | Hasil |
|---|---|---|
| Kekuatan tren | ADX | ✅ berhasil |
| Rezim volatilitas | ATR / SMA(ATR) | ✅ berhasil |
| Percepatan tren | kemiringan MA lambat | ✅ berhasil |
| Struktur harga | ruang ke swing high/low | ✅ berhasil |
| Arah tren (lagi) | MACD, MA timeframe lebih besar | ❌ redundan |
| Waktu/sesi | filter jam perdagangan | ❌ redundan |
| Timeframe berbeda utk indikator sama | ADX di H4 utk sinyal M15 | ❌ gagal |

⚠️ **Catatan audit**: kontribusi masing-masing filter di atas **tidak terbukti signifikan
secara individual** — hanya efek kumulatifnya yang terbukti. Perlakukan tabel ini sebagai
panduan arah eksplorasi, bukan peringkat mapan.

## 3.2 Frekuensi trade adalah KONSEKUENSI logika, bukan parameter bebas

Permintaan "untung kecil tapi tiap hari" tidak bisa dipenuhi dengan menurunkan timeframe.
Diuji 26+ konfigurasi di tiga keluarga strategi; semuanya rugi begitu frekuensi naik.

Frekuensi tinggi mudah dicapai (breakout menghasilkan ~1 trade/hari bursa) — yang sulit adalah
frekuensi tinggi **dengan expectancy positif**.

**Kalau kandidat yang profitable ternyata berfrekuensi rendah, itu kemungkinan besar bagian dari
alasan ia bekerja**, bukan kekurangan yang perlu diperbaiki.

## 3.3 Jangan tuning ulang parameter per periode

Walk-forward bergulir (latih 24 bln → uji 12 bln → geser, 6 jendela):

| Pendekatan | Net out-of-sample |
|---|---:|
| Pilih parameter terbaik dari data latih | +1.179.046 |
| **Patok satu nilai tetap** | **+1.672.099** |

Optimasi per periode **kalah dari tidak mengoptimasi**. Untuk strategi berfrekuensi rendah,
default-nya: jangan tuning ulang.

## 3.4 Indikator lambat mengalahkan yang responsif (di timeframe kecil)

MA20/100 SMA mengalahkan triple-MA 10/20/50 EMA. SL lebar (3,5×ATR) mengalahkan SL ketat.
Threshold filter makin ketat makin baik. Arah tuning yang sehat: **lebih selektif, bukan lebih
sering entry.**

## 3.5 Win rate tinggi tanpa rasio menang:kalah sehat = kehancuran

Mean-reversion Bollinger: win rate 52,4% (lebih tinggi dari kandidat trend-following saat itu)
tapi **kehilangan 78% modal**, drawdown 79,7%. TP jauh lebih dekat dari SL.

**Diagnosis cepat strategi gagal — hitung win rate breakeven:**

| Rasio SL:TP | Win rate untuk impas |
|---|---:|
| 1 : 1 | > 50,0% |
| 1 : 1,5 | > 40,0% |
| 1 : 3 | > 25,0% |
| 1 : 5 | > 16,7% |

Bandingkan dengan hasil backtest. Kalau meleset jauh di **semua** rasio, sinyalnya memang tidak
punya daya prediksi — bukan sekadar kalah karena biaya.

## 3.6 Filter memperbaiki edge tipis, TIDAK menciptakan edge yang tidak ada

Menambah ADX + filter volatilitas + anti-chasing ke strategi breakout ber-PF 0,82 hanya
menggesernya ke 0,78–0,83. **Kalau strategi dasarnya PF jauh di bawah 1, ganti logika entry-nya,
jangan tambah filter.**

## 3.7 Strategi bersifat instrument-specific

Konfigurasi juara di EURUSDm **rugi** di XAUUSDm dengan parameter sama. Dan polanya bisa
terbalik: di EURUSD makin ketat ADX makin baik, di Gold datar tanpa pola. Selalu sweep ulang
dari nol di instrumen baru.

⚠️ **Ini akan jadi jauh lebih penting di saham** — lihat Bagian 4.4.

---

# BAGIAN 4 — Adaptasi untuk saham Indonesia (IDX)

## 4.1 Apa yang berubah, apa yang tidak

| Tetap berlaku | Perlu diganti |
|---|---|
| Seluruh Bagian 1 (brankas, daya statistik, cek biaya, verifikasi arah) | Sumber data |
| Seluruh Bagian 2 (alur kerja, tangga validasi, statistik) | Model biaya transaksi |
| Prinsip 3.1–3.6 sebagai hipotesis awal | Mekanika pasar (jam, lot, fraksi harga, ARA/ARB) |
| | Timeframe (harian, bukan M15) |
| | **Dimensi baru: pemilihan universe saham** |

## 4.2 ⚠️ Biaya transaksi — perbedaan paling menentukan

Ini bagian yang paling mungkin membatalkan strategi sebelum dimulai.

| | Forex (EURUSD, Exness) | Saham IDX (broker retail tipikal) |
|---|---|---|
| Biaya beli | spread ~0,8 pip ≈ **0,008%** | komisi ~**0,15–0,25%** |
| Biaya jual | (termasuk di spread) | komisi ~**0,25–0,35%** (termasuk pajak final 0,1%) |
| **Bolak-balik** | **~0,02%** | **~0,4–0,6%** |

**Biayanya sekitar 20–30× lipat lebih besar.**

Terapkan aturan 1.3 sejak awal: dengan biaya bolak-balik 0,5%, agar rasio biaya di bawah 5%,
**target profit minimal harus ~10%**. Itu langsung menyingkirkan:
- Scalping dan day trading — praktis mustahil profitable secara retail
- Swing trading target 2–3% — rasio biayanya 17–25%, sangat berat

**Konsekuensi rancangan:** arahkan ke **swing/position trading dengan target ≥10%**, holding
period mingguan sampai bulanan. Ini berbeda karakter dari riset forex kemarin, dan sebaiknya
diterima sejak awal daripada ditemukan setelah 26 eksperimen.

Cek juga: banyak broker punya **minimum komisi** per transaksi (mis. Rp5.000–10.000), yang
membuat transaksi kecil jauh lebih mahal secara persentase.

## 4.3 Mekanika pasar IDX yang harus dimodelkan

| Aspek | Detail | Dampak ke backtest |
|---|---|---|
| **Lot** | 1 lot = 100 lembar | Position sizing harus bulat ke lot; saham mahal (mis. GGRM) bikin granularitas kasar untuk modal kecil |
| **Fraksi harga** | Tick size berjenjang menurut pita harga (Rp1 untuk <200, Rp2 untuk 200–500, Rp5 untuk 500–2000, dst) | SL/TP harus dibulatkan ke fraksi yang sah |
| **ARA / ARB** | Auto-rejection ±20–35% tergantung pita harga | Order bisa tidak tereksekusi saat gap besar — backtest naif akan terlalu optimistis |
| **Jam perdagangan** | Sesi I 09:00–12:00, Sesi II 13:30–15:49 WIB (Sen–Jum) | Data harian lebih aman; intraday perlu penanganan jeda |
| **Short selling** | Praktis tidak tersedia untuk retail | **Strategi harus long-only** — separuh logika riset forex (SELL) tidak berlaku |
| **Suspensi** | Saham bisa disuspend berhari-hari | Posisi terkunci; perlu dimodelkan atau minimal dicatat sebagai risiko |
| **Likuiditas** | Saham lapis 2–3 bisa sangat tipis | Slippage jauh lebih besar dari asumsi; batasi universe ke saham likuid |

## 4.4 Dimensi baru: pemilihan universe

Riset forex hanya punya 1 instrumen. Saham punya ~900 emiten — ini **dimensi kebebasan baru yang
sangat rawan overfitting.**

Bahayanya: memilih saham mana yang diuji, lalu melaporkan yang hasilnya bagus, adalah bentuk
data-mining yang jauh lebih parah daripada memilih parameter. Dengan 900 saham, akan selalu ada
puluhan yang "cocok" dengan strategi apapun murni karena kebetulan.

**Aturan yang disarankan:**
1. **Tentukan universe SEBELUM menguji apapun**, dengan kriteria objektif dan mekanis —
   misalnya: anggota indeks LQ45 atau IDX80 per tanggal tertentu, atau nilai transaksi harian
   rata-rata di atas ambang tertentu.
2. **Uji strategi di SELURUH universe sekaligus**, laporkan agregatnya. Jangan cherry-pick.
3. Kalau ingin tahu apakah strateginya cocok untuk saham tertentu, itu **pertanyaan terpisah**
   yang butuh brankas sendiri.
4. **Hati-hati survivorship bias** — universe hari ini tidak memuat emiten yang delisting atau
   yang dulu tidak likuid. Ini membuat hasil backtest terlalu optimistis. Kalau memungkinkan,
   gunakan komposisi indeks historis; kalau tidak, catat keterbatasan ini eksplisit.

## 4.5 Sumber data

| Sumber | Kelebihan | Kekurangan |
|---|---|---|
| **yfinance** (ticker `.JK`, mis. `BBCA.JK`) | gratis, mudah, OHLCV harian, sudah disesuaikan corporate action | kualitas bervariasi, tidak ada emiten delisting (survivorship bias), data intraday terbatas |
| **Stockbit** | data lengkap, ada skill [`stockbit-web`](../.claude/skills/) di setup ini | akses lewat browser, tidak dirancang untuk bulk historis |
| **IDX resmi** | otoritatif | format tidak ramah otomasi |
| **Broker/API berbayar** | kualitas terbaik | biaya |

**Rekomendasi untuk mulai:** yfinance untuk membangun dan memvalidasi metodologi (cepat, bisa
bulk download), dengan keterbatasan survivorship bias dicatat eksplisit di `SETUP.md`.

⚠️ **Wajib dicek di awal:** apakah harga sudah disesuaikan untuk **stock split dan dividen**.
Split yang tidak disesuaikan akan terlihat seperti crash 50% dan merusak semua indikator.
Verifikasi dengan memeriksa beberapa saham yang diketahui pernah split.

## 4.6 Rancangan harness awal yang disarankan

```
Universe    : anggota LQ45 (atau IDX80) — ditetapkan di awal, tidak diubah
Timeframe   : harian (D1)
Rentang     : eksplorasi 2019–2023  |  BRANKAS 2024–2026 (jangan disentuh)
              (atau sebaliknya — yang penting brankas ditetapkan SEBELUM mulai)
Arah        : long-only
Modal       : nominal tetap, mis. Rp100.000.000
Sizing      : risiko % per posisi, dibulatkan ke lot (100 lembar)
Biaya       : beli 0,20% + jual 0,30% (sesuaikan dengan broker riil)
Slippage    : minimal 1 fraksi harga; lebih untuk saham kurang likuid
Target      : ≥10% agar rasio biaya masuk akal (lihat 4.2)
```

Tulis ini ke `experiments/SETUP.md` dan **kunci** sebelum eksperimen pertama.

## 4.7 Ide strategi yang masuk akal untuk karakter IDX

Berdasarkan kendala biaya tinggi + long-only + data harian:

1. **Momentum / relative strength lintas saham** — peringkat saham berdasarkan return N bulan,
   pegang yang teratas, rebalance bulanan. Cocok karena frekuensi rendah dan target besar.
2. **Trend-following harian** — MA panjang, hanya long, keluar saat tren patah. Analog paling
   dekat dengan riset forex kemarin.
3. **Breakout dari konsolidasi panjang** — target besar, cocok dengan struktur biaya.
4. **Mean-reversion pada saham likuid** — hati-hati, di forex gagal total; dan target kecilnya
   berbenturan dengan biaya tinggi.

Prioritaskan (1) dan (2): keduanya berfrekuensi rendah dengan target besar, yang paling sesuai
dengan struktur biaya IDX.

## 4.8 Langkah pertama yang disarankan di sesi baru

1. Buat `sahamian/idx/experiments/SETUP.md`, isi harness dari 4.6, **kunci brankas**.
2. Tarik data universe via yfinance; **verifikasi penyesuaian split/dividen**.
3. Hitung statistik dasar universe: volatilitas harian rata-rata, rata-rata pergerakan bulanan.
4. **Hitung rasio biaya** (aturan 1.3) untuk beberapa kandidat target profit — putuskan target
   minimum yang realistis sebelum menulis strategi apapun.
5. Baru bangun strategi pertama (baseline sederhana), jalankan tangga validasi Bagian 2.2.

---

# Lampiran A — Kode yang bisa dipakai ulang

Dari [`../ian-skills/mt5-ea/quant-engine/`](../ian-skills/mt5-ea/quant-engine/):

| File | Transferable? |
|---|---|
| `qengine/stats.py` | ✅ **langsung pakai** — bootstrap, permutasi DD, tidak bergantung pasar |
| `qengine/engine.py` | ⚠️ arsitekturnya transferable; ganti model biaya (spread→komisi), sizing (lot forex→lot 100 lembar), hapus jalur SELL kalau long-only |
| `qengine/indicators.py` | ⚠️ berguna kalau ingin cocok dengan MT5; untuk saham lebih baik pakai pandas/pandas-ta biasa |
| `qengine/strategy.py` | ❌ spesifik EA forex |
| `run_bootstrap.py`, `run_walkforward.py`, `run_audit.py` | ✅ **pola analisisnya langsung transferable**, tinggal ganti sumber data |

Yang paling bernilai untuk disalin: **`stats.py` dan ketiga skrip analisis** — itu inti dari
kedisiplinan statistik yang dipelajari dengan mahal di riset ini.

# Lampiran B — Gotcha teknis (khusus MT5, abaikan untuk saham)

Disimpan untuk kelengkapan, tidak relevan untuk riset IDX:

- `CopyBuffer` dengan array biasa mengisi `arr[0]` = bar **tertua** — bukan terbaru. Ini yang
  membuat arah crossing terbalik tanpa disadari.
- ADX MT5 bukan ADX Wilder standar: normalisasi +DM/−DM terhadap TR per bar dulu, lalu smoothing
  EMA dengan alfa **2/(period+1)**, bukan 1/period.
- ATR MT5 memakai SMA dari True Range, bukan Wilder/RMA seperti ta-lib.
- Setelan "Max bars in chart" membatasi data yang terbaca Python API; Strategy Tester tidak
  terkena batas itu.
- Akun demo bisa expired diam-diam; server demo harus bernama "Trial", bukan "Real".
- pandas ≥3.0 mengembalikan array read-only dari `.to_numpy()` — pakai `copy=True`.
