"""Tarik anggota IDX80 yang belum ada + data indeks IHSG.

Saham ini masuk sebagai `extra_tickers()` — dipakai untuk daftar Utama (top gainer/loser/
trending) dan analisis per saham, TAPI TIDAK masuk universe riset yang dikunci di SETUP.md.
"""
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

import engine

IDX80 = """AADI ACES ADMR ADRO AKRA AMMN AMRT ANTM ARTO ASII BBCA BBNI BBRI BBTN BFIN BKSL
BMRI BRMS BRPT BSDE BUKA BUMI CBDK CMRY CPIN CTRA CUAN DEWA DSNG ELSA EMTK ENRG ERAA ESSA
EXCL GGRM GOTO HEAL HRTA HRUM ICBP INCO INDF INDY INKP ISAT ITMG JPFA JSMR KIJA KLBF KPIG
LSIP MAPA MAPI MBMA MDKA MEDC MIKA MYOR NCKL PGAS PGEO PNLF PTBA PTRO PWON RAJA RATU SCMA
SMGR SMRA SSIA TAPG TLKM TOWR TPIA UNTR UNVR WIFI""".split()

DATA_DIR = Path(__file__).parent / "data"
INDEX_DIR = Path(__file__).parent / "data_index"
INDEX_DIR.mkdir(exist_ok=True)
START, END = "2018-06-01", "2026-09-08"


def save(df: pd.DataFrame, path: Path) -> None:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index.name = "date"
    df.to_csv(path)


print("=== Indeks IHSG ===")
idx = yf.download("^JKSE", start=START, end=END, auto_adjust=True, progress=False)
save(idx, INDEX_DIR / "IHSG.csv")
print(f"  IHSG {len(idx)} bar {idx.index.min().date()} -> {idx.index.max().date()}")

have = set(engine.available_tickers())
todo = [t for t in IDX80 if t not in have]
print(f"\n=== {len(todo)} saham IDX80 belum ada, menarik ===")
ok, fail = 0, []
for t in todo:
    try:
        df = yf.download(f"{t}.JK", start=START, end=END, auto_adjust=True, progress=False)
        if df is None or df.empty or len(df) < 60:
            fail.append(t)
            continue
        save(df, DATA_DIR / f"{t}.csv")
        ok += 1
        print(f"  {t:6s} {len(df):5d} bar")
    except Exception as e:
        fail.append(f"{t} ({type(e).__name__})")
    time.sleep(0.3)

print(f"\nberhasil {ok}, gagal {len(fail)}: {fail}")
