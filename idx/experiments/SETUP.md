# SETUP — Harness Riset IDX (DIKUNCI)

Ditetapkan **sebelum** eksperimen pertama, mengikuti [`METHODOLOGY.md` Bagian 4.6](../../METHODOLOGY.md).
Jangan diubah setelah eksperimen dimulai — kalau ada kebutuhan berubah, catat sebagai
eksperimen baru dengan alasannya, jangan timpa file ini secara diam-diam.

Dibuat: 2026-09-07.

## Universe

**LQ45, komposisi periode Agustus–Oktober 2026** (44 ticker, diambil dari Wikipedia yang
mengutip data BEI terbaru saat riset ini dimulai):

```
AADI ADMR ADRO AKRA AMMN AMRT ANTM ASII BBCA BBNI BBRI BBTN BMRI BRPT BUMI CPIN
CUAN DEWA EMTK ESSA EXCL GOTO HRTA ICBP INCO INDF INDY INKP ISAT ITMG JPFA KLBF
MAPI MBMA MDKA MEDC PGAS PGEO PTBA SCMA TLKM UNTR UNVR WIFI
```

⚠️ **Survivorship bias, dicatat eksplisit (sesuai 4.4 poin 4):** ini komposisi LQ45 **hari
ini**, dipakai mundur ke 2019. Emiten yang delisting, atau yang dulu tidak cukup likuid untuk
masuk LQ45 tapi sekarang masuk (mis. AADI, CUAN, MBMA — baru IPO/listing setelah 2019), akan
punya data historis pendek atau tidak representatif untuk periode awal. Ini **bukan** komposisi
historis LQ45 yang sebenarnya berlaku di tiap tahun — itu keterbatasan yang disengaja diterima
demi kecepatan (rekomendasi 4.5), bukan diabaikan.

## Timeframe

Harian (D1), harga **adjusted close** (yfinance `auto_adjust=True` — sudah menyesuaikan split
dan dividen).

## Rentang & Brankas

```
Eksplorasi : 2019-01-01 s/d 2023-12-31   <- boleh dilihat, dites, dituning
BRANKAS    : 2024-01-01 s/d 2026-09-07   <- TIDAK DISENTUH sampai kandidat final terpilih
```

## Arah

**Long-only** — short selling praktis tidak tersedia untuk retail IDX (4.3).

## Modal & Sizing

- Modal nominal tetap: **Rp100.000.000**
- Sizing: alokasi % per posisi, dibulatkan ke bawah ke kelipatan 1 lot (100 lembar)

## Model Biaya (broker retail tipikal)

```
Beli  : 0,20%
Jual  : 0,30%  (termasuk pajak final 0,1%)
Bolak-balik: ~0,50%
```

## Slippage

Minimal 1 fraksi harga (tick size) per sisi, dinaikkan untuk saham kurang likuid kalau
diperlukan (belum dimodelkan di eksperimen pertama — dicatat sebagai keterbatasan).

## Target

Sesuai rasio biaya (aturan 1.3): dengan biaya bolak-balik 0,5%, target **≥10%** per posisi
agar rasio biaya tetap di bawah ~5%.

## Struktur file

```
sahamian/idx/
  experiments/
    SETUP.md       <- file ini
    INDEX.md       <- log eksperimen (dibuat berikutnya)
    NNN_nama/
  data/            <- cache OHLCV per ticker (parquet/csv)
```
