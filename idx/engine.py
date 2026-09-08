"""
Engine analisis saham IDX — dipakai oleh aplikasi (app/server.py).

Berbeda dari `experiments/NNN_*/strategy.py` yang merupakan SNAPSHOT beku dari kode
yang diuji (sesuai METHODOLOGY 2.1), modul ini adalah versi berparameter untuk dipakai
interaktif. Default-nya sengaja direproduksi persis sama dengan eksperimen 001 supaya
angka yang tampil di aplikasi bisa dicocokkan dengan angka riset.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")

# Universe terkunci sesuai experiments/SETUP.md (LQ45, komposisi Agu-Okt 2026).
# HARUS eksplisit: sebelumnya universe diambil dari "semua CSV di data/", sehingga saham
# yang ditambahkan user lewat aplikasi diam-diam ikut masuk ke backtest dan mengubah
# hasil riset tanpa terlihat. Saham tambahan tetap bisa dianalisis satu-satu, tapi tidak
# pernah ikut ke backtest/screener universe kecuali diminta eksplisit.
UNIVERSE = """AADI ADMR ADRO AKRA AMMN AMRT ANTM ASII BBCA BBNI BBRI BBTN BMRI BRPT BUMI CPIN
CUAN DEWA EMTK ESSA EXCL GOTO HRTA ICBP INCO INDF INDY INKP ISAT ITMG JPFA KLBF
MAPI MBMA MDKA MEDC PGAS PGEO PTBA SCMA TLKM UNTR UNVR WIFI""".split()

EXPLORE_START = "2019-01-01"
EXPLORE_END = "2023-12-31"
VAULT_START = "2024-01-01"


# --------------------------------------------------------------------------- data

def valid_ticker(ticker: str) -> str:
    """Validasi ketat: hanya huruf/angka, supaya tidak bisa dipakai untuk path traversal."""
    t = ticker.strip().upper().removesuffix(".JK")
    if not TICKER_RE.match(t):
        raise ValueError(f"kode saham tidak valid: {ticker!r}")
    return t


def load_prices(ticker: str) -> pd.DataFrame | None:
    t = valid_ticker(ticker)
    path = DATA_DIR / f"{t}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df.sort_index()


def available_tickers() -> list[str]:
    """Semua saham yang ada datanya secara lokal (universe + tambahan dari user)."""
    return sorted(p.stem for p in DATA_DIR.glob("*.csv"))


def universe_tickers() -> list[str]:
    """Universe riset yang terkunci — inilah yang dipakai backtest & screener."""
    return [t for t in UNIVERSE if (DATA_DIR / f"{t}.csv").exists()]


def extra_tickers() -> list[str]:
    """Saham di luar universe yang ditambahkan user lewat aplikasi."""
    return [t for t in available_tickers() if t not in set(UNIVERSE)]


_NAMES_PATH = Path(__file__).parent / "ticker_names.json"
_names_cache: dict | None = None


def ticker_names() -> dict:
    """Nama emiten dari yfinance (lihat build_ticker_names.py). Dimuat sekali."""
    global _names_cache
    if _names_cache is None:
        import json
        _names_cache = json.loads(_NAMES_PATH.read_text(encoding="utf-8")) if _NAMES_PATH.exists() else {}
    return _names_cache


def search_local(query: str, limit: int = 8) -> list[dict]:
    """Cari di saham yang datanya sudah ada — cocokkan kode ATAU nama perusahaan."""
    q = query.strip().upper()
    names = ticker_names()
    universe = set(UNIVERSE)
    hits = []
    for t in available_tickers():
        name = names.get(t, {}).get("name", "")
        code_hit = q in t
        name_hit = q in name.upper()
        if not (code_hit or name_hit):
            continue
        hits.append({
            "ticker": t, "name": name, "in_universe": t in universe,
            "cached": True,
            "_rank": (0 if t.startswith(q) else 1 if code_hit else 2),
        })
    hits.sort(key=lambda h: (h["_rank"], h["ticker"]))
    for h in hits:
        h.pop("_rank")
    return hits[:limit]


def search_remote(query: str, limit: int = 6) -> list[dict]:
    """Cari di seluruh emiten IDX lewat yfinance (untuk saham yang belum ada datanya)."""
    import yfinance as yf

    try:
        res = yf.Search(query, max_results=20)
        quotes = res.quotes or []
    except Exception:
        return []

    have = set(available_tickers())
    universe = set(UNIVERSE)
    out = []
    for q in quotes:
        sym = (q.get("symbol") or "").upper()
        if not sym.endswith(".JK") or q.get("quoteType") != "EQUITY":
            continue
        code = sym[:-3]
        if code in have or not TICKER_RE.match(code):
            continue
        out.append({
            "ticker": code,
            "name": q.get("longname") or q.get("shortname") or "",
            "in_universe": code in universe,
            "cached": False,
        })
        if len(out) >= limit:
            break
    return out


def fetch_ticker(ticker: str, start: str = "2018-06-01") -> pd.DataFrame | None:
    """Ambil saham baru dari yfinance dan cache ke data/. Dipanggil saat user mencari
    ticker yang belum ada di universe lokal."""
    import yfinance as yf

    t = valid_ticker(ticker)
    df = yf.download(f"{t}.JK", start=start, auto_adjust=True, progress=False)
    if df is None or df.empty or len(df) < 60:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index.name = "date"
    df.to_csv(DATA_DIR / f"{t}.csv")
    return df


def close_panel(tickers: list[str] | None = None) -> pd.DataFrame:
    tickers = tickers or universe_tickers()
    data = {}
    for t in tickers:
        df = load_prices(t)
        if df is not None:
            data[t] = df["Close"]
    return pd.DataFrame(data)


# --------------------------------------------------------------------- indikator

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = df["Close"].shift()
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - prev_close).abs(),
        (df["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


# ------------------------------------------------------------------ fraksi harga

def tick_size(price: float) -> int:
    """Fraksi harga IDX per pita harga (METHODOLOGY 4.3)."""
    if price < 200:
        return 1
    if price < 500:
        return 2
    if price < 2000:
        return 5
    if price < 5000:
        return 10
    return 25


def round_to_tick(price: float) -> float:
    t = tick_size(price)
    return round(price / t) * t


# ------------------------------------------------------------------- backtest

@dataclass
class BacktestParams:
    lookback_months: int = 6
    top_n: int = 9
    min_holdings: int = 3
    cost_buy: float = 0.0020
    cost_sell: float = 0.0030
    capital0: float = 100_000_000.0
    start: str = EXPLORE_START
    end: str = EXPLORE_END
    require_positive_momentum: bool = True
    tickers: list[str] | None = None


@dataclass
class BacktestResult:
    months: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    yearly: list[dict] = field(default_factory=list)
    benchmark: list[float] = field(default_factory=list)
    returns: list[float] = field(default_factory=list)


def momentum_backtest(p: BacktestParams) -> BacktestResult:
    monthly = close_panel(p.tickers).resample("ME").last()
    mom = monthly.pct_change(p.lookback_months)

    dates = monthly.index
    window = dates[(dates >= pd.Timestamp(p.start)) & (dates <= pd.Timestamp(p.end))]

    capital = p.capital0
    prev_weights: dict[str, float] = {}
    months: list[dict] = []

    for dt in window:
        loc = dates.get_loc(dt)
        if loc == 0:
            continue
        prev_dt = dates[loc - 1]

        month_pnl = 0.0
        for tkr, w in prev_weights.items():
            p0, p1 = monthly.loc[prev_dt, tkr], monthly.loc[dt, tkr]
            if pd.isna(p0) or pd.isna(p1) or p0 <= 0:
                continue
            month_pnl += capital * w * (p1 / p0 - 1.0)

        before = capital + month_pnl

        row = mom.loc[dt].dropna()
        if p.require_positive_momentum:
            row = row[row > 0]
        selected = row.sort_values(ascending=False).head(max(p.min_holdings, p.top_n)).index.tolist()
        new_weights = {t: 1.0 / len(selected) for t in selected} if selected else {}

        cost = 0.0
        for t in set(prev_weights) | set(new_weights):
            delta = new_weights.get(t, 0.0) - prev_weights.get(t, 0.0)
            cost += before * abs(delta) * (p.cost_buy if delta > 0 else p.cost_sell)

        after = before - cost
        months.append({
            "date": dt.strftime("%Y-%m"),
            "capital": round(after),
            "pnl": round(after - capital),
            "return_pct": round((after / capital - 1) * 100, 3),
            "n_holdings": len(selected),
            "holdings": selected,
            "cost": round(cost),
        })
        capital, prev_weights = after, new_weights

    rets = np.array([m["return_pct"] / 100 for m in months], dtype=float)
    metrics = compute_metrics(rets, p.capital0) if len(rets) else {}

    yearly = []
    if months:
        df = pd.DataFrame(months)
        df["year"] = df["date"].str.slice(0, 4).astype(int)
        for y, g in df.groupby("year"):
            r = g["return_pct"].values.astype(float)
            gp, gl = r[r > 0].sum(), -r[r < 0].sum()
            yearly.append({
                "year": int(y), "n_months": len(r),
                "pf": round(float(gp / gl), 2) if gl > 0 else None,
                "win_rate": round(float((r > 0).mean() * 100), 1),
                "net": round(float(g["pnl"].sum())),
                "return_pct": round(float((np.prod(1 + r / 100) - 1) * 100), 1),
            })

    bench = _benchmark_curve(monthly, window, p.capital0)
    return BacktestResult(months=months, metrics=metrics, yearly=yearly,
                          benchmark=bench, returns=rets.tolist())


def _benchmark_curve(monthly: pd.DataFrame, window: pd.DatetimeIndex, capital0: float) -> list[float]:
    """Equal-weight buy&hold saham yang sudah listing di awal periode (tanpa biaya)."""
    sub = monthly.loc[window]
    if sub.empty:
        return []
    valid = sub.iloc[0].dropna().index
    if len(valid) == 0:
        return []
    norm = sub[valid] / sub[valid].iloc[0]
    return [round(float(v * capital0)) for v in norm.mean(axis=1).values]


def compute_metrics(returns: np.ndarray, capital0: float) -> dict:
    """Semua metrik dihitung di ruang RETURN, bukan rupiah absolut — lihat catatan di
    `stats.permute_drawdown_returns` soal kenapa P&L nominal menyesatkan untuk
    strategi yang memajemukkan modal."""
    gp, gl = returns[returns > 0].sum(), -returns[returns < 0].sum()
    equity = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(equity)
    max_dd = float(((peak - equity) / peak).max() * 100)
    years = len(returns) / 12
    growth = float(equity[-1])
    return {
        "n_months": len(returns),
        "final_capital": round(capital0 * growth),
        "total_return_pct": round((growth - 1) * 100, 1),
        "cagr_pct": round((growth ** (1 / years) - 1) * 100, 1) if years > 0 else None,
        "pf": round(float(gp / gl), 2) if gl > 0 else None,
        "win_rate_pct": round(float((returns > 0).mean() * 100), 1),
        "max_dd_pct": round(max_dd, 1),
        "avg_month_return_pct": round(float(returns.mean() * 100), 2),
    }


# -------------------------------------------------------------------- screener

def screen(lookback_months: int = 6, top_n: int = 9, tickers: list[str] | None = None,
           as_of: str | None = None) -> dict:
    """Peringkat momentum seluruh universe pada tanggal terakhir data (sinyal live)."""
    panel = close_panel(tickers)
    if as_of:
        panel = panel.loc[:as_of]
    monthly = panel.resample("ME").last()
    mom6 = monthly.pct_change(lookback_months).iloc[-1]

    rows = []
    for t in panel.columns:
        df = load_prices(t)
        if df is None or len(df) < 60:
            continue
        if as_of:
            df = df.loc[:as_of]
        close = df["Close"]
        last = float(close.iloc[-1])
        m = mom6.get(t)
        r = rsi(close).iloc[-1]
        s50, s200 = sma(close, 50).iloc[-1], sma(close, 200).iloc[-1]
        rows.append({
            "ticker": t,
            "price": round(last, 2),
            "momentum_pct": round(float(m) * 100, 1) if pd.notna(m) else None,
            "ret_1m_pct": _ret(close, 21),
            "ret_3m_pct": _ret(close, 63),
            "ret_6m_pct": _ret(close, 126),
            "ret_12m_pct": _ret(close, 252),
            "rsi": round(float(r), 1) if pd.notna(r) else None,
            "above_sma50": bool(last > s50) if pd.notna(s50) else None,
            "above_sma200": bool(last > s200) if pd.notna(s200) else None,
            "volatility_pct": round(float(close.pct_change().tail(252).std() * 100), 2),
            "avg_value_bn": round(float((df["Close"] * df["Volume"]).tail(60).mean() / 1e9), 2),
            "last_date": df.index[-1].strftime("%Y-%m-%d"),
        })

    ranked = sorted(
        [r for r in rows if r["momentum_pct"] is not None],
        key=lambda r: -r["momentum_pct"],
    )
    positive = [r for r in ranked if r["momentum_pct"] > 0]
    picks = {r["ticker"] for r in positive[:top_n]}
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
        r["selected"] = r["ticker"] in picks
    for r in rows:
        if r["momentum_pct"] is None:
            r["rank"] = None
            r["selected"] = False

    return {
        "as_of": max((r["last_date"] for r in rows), default=None),
        "lookback_months": lookback_months,
        "top_n": top_n,
        "rows": ranked + [r for r in rows if r["momentum_pct"] is None],
        "picks": [r["ticker"] for r in positive[:top_n]],
    }


def _ret(close: pd.Series, bars: int) -> float | None:
    if len(close) <= bars:
        return None
    return round(float(close.iloc[-1] / close.iloc[-1 - bars] - 1) * 100, 1)


# ---------------------------------------------------------------- stock detail

def momentum_rank(ticker: str, lookback_months: int = 6, top_n: int = 9) -> dict:
    """Posisi saham ini dalam peringkat momentum universe — satu-satunya strategi yang
    lolos validasi (eksperimen 001-003). Untuk saham di luar universe, peringkatnya
    dihitung sebagai pembanding tapi ditandai `in_universe: False`."""
    t = valid_ticker(ticker)
    monthly = close_panel().resample("ME").last()
    mom = monthly.pct_change(lookback_months).iloc[-1].dropna()

    own = None
    df = load_prices(t)
    if df is not None:
        m = df["Close"].resample("ME").last()
        if len(m) > lookback_months and pd.notna(m.iloc[-1 - lookback_months]) and m.iloc[-1 - lookback_months] > 0:
            own = float(m.iloc[-1] / m.iloc[-1 - lookback_months] - 1)

    ranked = mom.sort_values(ascending=False)
    in_universe = t in set(UNIVERSE)
    positive = ranked[ranked > 0]
    picks = set(positive.head(top_n).index)

    rank = None
    if in_universe and t in ranked.index:
        rank = int(list(ranked.index).index(t) + 1)
    elif own is not None:
        rank = int((ranked > own).sum() + 1)  # posisi seandainya ikut diperingkat

    return {
        "momentum_pct": round(own * 100, 1) if own is not None else None,
        "rank": rank,
        "universe_size": int(len(ranked)),
        "in_universe": in_universe,
        "selected": bool(in_universe and t in picks),
        "top_n": top_n,
        "n_positive": int(len(positive)),
    }


def stock_detail(ticker: str, bars: int = 500, lookback_months: int = 6) -> dict | None:
    df = load_prices(ticker)
    if df is None:
        return None
    close = df["Close"]
    # momentum dihitung persis seperti screener/strategi (basis harga akhir bulan),
    # bukan basis N hari bursa -- supaya angka di detail cocok dengan angka seleksi
    monthly = close.resample("ME").last()
    momentum = None
    if len(monthly) > lookback_months:
        prev = monthly.iloc[-1 - lookback_months]
        if pd.notna(prev) and prev > 0:
            momentum = round(float(monthly.iloc[-1] / prev - 1) * 100, 1)
    full = pd.DataFrame({
        "date": df.index.strftime("%Y-%m-%d"),
        "close": close.round(2),
        "open": df["Open"].round(2),
        "high": df["High"].round(2),
        "low": df["Low"].round(2),
        "volume": df["Volume"],
        "sma20": sma(close, 20).round(2),
        "sma50": sma(close, 50).round(2),
        "sma200": sma(close, 200).round(2),
        "rsi": rsi(close).round(1),
    })
    tail = full.tail(bars).where(pd.notna(full.tail(bars)), None)

    last = float(close.iloc[-1])
    a = float(atr(df).iloc[-1])
    high_52w = float(close.tail(252).max())
    low_52w = float(close.tail(252).min())

    rng = high_52w - low_52w
    return {
        "ticker": valid_ticker(ticker),
        "name": ticker_names().get(valid_ticker(ticker), {}).get("name", ""),
        "last_date": df.index[-1].strftime("%Y-%m-%d"),
        "price": round(last, 2),
        "series": tail.to_dict("records"),
        "strategy": momentum_rank(ticker, lookback_months=lookback_months),
        "stats": {
            "range_position_pct": round((last - low_52w) / rng * 100, 1) if rng > 0 else None,
            "momentum_pct": momentum,
            "lookback_months": lookback_months,
            "ret_1m_pct": _ret(close, 21),
            "ret_3m_pct": _ret(close, 63),
            "ret_6m_pct": _ret(close, 126),
            "ret_12m_pct": _ret(close, 252),
            "rsi": round(float(rsi(close).iloc[-1]), 1),
            "atr": round(a, 2),
            "atr_pct": round(a / last * 100, 2),
            "volatility_pct": round(float(close.pct_change().tail(252).std() * 100), 2),
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "pct_from_high": round((last / high_52w - 1) * 100, 1),
            "pct_from_low": round((last / low_52w - 1) * 100, 1),
            "above_sma50": bool(last > sma(close, 50).iloc[-1]),
            "above_sma200": bool(last > sma(close, 200).iloc[-1]),
            "avg_value_bn": round(float((df["Close"] * df["Volume"]).tail(60).mean() / 1e9), 2),
            "tick_size": tick_size(last),
            "lot_price": round(last * 100),
        },
    }
