"""
Deteksi pergerakan tidak wajar + berita pasar, dan (opsional) analisis AI yang mengaitkan
keduanya.

Prinsip yang dipegang di modul ini: **aplikasi tidak boleh mengarang sebab.** Bagian
statistik hanya melaporkan saham mana yang bergerak di luar kebiasaannya sendiri. Bagian
berita hanya menampilkan judul asli beserta tautannya. Kalau analisis AI dinyalakan, ia
HANYA boleh memakai judul berita yang benar-benar diambil di sini — dan diminta secara
eksplisit mengatakan "tidak ada berita yang menjelaskan" kalau memang tidak ketemu.
Menebak sebab kenaikan saham adalah cara cepat membuat orang rugi.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from html import unescape
from pathlib import Path

import numpy as np

import engine

CACHE = Path(__file__).parent / "data_news"
CACHE.mkdir(exist_ok=True)
NEWS_TTL_SECONDS = 900

FEEDS = [
    ("CNBC Indonesia", "https://www.cnbcindonesia.com/market/rss"),
    ("Kontan Investasi", "https://investasi.kontan.co.id/rss"),
    ("IDX Channel", "https://www.idxchannel.com/rss/market-news"),
]

STOPWORDS = {"PT", "TBK", "PERSERO", "INDONESIA", "TBK.", "(PERSERO)"}


# ------------------------------------------------------------- pergerakan tak wajar

def unusual_movers(min_z: float = 2.0, limit: int = 12) -> list[dict]:
    """Saham yang pergerakan hari ini menyimpang jauh dari volatilitas normalnya sendiri.

    Memakai z-score terhadap simpangan baku 60 hari — bukan ambang persentase tetap,
    supaya saham kalem seperti BBCA dan saham liar seperti BUMI dinilai dengan ukuran
    masing-masing.
    """
    names = engine.ticker_names()
    out = []
    for t in engine.available_tickers():
        df = engine.load_prices(t)
        if df is None or len(df) < 90:
            continue
        c = df["Close"]
        ret = c.pct_change()
        today = float(ret.iloc[-1])
        sigma = float(ret.iloc[-61:-1].std())
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        z = today / sigma
        vol_avg = float(df["Volume"].iloc[-21:-1].mean())
        vol_ratio = float(df["Volume"].iloc[-1] / vol_avg) if vol_avg > 0 else None
        if abs(z) < min_z:
            continue
        out.append({
            "ticker": t,
            "name": names.get(t, {}).get("name", ""),
            "price": round(float(c.iloc[-1]), 2),
            "change_pct": round(today * 100, 2),
            "z_score": round(z, 1),
            "volume_ratio": round(vol_ratio, 1) if vol_ratio else None,
            "date": df.index[-1].strftime("%Y-%m-%d"),
        })
    out.sort(key=lambda r: -abs(r["z_score"]))
    return out[:limit]


# ------------------------------------------------------------------------- berita

def _strip_html(s: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", s)).strip()


def fetch_news(refresh: bool = False) -> list[dict]:
    cache_path = CACHE / "headlines.json"
    if cache_path.exists() and not refresh:
        if time.time() - cache_path.stat().st_mtime < NEWS_TTL_SECONDS:
            return json.loads(cache_path.read_text(encoding="utf-8"))

    items = []
    for source, url in FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")
        except Exception:
            continue
        for block in re.findall(r"<item>(.*?)</item>", raw, re.S)[:25]:
            title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
            link = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", block, re.S)
            date = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
            if not title:
                continue
            items.append({
                "source": source,
                "title": _strip_html(title.group(1)),
                "link": _strip_html(link.group(1)) if link else None,
                "published": _strip_html(date.group(1)) if date else None,
            })

    cache_path.write_text(json.dumps(items), encoding="utf-8")
    return items


def _keywords(ticker: str, name: str) -> list[str]:
    words = [w for w in re.split(r"[^A-Za-z]+", name.upper())
             if len(w) > 3 and w not in STOPWORDS]
    return [ticker] + words[:2]


def link_news(headlines: list[dict], tickers: list[str]) -> dict[str, list[dict]]:
    names = engine.ticker_names()
    linked: dict[str, list[dict]] = {}
    for t in tickers:
        kws = _keywords(t, names.get(t, {}).get("name", ""))
        hits = []
        for h in headlines:
            up = h["title"].upper()
            if any(re.search(rf"\b{re.escape(k)}\b", up) for k in kws):
                hits.append(h)
        if hits:
            linked[t] = hits[:4]
    return linked


# ---------------------------------------------------------------------- analisis AI

SYSTEM_PROMPT = """Kamu membantu menganalisis pasar saham Indonesia (IDX).

Kamu diberi (a) daftar saham yang hari ini bergerak jauh di luar kebiasaannya secara
statistik, dan (b) daftar judul berita pasar yang baru diambil dari RSS media keuangan
Indonesia.

Aturan yang WAJIB dipatuhi:
1. Hanya gunakan judul berita yang diberikan. Jangan memakai pengetahuan dari ingatanmu
   tentang peristiwa, emiten, atau kondisi pasar.
2. Kalau tidak ada judul berita yang menjelaskan pergerakan sebuah saham, katakan apa
   adanya: "tidak ada berita di daftar ini yang menjelaskannya". JANGAN mengarang sebab.
3. Bedakan dengan jelas antara "berita ini menyebut saham tersebut" (fakta) dan "berita ini
   mungkin penyebabnya" (dugaan). Korelasi satu hari bukan bukti sebab-akibat.
4. Jangan memberi rekomendasi beli/jual dan jangan memprediksi harga.
5. Jawab dalam bahasa Indonesia, ringkas, maksimal 200 kata.

Format: untuk tiap saham yang punya kaitan berita, satu paragraf pendek. Tutup dengan satu
kalimat pengingat bahwa lonjakan karena sentimen berita sering berbalik arah."""


def ai_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ai_analysis(movers: list[dict], headlines: list[dict]) -> dict:
    if not ai_available():
        return {
            "available": False,
            "reason": ("Analisis AI belum aktif. Set environment variable ANTHROPIC_API_KEY "
                       "lalu jalankan ulang server API. Tanpa itu, aplikasi hanya menampilkan "
                       "pergerakan statistik dan judul berita apa adanya — sengaja tidak "
                       "menebak sebab."),
        }

    import anthropic

    linked = link_news(headlines, [m["ticker"] for m in movers])
    payload = {
        "saham_bergerak_tak_wajar": movers,
        "berita_terkait_per_saham": linked,
        "semua_judul_berita": [h["title"] for h in headlines[:60]],
    }

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": ("Berikut datanya dalam JSON. Jelaskan saham mana yang pergerakannya "
                        "punya kaitan dengan berita, dan mana yang tidak ada penjelasannya.\n\n"
                        + json.dumps(payload, ensure_ascii=False, indent=1)),
        }],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return {"available": True, "analysis": text, "model": "claude-opus-4-8", "linked": linked}


def briefing(refresh: bool = False) -> dict:
    movers = unusual_movers()
    headlines = fetch_news(refresh=refresh)
    return {
        "movers": movers,
        "headlines": headlines[:30],
        "linked": link_news(headlines, [m["ticker"] for m in movers]),
        "ai_available": ai_available(),
    }
