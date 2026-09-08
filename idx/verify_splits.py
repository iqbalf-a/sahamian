"""Verifikasi adjustment: cek BBCA di sekitar stock split 1:5 (Juni 2021),
dan scan seluruh universe untuk lompatan harga >40% dalam 1 hari (indikasi split
yang TIDAK ter-adjust dengan benar)."""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

print("=== BBCA sekitar split 1:5 (2021-06-08 ish) ===")
bbca = pd.read_csv(DATA_DIR / "BBCA.csv", index_col=0, parse_dates=True)
window = bbca.loc["2021-05-25":"2021-06-15", ["Close"]]
print(window)
print()

print("=== Scan lompatan 1-hari > 40% (kandidat split yang tidak ter-adjust) ===")
any_found = False
for f in sorted(DATA_DIR.glob("*.csv")):
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    ret = df["Close"].pct_change()
    big = ret[ret.abs() > 0.40]
    if len(big) > 0:
        any_found = True
        print(f"{f.stem}:")
        for dt, r in big.items():
            print(f"  {dt.date()}  {r:+.1%}")
if not any_found:
    print("Tidak ada lompatan >40% di seluruh universe -- indikasi kuat adjustment sudah benar.")
