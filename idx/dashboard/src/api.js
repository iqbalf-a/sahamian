async function req(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Gagal memuat (${res.status})`);
  }
  return res.json();
}

export const getScreen = (lookback, topN) =>
  req(`/api/screen?lookback=${lookback}&top_n=${topN}`);

export const getStock = (ticker, bars = 400) =>
  req(`/api/stock/${encodeURIComponent(ticker)}?bars=${bars}`);

export const addTicker = (ticker) =>
  req(`/api/fetch/${encodeURIComponent(ticker)}`, { method: "POST" });

export const runBacktest = (body) =>
  req("/api/backtest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
