# Eksperimen 003 — Validasi semua template screener

Menjawab satu pertanyaan: dari enam template screener di aplikasi, **mana yang benar-benar
menghasilkan uang?** Sebelumnya empat di antaranya berstatus "belum diuji" — status yang
menyesatkan, karena layar screener yang kelihatan meyakinkan mudah disangka sinyal.

Kode: [`backtest_templates.py`](backtest_templates.py) · hasil: [`results.json`](results.json)

## Cara menguji

Tiap template diubah jadi strategi portofolio yang **persis sebanding** dengan eksperimen 001:
long-only, rebalance bulanan, pegang top-9 skor tertinggi, equal weight, biaya 0,20%/0,30%.
Dengan mekanika yang sama, perbedaan hasil hanya bisa datang dari kualitas sinyalnya.

Template `overnight` dan `intraday` tidak diikutkan karena berpindah posisi harian — sudah
dinilai terpisah di screener (temuan 9 INDEX.md) dan gagal oleh biaya.

## Hasil — periode eksplorasi 2019–2023

| Template | CAGR | PF | 95% CI PF | P(PF>1) | Win rate | DD p95 | Rata² pegang |
|---|---:|---:|---|---:|---:|---:|---:|
| **momentum** | **+16,3%** | **1,81** | [0,86 ; 4,13] | 94% | 53,3% | 45,2% | 8,5 |
| *buy&hold equal-weight* | *+8,8%* | *1,48* | — | — | *57,6%* | — | *36* |
| akumulasi (proxy bandarmology) | +1,6% | 1,17 | [0,56 ; 2,43] | 67% | 48,3% | 53,4% | 8,4 |
| pullback | −0,4% | 1,10 | [0,48 ; 2,45] | 59% | 35,0% | 56,4% | 3,0 |
| trend-following | −1,9% | 1,05 | [0,51 ; 2,16] | 55% | 45,0% | 59,7% | 6,9 |
| breakout | −5,7% | 0,83 | [0,37 ; 1,74] | 31% | 33,3% | 52,8% | 2,9 |

**Empat-empatnya gagal.** Tidak satupun mengalahkan buy&hold pasif (+8,8%), dan tiga di
antaranya rugi. Hanya momentum yang lolos.

## Yang menarik dari kegagalannya

**Breakout paling buruk (PF 0,83) — dan ini sudah diramalkan.** Riset forex sebelumnya menguji
14 konfigurasi breakout dan PF terbaiknya cuma 0,91. Dua pasar yang sama sekali berbeda,
kesimpulan yang sama. Ini menaikkan kepercayaan bahwa kegagalan breakout bersifat struktural,
bukan kebetulan periode.

**Trend-following gagal padahal paling "masuk akal".** Beli saham yang di atas SMA50 dan SMA200
dengan tren menguat terdengar seperti definisi investasi yang waras — hasilnya −1,9%. Ini
pengingat langsung ke METHODOLOGY 1.4: arah yang terasa logis bukan bukti apa-apa sebelum diuji.

**Proxy bandarmology tidak punya edge (+1,6%, PF 1,17, CI menyentuh nol).** Perlu ditekankan
apa yang ini uji dan apa yang tidak: yang diuji adalah *jejak* akumulasi di OHLCV (lonjakan
volume, harga menutup dekat tertinggi, arah OBV). Bandarmology sungguhan memakai broker summary
dan net foreign flow, yang tidak tersedia di yfinance. Jadi kesimpulan yang sah adalah
**"jejak akumulasi di data harga tidak cukup"**, bukan "bandarmology tidak bekerja".

**Momentum menang justru karena paling sedikit strukturnya.** Ia tidak memakai indikator apapun —
hanya peringkat return 6 bulan. Empat template yang kalah semuanya memakai lebih banyak
indikator (SMA, RSI, OBV, volume).

## Brankas 2024–2026 (INFORMATIF — sudah terpakai 2026-09-07)

| Template | CAGR | PF | Win rate |
|---|---:|---:|---:|
| breakout | +36,3% | 2,42 | 45,5% |
| *buy&hold* | *+24,9%* | *2,04* | *75,0%* |
| momentum | +21,3% | 1,82 | 66,7% |
| trend | +17,5% | 1,71 | 63,6% |
| akumulasi | +12,8% | 1,69 | 63,6% |
| pullback | −11,0% | 0,90 | 45,5% |

Di sini breakout justru terlihat terbaik (+36,3%). **Jangan tergoda.** CI-nya [0,59 ; 8,63] —
selebar itu artinya tidak ada informasi; rata-rata cuma memegang 2,4 saham; dan periode ini
sudah tidak independen. Membalik kesimpulan berdasarkan 33 bulan di periode yang sudah terpakai
adalah persis kesalahan yang METHODOLOGY 1.1 peringatkan. Kalau breakout mau dihidupkan lagi,
jalurnya adalah brankas baru, bukan angka ini.

## Verdict

| Template | Status baru di aplikasi |
|---|---|
| momentum | tervalidasi sebagian |
| overnight | gagal: biaya |
| intraday | gagal: sinyal |
| akumulasi, breakout, trend, pullback | gagal: backtest |

Keempat template yang gagal **tetap ditampilkan di aplikasi**, lengkap dengan angka
kegagalannya. Menghapusnya akan menyembunyikan pelajaran yang paling mahal: layar screener
yang rapi dan masuk akal tidak berarti apa-apa sampai diuji.
