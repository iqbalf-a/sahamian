"""Bangun cache nama emiten untuk saham yang datanya ada di data/.

Nama diambil dari yfinance (otoritatif), bukan diketik manual — salah nama perusahaan di
aplikasi finansial bisa membuat orang menganalisis saham yang salah.
"""
import json
import time
from pathlib import Path

import yfinance as yf

DATA_DIR = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "ticker_names.json"

existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
tickers = sorted(p.stem for p in DATA_DIR.glob("*.csv"))

for t in tickers:
    if t in existing:
        continue
    try:
        info = yf.Ticker(f"{t}.JK").info
        name = info.get("longName") or info.get("shortName")
        if name:
            existing[t] = {"name": name, "sector": info.get("sector")}
            print(f"  {t:6s} {name}")
        else:
            print(f"  {t:6s} (nama tidak ditemukan)")
    except Exception as e:
        print(f"  {t:6s} error: {type(e).__name__}")
    time.sleep(0.4)

OUT.write_text(json.dumps(existing, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\n{len(existing)} nama tersimpan di {OUT}")
