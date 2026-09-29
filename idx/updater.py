"""
Pembaruan data harga + status kesegarannya.

Dipakai oleh tombol "Perbarui" di aplikasi. Berbeda dari `download_data.py` /
`download_extra.py` yang untuk setup awal, modul ini menyegarkan **apa pun yang sudah ada**
di `data/` — termasuk saham yang ditambahkan user sendiri — dan melaporkan progresnya
supaya UI bisa menampilkan status.
"""
from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

import engine
import market

START = "2018-06-01"

_state = {
    "running": False,
    "done": 0,
    "total": 0,
    "current": None,
    "error": None,
    "finished_at": None,
    "updated": 0,
}
_lock = threading.Lock()


# ------------------------------------------------------------------ kesegaran data

def _expected_last_trading_day(now: datetime | None = None) -> date:
    """Hari bursa terakhir yang datanya WAJAR sudah ada.

    IDX tutup jam 15:49 WIB. Sebelum sore, data hari ini belum tentu final, jadi acuannya
    hari bursa sebelumnya. Hari libur nasional tidak diketahui modul ini — itu sebabnya
    UI menyebut "terakhir diperbarui", bukan mengklaim data pasti tertinggal.
    """
    now = now or datetime.now()
    d = now.date()
    if now.hour < 17:
        d -= timedelta(days=1)
    while d.weekday() >= 5:            # 5=Sabtu, 6=Minggu
        d -= timedelta(days=1)
    return d


def freshness() -> dict:
    """Seberapa lama data yang tersimpan, dibanding hari bursa terakhir yang diharapkan."""
    latest = None
    for t in engine.available_tickers():
        df = engine.load_prices(t)
        if df is not None and len(df):
            d = df.index[-1].date()
            if latest is None or d > latest:
                latest = d

    idx = market.load_index()
    if idx is not None and len(idx):
        d = idx.index[-1].date()
        if latest is None or d > latest:
            latest = d

    if latest is None:
        return {"has_data": False, "stale": True, "message": "Belum ada data sama sekali."}

    expected = _expected_last_trading_day()
    behind = 0
    cur = expected
    while cur > latest:                # hitung selisih dalam hari BURSA, bukan kalender
        if cur.weekday() < 5:
            behind += 1
        cur -= timedelta(days=1)

    calendar_days = (date.today() - latest).days
    return {
        "has_data": True,
        "last_date": latest.isoformat(),
        "expected_last_trading_day": expected.isoformat(),
        "trading_days_behind": behind,
        "calendar_days_ago": calendar_days,
        "stale": behind >= 1,
        "tickers": len(engine.available_tickers()),
    }


# ------------------------------------------------------------------- proses update

def status() -> dict:
    with _lock:
        return dict(_state)


def _refresh_all() -> None:
    import yfinance as yf

    tickers = engine.available_tickers()
    with _lock:
        _state.update(running=True, done=0, total=len(tickers) + 1, current=None,
                      error=None, finished_at=None, updated=0)

    updated = 0
    try:
        # indeks IHSG dulu — paling cepat terlihat di UI
        with _lock:
            _state["current"] = "IHSG"
        try:
            idx = yf.download("^JKSE", start=START, auto_adjust=True, progress=False)
            if idx is not None and not idx.empty:
                if isinstance(idx.columns, pd.MultiIndex):
                    idx.columns = idx.columns.get_level_values(0)
                idx.index.name = "date"
                market.INDEX_DIR.mkdir(exist_ok=True)
                idx.to_csv(market.INDEX_DIR / "IHSG.csv")
                updated += 1
        except Exception:
            pass
        with _lock:
            _state["done"] = 1

        for i, t in enumerate(tickers, start=1):
            with _lock:
                _state["current"] = t
            try:
                df = yf.download(f"{t}.JK", start=START, auto_adjust=True, progress=False)
                if df is not None and not df.empty and len(df) >= 60:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df.index.name = "date"
                    df.to_csv(engine.DATA_DIR / f"{t}.csv")
                    updated += 1
            except Exception:
                pass                    # satu ticker gagal tidak boleh menggagalkan semuanya
            with _lock:
                _state["done"] = i + 1
                _state["updated"] = updated
            time.sleep(0.15)

    except Exception as e:
        with _lock:
            _state["error"] = f"{type(e).__name__}: {e}"
    finally:
        # bersihkan cache in-memory supaya data baru langsung terpakai
        engine._names_cache = engine._names_cache
        with _lock:
            _state.update(running=False, current=None, updated=updated,
                          finished_at=datetime.now().isoformat(timespec="seconds"))


def start_update() -> dict:
    with _lock:
        if _state["running"]:
            return {"started": False, "reason": "Pembaruan sedang berjalan.", **_state}
    threading.Thread(target=_refresh_all, daemon=True).start()
    time.sleep(0.2)
    return {"started": True, **status()}
