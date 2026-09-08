# Eksperimen 002 — Walk-forward bergulir & sensitivitas parameter

Tahap 3 tangga validasi ([`METHODOLOGY.md` 2.2](../../../METHODOLOGY.md)), satu-satunya tahap
yang belum dilalui eksperimen 001.

Dijalankan **hanya di periode eksplorasi 2019–2023**. Rentang penuh ikut dihitung tapi ditandai
INFORMATIF: brankas sudah dibuka 2026-09-07, jadi angka di sana bukan uji independen lagi.

Kode: [`walkforward.py`](walkforward.py) · hasil mentah: [`results.json`](results.json)

## A. Walk-forward bergulir (latih 24 bln → uji 12 bln → geser)

| Jendela uji | Lookback dipilih dari data latih | Hasil "tuned" | Hasil patok 6 bulan |
|---|---:|---:|---:|
| 2021 | 9 bulan | +15,4% | +10,0% |
| 2022 | 9 bulan | +53,9% | +49,1% |
| 2023 | 9 bulan | −10,3% | +14,2% |
| **Total majemuk** | | **+59,3%** | **+87,3%** |

**3/3 jendela profitable untuk patokan tetap.** Sample-nya tipis (hanya 3 jendela — konsekuensi
periode eksplorasi 5 tahun), jadi ini bukti lemah soal stabilitas.

Rentang penuh (INFORMATIF, 5 jendela): tuned +342,5% vs patok +419,3%; jendela 2024 dan 2025
memilih lookback 2 bulan dari data latih dan tetap kalah dari patokan.

## B. Tuning per jendela KALAH dari patokan tetap

**Ini mereplikasi temuan forex ([`METHODOLOGY.md` 3.3](../../../METHODOLOGY.md)):**

| | Riset forex (EURUSD M15) | Riset ini (IDX LQ45) |
|---|---|---|
| Pilih parameter dari data latih | +1.179.046 | +59,3% |
| **Patok satu nilai tetap** | **+1.672.099** | **+87,3%** |

Mekanismenya terlihat jelas di jendela 2023: data latih 2021–2022 bilang lookback 9 bulan paling
bagus, lalu di 2023 lookback 9 menghasilkan −10,3% sementara patokan 6 bulan menghasilkan +14,2%.
Parameter yang menang di masa lalu bukan parameter yang akan menang berikutnya.

**Konsekuensi praktis: jangan sediakan fitur "auto-optimize" di aplikasi.** Lab backtest boleh
dipakai untuk memahami sensitivitas, bukan untuk memilih parameter tahun depan.

## C. Sensitivitas parameter — CAGR % (eksplorasi 2019–2023)

| lookback ↓ / jumlah saham → | 3 | 5 | 9 | 12 | 15 | 20 |
|---|---:|---:|---:|---:|---:|---:|
| 1 bulan | 11,7 | 10,9 | 9,8 | 10,4 | 10,9 | 12,2 |
| 2 bulan | −2,8 | 1,2 | 5,2 | 6,3 | 5,5 | 7,4 |
| 3 bulan | 1,2 | 3,7 | 1,8 | 2,5 | 0,7 | 1,4 |
| **6 bulan** | **43,1** | 21,7 | **16,3** | 12,0 | 12,1 | 8,2 |
| 9 bulan | 30,8 | 19,0 | 15,9 | 14,3 | 12,0 | 13,8 |
| 12 bulan | 13,1 | 18,0 | 16,3 | 11,4 | 12,6 | 10,1 |

Dua pola, dan keduanya penting:

**1. Sepanjang sumbu lookback permukaannya TIDAK datar** — 2–3 bulan gagal (CAGR 0–7%, PF
1,06–1,32) sementara 6–12 bulan bagus (CAGR 12–43%, PF 1,47–2,59). Awalnya ini terlihat seperti
tanda bahaya (konfigurasi terpilih tidak duduk di dataran datar). Tapi bentuknya justru cocok
dengan literatur momentum klasik: formasi 6–12 bulan bekerja, horizon pendek tidak. Jadi ini
**pola berstruktur ekonomi, bukan puncak acak** — meski tetap perlu dicatat bahwa kalau kita
kebetulan memilih lookback 3 bulan di awal, seluruh riset ini akan menyimpulkan "momentum tidak
bekerja di IDX".

**2. Sepanjang sumbu jumlah saham polanya mulus dan monoton** — makin sedikit saham makin tinggi
return (di lookback 6: 43,1 → 21,7 → 16,3 → 12,0 → 12,1 → 8,2). Ini persis yang diharapkan kalau
sinyalnya nyata: memegang 20 dari 44 saham berarti separuh universe, mendekati indeks.

## D. Konsentrasi — temuan yang paling menggoda dan paling berbahaya

| Konfigurasi | CAGR | PF | 95% CI PF | Return/bulan | 95% CI | DD p95 |
|---|---:|---:|---|---:|---|---:|
| lookback 6, top 3 | 43,1% | 2,59 | **[1,31 ; 5,61]** | +3,53% | [+0,95 ; +6,19] | 44,2% |
| lookback 9, top 3 | 30,8% | 2,12 | **[1,02 ; 4,49]** | +2,84% | [+0,08 ; +5,80] | 50,8% |
| **lookback 6, top 9 (default)** | 16,3% | 1,81 | [0,86 ; 4,11] | +1,56% | [−0,39 ; +3,55] | 45,2% |
| lookback 9, top 9 | 15,9% | 1,77 | [0,85 ; 3,78] | +1,51% | [−0,39 ; +3,49] | 42,6% |

Yang mencolok: **konfigurasi terkonsentrasi punya CI yang TIDAK menyentuh 1,0**, sementara
default menyentuh. Dan drawdown-nya tidak lebih buruk (44,2% vs 45,2%). Secara statistik,
memegang 3 saham teratas justru memberi bukti lebih kuat bahwa edge-nya nyata — masuk akal, karena
mengencerkan ke 9 saham berarti memasukkan nama-nama dengan momentum lemah.

**Kenapa ini TIDAK boleh langsung dipakai untuk pindah konfigurasi:**

1. Angka ini ditemukan dengan **menyisir 36 sel grid**. Dengan 36 percobaan, beberapa akan terlihat
   signifikan murni karena kebetulan — CI 95% per sel tidak dikoreksi untuk banyaknya perbandingan.
2. CI-nya **tumpang tindih lebar** dengan default ([1,31 ; 5,61] vs [0,86 ; 4,11]). Per aturan
   [2.4](../../../METHODOLOGY.md): jangan berpindah konfigurasi berdasarkan selisih yang tidak
   terbedakan.
3. Risiko yang tidak muncul di angka: 3 saham berarti **33% modal per emiten**. Kalau satu kena
   suspensi (METHODOLOGY 4.3), sepertiga portofolio terkunci. Backtest ini tidak memodelkan
   suspensi maupun slippage.
4. Brankas sudah terpakai, jadi tidak ada lagi periode bersih untuk mengujinya di data yang ada.

**Cara yang benar untuk menindaklanjuti**: catat sebagai hipotesis pra-terdaftar, tetapkan
brankas baru (mis. data 2027 ke depan, atau universe lain seperti IDX80 non-LQ45), lalu uji sekali.

## Verdict

- ✅ Tahap 3 terlewati untuk konfigurasi default: 3/3 jendela profitable dengan patokan tetap.
- ✅ Temuan forex "jangan tuning per periode" **tereplikasi di pasar yang sama sekali berbeda** —
  ini mungkin pelajaran paling transferable dari seluruh riset ini.
- ⚠️ Sample walk-forward tipis (3 jendela).
- ⚠️ Konfigurasi default kemungkinan **bukan yang terbaik** — arah konsentrasi terlihat lebih kuat,
  tapi buktinya belum layak dipakai untuk berpindah.
