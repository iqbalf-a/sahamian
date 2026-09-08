# Analisis Saham IDX — Aplikasi & Riset Kuantitatif

Aplikasi analisis saham Indonesia (screener, chart, backtest, kalender) yang dibangun di atas
riset kuantitatif yang metodologinya diwarisi dari riset EA forex sebelumnya.

Yang membedakan proyek ini dari kebanyakan alat screener: **setiap strategi di sini sudah
di-backtest, dan yang gagal tetap ditampilkan beserta angka kegagalannya.** Dari tujuh template
screener, hanya satu yang terbukti mengalahkan beli-tahan pasif.

---

## Cara menjalankan

Aplikasi ini butuh **dua server berjalan bersamaan**, jadi siapkan **dua jendela terminal**
(Command Prompt atau PowerShell — perintah di bawah sama untuk keduanya).

> ⚠️ **Gunakan backslash `\`, bukan garis miring `/`.** Command Prompt akan menolak
> `.venv/Scripts/python.exe` dengan pesan `'.venv' is not recognized as an internal or
> external command`.

### Terminal 1 — Backend (port 8000)

**Langkah 1.** Masuk ke folder `idx`:

```
cd D:\github-repos\quant-research\idx
```

**Langkah 2.** Jalankan server:

```
.venv\Scripts\python.exe -m uvicorn app.server:api --port 8000 --reload
```

**Langkah 3.** Tunggu sampai muncul baris ini:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Biarkan jendela ini terbuka. Kalau ditutup, aplikasi berhenti bekerja.

### Terminal 2 — Frontend (port 5173)

**Langkah 4.** Buka jendela terminal **baru**, masuk ke folder `dashboard`:

```
cd D:\github-repos\quant-research\idx\dashboard
```

**Langkah 5.** Jalankan:

```
npm run dev
```

**Langkah 6.** Tunggu sampai muncul:

```
  VITE v8.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

### Terminal 3 — tidak perlu

**Langkah 7.** Buka browser ke **http://localhost:5173**

Selesai. Untuk menghentikan: tekan `Ctrl + C` di masing-masing jendela terminal.

> Kalau memakai Claude Code, kedua server sudah terdaftar di `.claude/launch.json` sebagai
> `idx-api` dan `idx-app`, jadi bisa dijalankan lewat preview tanpa mengetik apapun.

---

## Kalau muncul error

### `'.venv' is not recognized as an internal or external command`

Anda memakai garis miring `/` di Command Prompt. Ganti jadi backslash:

| ❌ Salah | ✅ Benar |
|---|---|
| `.venv/Scripts/python.exe` | `.venv\Scripts\python.exe` |

### `[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`

Port 8000 **sudah dipakai program lain** — biasanya server yang belum ditutup dari percobaan
sebelumnya. Cari dan hentikan prosesnya lewat PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object {
  Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" |
    Select-Object ProcessId, Name, CommandLine
}
```

Setelah tahu PID-nya dan yakin itu memang server lama Anda:

```powershell
Stop-Process -Id <PID> -Force
```

Atau pakai port lain: ganti `--port 8000` jadi `--port 8001`, lalu ubah juga tujuan proxy di
`idx/dashboard/vite.config.js` agar menunjuk ke port yang sama.

### `Failed to fetch` / halaman kosong / tabel tidak terisi

Backend belum jalan atau sudah mati. Cek Terminal 1 masih hidup, lalu buka
**http://localhost:8000/api/health** di browser — harusnya muncul `{"ok":true,"tickers":82}`.

### `python` atau `npm` tidak dikenali

Belum terpasang atau belum masuk PATH. Pasang [Python 3.11+](https://www.python.org/downloads/)
(centang **Add Python to PATH** saat memasang) dan [Node.js](https://nodejs.org/).

---

## Setup pertama kali (kalau `.venv` atau `node_modules` belum ada)

Jalankan berurutan dari Command Prompt:

```
cd D:\github-repos\quant-research\idx
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Lalu tarik datanya (butuh beberapa menit, perlu koneksi internet):

```
.venv\Scripts\python.exe download_data.py
.venv\Scripts\python.exe download_extra.py
.venv\Scripts\python.exe build_ticker_names.py
```

Terakhir, dependensi frontend:

```
cd dashboard
npm install
```

Setelah itu kembali ke bagian **Cara menjalankan** di atas.

### Memperbarui data harga

Data harga tersimpan sebagai CSV dan **tidak** ikut diperbarui otomatis. Kapan pun ingin data
terbaru, hentikan server lalu jalankan ulang:

```
cd D:\github-repos\quant-research\idx
.venv\Scripts\python.exe download_data.py
.venv\Scripts\python.exe download_extra.py
```

---

## Isi aplikasi

| Tab | Isi |
|---|---|
| **Utama** | IHSG, deteksi pergerakan tidak wajar + berita terkait, dan daftar top gainer / loser / trending / teraktif / dekat tertinggi–terendah 52 minggu |
| **Screener** | 7 template strategi, masing-masing dengan status hasil ujinya |
| **Kalender** | Heatmap untung-rugi harian, per halaman 2 bulan. Default IHSG, bisa diganti ke saham manapun |
| **Lab backtest** | Backtest strategi momentum dengan parameter yang bisa diatur |
| **Sensitivitas** | Walk-forward bergulir + grid 36 kombinasi parameter |
| **Riset** | Laporan lengkap eksperimen 001 |

**Detail saham** dibuka dengan mengklik baris tabel atau lewat kotak pencarian di kanan atas
(bisa cari dengan kode **atau** nama perusahaan — ketik "bank" atau "asuransi"). Isinya: panel
ringkasan, chart garis/candle dengan SMA20/50/200 + RSI (bisa diperbesar), penilaian terhadap
kriteria strategi, kelayakan target profit di harga sekarang, dan corporate action.

Saham di luar 82 yang tersimpan bisa ditarik langsung dari aplikasi — pilih dari hasil
pencarian, datanya otomatis diambil dari yfinance.

---

## Status tiap strategi

| Template | Status | Angka |
|---|---|---|
| Momentum lintas saham | ✅ tervalidasi sebagian | CAGR +16,3% vs buy&hold +8,8% (2019–2023) |
| Beli sore → jual pagi | ❌ gagal: biaya | efek kotor nyata (+0,27%/hari) tapi 0 dari 44 saham bersihnya positif |
| Beli pagi → jual sore | ❌ gagal: sinyal | −0,17%/hari bahkan sebelum biaya |
| Akumulasi (proxy bandarmology) | ❌ gagal: backtest | +1,6%, PF 1,17 |
| Breakout konsolidasi | ❌ gagal: backtest | −5,7%, PF 0,83 |
| Trend-following | ❌ gagal: backtest | −1,9%, PF 1,05 |
| Koreksi dalam tren naik | ❌ gagal: backtest | −0,4%, win rate bulanan 35% |

Detail pengujiannya di [`idx/experiments/`](idx/experiments/INDEX.md).

⚠️ Bahkan strategi momentum **belum layak dipakai dengan uang sungguhan**: drawdown persentil 95
mencapai 57%, dan tahun 2026 turun −40,1% setelah 2025 naik +138,6%. Belum pernah dijalankan di
akun nyata.

---

## Fitur AI (opsional, perlu kunci API)

Panel di tab Utama mendeteksi saham yang bergerak >2 simpangan baku dari volatilitasnya sendiri,
lalu mencocokkannya dengan judul berita dari RSS (CNBC Indonesia, Kontan, IDX Channel). Bagian
statistik dan berita **selalu jalan tanpa kunci apapun**.

Analisis AI-nya opsional. Untuk mengaktifkan:

```bash
export ANTHROPIC_API_KEY=sk-ant-...    # atau set di Windows: setx ANTHROPIC_API_KEY "sk-ant-..."
```

lalu jalankan ulang server API. Prompt-nya dikunci agar model **hanya** memakai judul berita yang
benar-benar diambil, dan wajib menyatakan "tidak ada berita yang menjelaskan" kalau tidak ketemu —
bukan mengarang sebab.

---

## Struktur folder

```
quant-research/
├── README.md              file ini
├── METHODOLOGY.md         metodologi riset — baca Bagian 1 & 4 kalau waktunya terbatas
├── FINDINGS.md            hasil lengkap riset forex yang jadi asal metodologinya
├── reusable/stats.py      bootstrap CI & permutasi drawdown (tidak bergantung pasar)
└── idx/
    ├── engine.py          indikator, backtest momentum, peringkat universe
    ├── screeners.py       7 template screener
    ├── market.py          daftar Utama, kalender, corporate action
    ├── news.py            deteksi pergerakan tak wajar, RSS berita, analisis AI
    ├── stats.py           salinan reusable/stats.py + fungsi berbasis return
    ├── app/server.py      backend FastAPI
    ├── dashboard/         frontend React + Vite + Recharts
    ├── data/              82 CSV harga harian (LQ45 + IDX80)
    ├── data_index/        IHSG
    └── experiments/       INDEX.md + eksperimen 001–003
```

**Baca [`idx/experiments/INDEX.md`](idx/experiments/INDEX.md) duluan** kalau ingin melanjutkan
risetnya — di situ ada daftar temuan, apa yang sudah diuji, dan apa yang belum.

---

## Catatan penting soal data

- Sumber: yfinance (ticker `.JK`), harga sudah disesuaikan split & dividen — terverifikasi bersih
  (tidak ada lompatan >40% di seluruh universe; BBCA dicek manual di tanggal split 2021-10-13).
- **Survivorship bias belum dikoreksi**: universe memakai komposisi LQ45 hari ini yang dipakai
  mundur sampai 2019. Emiten yang delisting tidak ada di sini.
- Daftar top gainer/loser dihitung dari 82 saham yang datanya tersimpan, **bukan** dari seluruh
  ~900 emiten IDX — jadi bukan top gainer bursa yang sesungguhnya.
- Backtest belum memodelkan suspensi saham maupun slippage.

---

## Riset asal (forex)

Metodologi proyek ini berasal dari riset EA MetaTrader 5 (EURUSDm M15, 32 eksperimen) yang
filenya ada di repo sebelah:

- [`../ian-skills/mt5-ea/experiments/INDEX.md`](../ian-skills/mt5-ea/experiments/INDEX.md) — 41 temuan bernomor
- [`../ian-skills/mt5-ea/quant-engine/`](../ian-skills/mt5-ea/quant-engine/) — engine backtest + analisis

Status riset forex: kandidat final PF ~1,73 (8 tahun, CI [1,05–2,49]), win rate ~59%, drawdown
perencanaan ~7%. **Belum pernah forward test di akun live.** Akun demo: 463928352 @
Exness-MT5Trial17.

Satu temuan dari riset itu **tereplikasi di saham IDX**: memilih parameter dari data masa lalu
justru kalah dari mematoknya tetap (+59,3% vs +87,3%). Itu sebabnya aplikasi ini sengaja tidak
punya tombol "auto-optimize".

---

Bukan rekomendasi investasi. Semua angka di sini hasil backtest, dan backtest bukan masa depan.
