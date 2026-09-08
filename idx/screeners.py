"""
Template screener untuk aplikasi analisis saham IDX.

Setiap template mengembalikan bentuk yang sama — {columns, rows, summary, warning} — supaya
frontend bisa merender tabel apapun tanpa tahu isi templatenya.

⚠️ Semua template di sini dihitung dari OHLCV harian. Tidak ada satupun yang sudah lolos
validasi seperti eksperimen 001; ini alat eksplorasi, bukan sinyal tervalidasi. Yang punya
masalah struktural (biaya, ketiadaan data) membawa `warning` sendiri yang ditampilkan di UI.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import engine

COST_BUY = 0.0020
COST_SELL = 0.0030


def _col(key, label, fmt="num", align="right", good=None, digits=2, hint=None):
    return {"key": key, "label": label, "format": fmt, "align": align,
            "good": good, "digits": digits, "hint": hint}


def _frames(min_bars: int = 260):
    for t in engine.universe_tickers():
        df = engine.load_prices(t)
        if df is not None and len(df) >= min_bars:
            yield t, df


# ---------------------------------------------------------------- sesi perdagangan

def _session(kind: str, days: int = 504, slippage_ticks: int = 1) -> dict:
    """kind='overnight' (beli sore jual pagi) atau 'intraday' (beli pagi jual sore)."""
    rows = []
    for t, df in _frames():
        d = df.tail(days + 1)
        if kind == "overnight":
            r = (d["Open"] / d["Close"].shift(1) - 1).dropna()
        else:
            r = (d["Close"] / d["Open"] - 1).dropna()
        if len(r) < 100:
            continue

        price = float(d["Close"].iloc[-1])
        slip_pct = slippage_ticks * engine.tick_size(price) / price
        net = (1 + r) * (1 - COST_SELL) / (1 + COST_BUY) - 1 - 2 * slip_pct

        n = len(r)
        gross_annual = (float(np.prod(1 + r.values)) ** (252 / n) - 1) * 100
        net_annual = (max(float(np.prod(1 + net.values)), 1e-12) ** (252 / n) - 1) * 100
        mean_gross = float(r.mean()) * 100

        rows.append({
            "ticker": t,
            "price": round(price, 2),
            "n_days": n,
            "mean_gross_pct": round(mean_gross, 3),
            "win_rate_pct": round(float((r > 0).mean()) * 100, 1),
            "gross_annual_pct": round(gross_annual, 1),
            "mean_net_pct": round(float(net.mean()) * 100, 3),
            "net_annual_pct": round(max(net_annual, -99.9), 1),
            "friction_pct": round((COST_BUY + COST_SELL + 2 * slip_pct) * 100, 2),
            "signal": False,
        })

    rows.sort(key=lambda x: -x["mean_gross_pct"])
    for r_ in rows:
        r_["signal"] = r_["mean_net_pct"] > 0

    mean_g = float(np.mean([r["mean_gross_pct"] for r in rows])) if rows else 0.0
    mean_n = float(np.mean([r["mean_net_pct"] for r in rows])) if rows else 0.0
    n_pos = sum(1 for r in rows if r["mean_net_pct"] > 0)

    label = "beli sore (closing) → jual pagi (opening)" if kind == "overnight" \
        else "beli pagi (opening) → jual sore (closing)"

    return {
        "columns": [
            _col("ticker", "Saham", "ticker", "left"),
            _col("price", "Harga", "price"),
            _col("mean_gross_pct", "Rata² kotor/hari", "pct", digits=3, good="high"),
            _col("win_rate_pct", "Win rate", "pct", digits=1, good="high"),
            _col("gross_annual_pct", "Kotor setahun", "pct", digits=1, good="high"),
            _col("friction_pct", "Biaya+slippage", "pct", digits=2, good="low",
                 hint="komisi 0,5% + 1 fraksi harga tiap sisi"),
            _col("mean_net_pct", "Rata² bersih/hari", "pct", digits=3, good="high"),
            _col("net_annual_pct", "Bersih setahun", "pct", digits=1, good="high"),
        ],
        "rows": rows,
        "summary": {
            "Rata² kotor/hari (universe)": f"{mean_g:+.3f}%",
            "Rata² bersih/hari (universe)": f"{mean_n:+.3f}%",
            "Saham dengan hasil bersih positif": f"{n_pos} dari {len(rows)}",
            "Periode": f"{days} hari bursa terakhir",
        },
        "warning": (
            f"Strategi ini ({label}) berpindah posisi SETIAP HARI, jadi biaya transaksi "
            f"~0,5% bolak-balik ditambah slippage 1 fraksi harga tiap sisi dikenakan {252} kali "
            f"setahun. Rata-rata efek kotornya {mean_g:+.3f}%/hari, sementara ongkosnya "
            f"jauh lebih besar — persis kasus yang diperingatkan METHODOLOGY 1.3 dan 4.2. "
            f"Kolom 'kotor' berguna untuk melihat apakah polanya nyata; kolom 'bersih' "
            f"menunjukkan apa yang benar-benar sampai ke rekening."
        ),
    }


def overnight(**kw) -> dict:
    return _session("overnight", **kw)


def intraday(**kw) -> dict:
    return _session("intraday", **kw)


# ------------------------------------------------------- akumulasi (proxy bandarmology)

def akumulasi(**_) -> dict:
    rows = []
    for t, df in _frames():
        d = df.tail(120)
        vol5 = float(d["Volume"].tail(5).mean())
        vol60 = float(d["Volume"].tail(60).mean())
        if vol60 <= 0:
            continue
        rng = (d["High"] - d["Low"]).replace(0, np.nan)
        close_pos = float(((d["Close"] - d["Low"]) / rng).tail(5).mean(skipna=True) * 100)

        direction = np.sign(d["Close"].diff().fillna(0.0))
        obv = (direction * d["Volume"]).cumsum()
        obv_slope = float((obv.iloc[-1] - obv.iloc[-21]) / (d["Volume"].tail(20).mean() * 20)) * 100

        price = float(d["Close"].iloc[-1])
        rows.append({
            "ticker": t,
            "price": round(price, 2),
            "vol_ratio": round(vol5 / vol60, 2),
            "close_pos_pct": round(close_pos, 1) if not np.isnan(close_pos) else None,
            "obv_slope_pct": round(obv_slope, 1),
            "ret_5d_pct": round(float(d["Close"].iloc[-1] / d["Close"].iloc[-6] - 1) * 100, 1),
            "value_bn": round(float((d["Close"] * d["Volume"]).tail(20).mean() / 1e9), 2),
            "signal": False,
        })

    for key in ["vol_ratio", "close_pos_pct", "obv_slope_pct"]:
        vals = [r[key] for r in rows if r[key] is not None]
        order = {v: i for i, v in enumerate(sorted(vals))}
        for r_ in rows:
            r_.setdefault("_score", 0.0)
            if r_[key] is not None:
                r_["_score"] += order[r_[key]] / max(len(order) - 1, 1)

    rows.sort(key=lambda x: -x.get("_score", 0))
    for i, r_ in enumerate(rows):
        r_["signal"] = i < 10
        r_.pop("_score", None)

    return {
        "columns": [
            _col("ticker", "Saham", "ticker", "left"),
            _col("price", "Harga", "price"),
            _col("vol_ratio", "Volume 5h / 60h", "ratio", digits=2, good="high",
                 hint="lonjakan volume dibanding rata-rata 3 bulan"),
            _col("close_pos_pct", "Tutup di kisaran", "pct", digits=0, good="high",
                 hint="100% = selalu tutup di harga tertinggi hari itu"),
            _col("obv_slope_pct", "Arah OBV 20h", "pct", digits=0, good="high",
                 hint="on-balance volume: volume mengalir ke sisi beli atau jual"),
            _col("ret_5d_pct", "Return 5 hari", "pct", digits=1, good="high"),
            _col("value_bn", "Nilai transaksi", "num", digits=1, good="high",
                 hint="rata-rata harian 20 hari, Rp miliar"),
        ],
        "rows": rows,
        "summary": {"Peringkat": "gabungan lonjakan volume + posisi penutupan + arah OBV"},
        "warning": (
            "⚠️ Ini BUKAN bandarmology sungguhan. Bandarmology asli membaca broker summary "
            "(broker mana yang akumulasi/distribusi) dan net foreign flow — data itu TIDAK ADA "
            "di yfinance, sumber data aplikasi ini. Yang ditampilkan di sini hanya jejak yang "
            "tertinggal di OHLCV: lonjakan volume, harga menutup di dekat tertinggi, dan arah "
            "OBV. Pola itu bisa muncul dari akumulasi, tapi juga dari berita, rebalancing indeks, "
            "atau kebetulan. Untuk bandarmology sungguhan Anda perlu data broker summary dari "
            "Stockbit/RTI/broker Anda. Template ini juga belum pernah di-backtest sama sekali."
        ),
    }


# ----------------------------------------------------------------------- breakout

def breakout(lookback_days: int = 60, **_) -> dict:
    rows = []
    for t, df in _frames():
        c = df["Close"]
        if len(c) < lookback_days + 25:
            continue
        prior = c.iloc[-(lookback_days + 1):-1]
        prior_high = float(prior.max())
        prior_low = float(prior.min())
        price = float(c.iloc[-1])
        vol_confirm = float(df["Volume"].iloc[-1] / df["Volume"].iloc[-21:-1].mean())

        rows.append({
            "ticker": t,
            "price": round(price, 2),
            "dist_to_high_pct": round((price / prior_high - 1) * 100, 1),
            "base_range_pct": round((prior_high / prior_low - 1) * 100, 1),
            "vol_confirm": round(vol_confirm, 2),
            "rsi": round(float(engine.rsi(c).iloc[-1]), 1),
            "value_bn": round(float((df["Close"] * df["Volume"]).tail(20).mean() / 1e9), 2),
            "signal": price >= prior_high and vol_confirm >= 1.5,
        })

    rows.sort(key=lambda x: -x["dist_to_high_pct"])
    return {
        "columns": [
            _col("ticker", "Saham", "ticker", "left"),
            _col("price", "Harga", "price"),
            _col("dist_to_high_pct", f"Jarak ke tertinggi {lookback_days}h", "pct", digits=1, good="high",
                 hint="0% atau lebih = sedang menembus"),
            _col("base_range_pct", "Lebar konsolidasi", "pct", digits=1, good="low",
                 hint="makin sempit basisnya, makin bersih breakout-nya"),
            _col("vol_confirm", "Konfirmasi volume", "ratio", digits=2, good="high",
                 hint="volume hari ini dibanding rata-rata 20 hari"),
            _col("rsi", "RSI", "num", digits=1),
            _col("value_bn", "Nilai transaksi", "num", digits=1, good="high"),
        ],
        "rows": rows,
        "summary": {"Sinyal": "harga menembus tertinggi 60 hari DAN volume ≥ 1,5× rata-rata"},
        "warning": (
            "Breakout adalah ide #3 di METHODOLOGY 4.7 dan cocok dengan struktur biaya IDX "
            "karena targetnya besar. Tapi di riset forex, keluarga strategi breakout gagal total "
            "(PF terbaik 0,91 dari 14 konfigurasi). Template ini BELUM di-backtest di IDX — "
            "anggap sebagai daftar kandidat untuk diteliti, bukan sinyal."
        ),
    }


# -------------------------------------------------------------------- trend & pullback

def trend(**_) -> dict:
    rows = []
    for t, df in _frames():
        c = df["Close"]
        price = float(c.iloc[-1])
        s50, s200 = engine.sma(c, 50), engine.sma(c, 200)
        if pd.isna(s50.iloc[-1]) or pd.isna(s200.iloc[-1]):
            continue
        slope = float(s50.iloc[-1] / s50.iloc[-21] - 1) * 100
        rows.append({
            "ticker": t,
            "price": round(price, 2),
            "above_sma50": bool(price > s50.iloc[-1]),
            "above_sma200": bool(price > s200.iloc[-1]),
            "sma50_slope_pct": round(slope, 1),
            "dist_sma200_pct": round((price / float(s200.iloc[-1]) - 1) * 100, 1),
            "rsi": round(float(engine.rsi(c).iloc[-1]), 1),
            "signal": bool(price > s50.iloc[-1] and price > s200.iloc[-1] and slope > 0),
        })
    rows.sort(key=lambda x: (-x["signal"], -x["sma50_slope_pct"]))
    return {
        "columns": [
            _col("ticker", "Saham", "ticker", "left"),
            _col("price", "Harga", "price"),
            _col("above_sma50", "> SMA50", "bool", "center"),
            _col("above_sma200", "> SMA200", "bool", "center"),
            _col("sma50_slope_pct", "Kemiringan SMA50", "pct", digits=1, good="high",
                 hint="perubahan SMA50 selama 20 hari"),
            _col("dist_sma200_pct", "Jarak dari SMA200", "pct", digits=1),
            _col("rsi", "RSI", "num", digits=1),
        ],
        "rows": rows,
        "summary": {"Sinyal": "harga di atas SMA50 & SMA200, dan SMA50 sedang naik"},
        "warning": (
            "Trend-following harian adalah ide #2 di METHODOLOGY 4.7 — analog terdekat dengan "
            "riset forex. Belum di-backtest di IDX. Perhatikan: kandidat forex ternyata "
            "counter-trend, bukan trend-following (METHODOLOGY 1.4), jadi jangan asumsikan "
            "arah yang 'masuk akal' itu yang benar sebelum diuji."
        ),
    }


def pullback(**_) -> dict:
    rows = []
    for t, df in _frames():
        c = df["Close"]
        price = float(c.iloc[-1])
        s50, s200 = engine.sma(c, 50), engine.sma(c, 200)
        if pd.isna(s200.iloc[-1]):
            continue
        r = float(engine.rsi(c).iloc[-1])
        high20 = float(c.tail(20).max())
        rows.append({
            "ticker": t,
            "price": round(price, 2),
            "rsi": round(r, 1),
            "above_sma200": bool(price > s200.iloc[-1]),
            "dist_high20_pct": round((price / high20 - 1) * 100, 1),
            "dist_sma50_pct": round((price / float(s50.iloc[-1]) - 1) * 100, 1) if pd.notna(s50.iloc[-1]) else None,
            "signal": bool(price > s200.iloc[-1] and r < 40),
        })
    rows.sort(key=lambda x: (-x["signal"], x["rsi"]))
    return {
        "columns": [
            _col("ticker", "Saham", "ticker", "left"),
            _col("price", "Harga", "price"),
            _col("rsi", "RSI", "num", digits=1, good="low", hint="< 30 oversold"),
            _col("above_sma200", "> SMA200", "bool", "center", hint="tren panjang masih naik"),
            _col("dist_high20_pct", "Jarak dari tertinggi 20h", "pct", digits=1),
            _col("dist_sma50_pct", "Jarak dari SMA50", "pct", digits=1),
        ],
        "rows": rows,
        "summary": {"Sinyal": "harga masih di atas SMA200 tapi RSI < 40 (koreksi dalam tren naik)"},
        "warning": (
            "Mean-reversion adalah ide #4 (prioritas terendah) di METHODOLOGY 4.7. Di riset forex "
            "keluarga ini gagal paling parah: win rate 52% tapi kehilangan 78% modal, karena TP "
            "jauh lebih dekat dari SL (METHODOLOGY 3.5). Target kecil juga berbenturan dengan "
            "biaya IDX. Belum di-backtest."
        ),
    }


def momentum(lookback_months: int = 6, top_n: int = 9, **_) -> dict:
    """Bungkus `engine.screen()` ke bentuk generik supaya /api/screen/run/momentum
    konsisten dengan template lain. Frontend memakai /api/screen (yang punya kontrol
    lookback & jumlah saham sendiri), tapi endpoint ini tetap harus jalan karena
    'momentum' ikut terdaftar di /api/screen/templates."""
    res = engine.screen(lookback_months=lookback_months, top_n=top_n)
    picks = set(res["picks"])
    rows = [{**r, "signal": r["ticker"] in picks} for r in res["rows"]]
    return {
        "columns": [
            _col("ticker", "Saham", "ticker", "left"),
            _col("price", "Harga", "price"),
            _col("momentum_pct", f"Momentum {lookback_months} bln", "pct", digits=1, good="high"),
            _col("ret_1m_pct", "1 bulan", "pct", digits=1, good="high"),
            _col("ret_3m_pct", "3 bulan", "pct", digits=1, good="high"),
            _col("ret_12m_pct", "12 bulan", "pct", digits=1, good="high"),
            _col("rsi", "RSI", "num", digits=1),
            _col("avg_value_bn", "Likuiditas", "num", digits=1, good="high",
                 hint="rata-rata nilai transaksi harian 60 hari, Rp miliar"),
        ],
        "rows": rows,
        "summary": {
            "Sinyal per": res["as_of"],
            "Dipegang": f"{len(res['picks'])} saham momentum tertinggi yang masih positif",
        },
        "warning": None,
    }


TEMPLATES = {
    "momentum": {
        "name": "Momentum lintas saham",
        "tagline": "Peringkat return 6 bulan — strategi eksperimen 001",
        "fn": momentum,
        "status": "tervalidasi sebagian",
        "evidence": "Satu-satunya template yang mengalahkan buy&hold: CAGR +16,3% vs +8,8% "
                    "(2019–2023), PF 1,81. Brankas bertahan (PF 1,82).",
    },
    "overnight": {
        "name": "Beli sore → jual pagi",
        "tagline": "Menahan posisi semalam saja (overnight)",
        "fn": overnight,
        "status": "gagal: biaya",
        "evidence": "Efek kotornya nyata (+0,27%/hari, win 58%) tapi friksi 0,9–2,5% per "
                    "transaksi memakannya habis: 0 dari 44 saham bersihnya positif.",
    },
    "intraday": {
        "name": "Beli pagi → jual sore",
        "tagline": "Masuk dan keluar di hari yang sama",
        "fn": intraday,
        "status": "gagal: sinyal",
        "evidence": "Bahkan sebelum biaya sudah rugi: rata-rata −0,17%/hari dengan win rate 38%.",
    },
    "akumulasi": {
        "name": "Akumulasi (proxy bandarmology)",
        "tagline": "Jejak akumulasi dari volume & posisi penutupan",
        "fn": akumulasi,
        "status": "gagal: backtest",
        "evidence": "Eksperimen 003: CAGR +1,6% vs buy&hold +8,8% (2019–2023). PF 1,17, "
                    "CI [0,56;2,43] — tidak terbedakan dari nol.",
    },
    "breakout": {
        "name": "Breakout konsolidasi",
        "tagline": "Menembus tertinggi 60 hari dengan volume",
        "fn": breakout,
        "status": "gagal: backtest",
        "evidence": "Eksperimen 003: CAGR −5,7%, PF 0,83 — paling buruk dari semua template. "
                    "Sejalan dengan riset forex, di mana keluarga breakout juga gagal total.",
    },
    "trend": {
        "name": "Trend-following",
        "tagline": "Di atas SMA50 & SMA200 dengan tren menguat",
        "fn": trend,
        "status": "gagal: backtest",
        "evidence": "Eksperimen 003: CAGR −1,9%, PF 1,05, CI [0,51;2,16]. Strategi yang paling "
                    "'masuk akal' justru tidak menghasilkan apa-apa.",
    },
    "pullback": {
        "name": "Koreksi dalam tren naik",
        "tagline": "RSI rendah tapi masih di atas SMA200",
        "fn": pullback,
        "status": "gagal: backtest",
        "evidence": "Eksperimen 003: CAGR −0,4%, PF 1,10, win rate bulanan hanya 35%.",
    },
}


def list_templates() -> list[dict]:
    return [{"id": k, "name": v["name"], "tagline": v["tagline"], "status": v["status"],
             "evidence": v.get("evidence")}
            for k, v in TEMPLATES.items()]


def run(template_id: str, **kw) -> dict:
    if template_id not in TEMPLATES:
        raise KeyError(template_id)
    result = TEMPLATES[template_id]["fn"](**kw)
    meta = TEMPLATES[template_id]
    result["id"] = template_id
    result["name"] = meta["name"]
    result["status"] = meta["status"]
    return result
