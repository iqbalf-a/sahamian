"""Tarik data harian LQ45 via yfinance, simpan ke cache parquet, verifikasi adjustment."""
import pandas as pd
import yfinance as yf
from pathlib import Path
import time

TICKERS = """AADI ADMR ADRO AKRA AMMN AMRT ANTM ASII BBCA BBNI BBRI BBTN BMRI BRPT BUMI CPIN
CUAN DEWA EMTK ESSA EXCL GOTO HRTA ICBP INCO INDF INDY INKP ISAT ITMG JPFA KLBF
MAPI MBMA MDKA MEDC PGAS PGEO PTBA SCMA TLKM UNTR UNVR WIFI""".split()

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

START = "2018-06-01"  # sedikit lebih awal dari 2019 untuk buffer indikator
END = "2026-09-08"

ok, failed = [], []
for t in TICKERS:
    sym = f"{t}.JK"
    out = DATA_DIR / f"{t}.csv"
    try:
        df = yf.download(sym, start=START, end=END, auto_adjust=True, progress=False)
        if df is None or df.empty or len(df) < 100:
            failed.append((t, "empty or too short"))
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index.name = "date"
        df.to_csv(out)
        ok.append((t, len(df), df.index.min().date(), df.index.max().date()))
    except Exception as e:
        failed.append((t, str(e)))
    time.sleep(0.3)

print(f"OK: {len(ok)}/{len(TICKERS)}")
for t, n, lo, hi in ok:
    print(f"  {t:6s} {n:5d} bars  {lo} -> {hi}")
if failed:
    print(f"\nGAGAL: {len(failed)}")
    for t, msg in failed:
        print(f"  {t}: {msg}")
