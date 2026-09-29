# Sahamian

An Indonesian stock (IDX) analysis app — screener, charts, backtesting, and a returns
calendar — built on top of quantitative research that inherits its methodology from an earlier
forex EA study.

What sets this apart from most screeners: **every strategy here has been backtested, and the
ones that failed are still shown along with the numbers proving they failed.** Out of seven
screener templates, only one beat passive buy-and-hold.

> The application interface is in Indonesian, since it targets the Indonesian market. This
> documentation is in English.

---

## Running the app

### Double-click `START.bat`

That's it. The script handles everything:

1. Checks that Python and Node.js are installed — and points you to the downloads if not
2. Sets up the Python environment and frontend dependencies — **automatic, first run only**
3. Downloads price data if none exists yet
4. Frees up ports left behind by previous runs
5. Starts both servers
6. Opens the browser

Two small windows appear in the taskbar (**Server Data** and **Server Tampilan** — the data and
UI servers). **Leave them open** while using the app; they are the engine behind it.

**To stop:** double-click `STOP.bat`.

On a first run, steps 2–3 take roughly five minutes. Every run after that takes seconds.

### Alternative: start the servers manually

Useful if you want to watch the logs, or if `START.bat` misbehaves. Open **two** Command
Prompt or PowerShell windows.

**Window 1** — backend:

```
cd idx
.venv\Scripts\python.exe -m uvicorn app.server:api --port 8000 --reload
```

**Window 2** — frontend:

```
cd idx\dashboard
npm run dev
```

Then open **http://localhost:5173**. Stop either server with `Ctrl + C`.

> ⚠️ On Windows, use backslashes `\`, not forward slashes `/`. Command Prompt rejects
> `.venv/Scripts/python.exe` with `'.venv' is not recognized as an internal or external
> command`. PowerShell accepts both, but backslashes work everywhere.

> If you use Claude Code, both servers are registered in `.claude/launch.json` as `idx-api`
> and `idx-app`.

---

## Price data: staleness warning and refresh button

Price data lives in CSV files on your machine and **does not refresh on its own**.

The app checks on every load. If the data has fallen behind, a banner appears at the top:

> **Data yang tampil bukan yang terbaru** *(the data shown is not current)*
> Data terakhir 7 Sep 2026 (22 hari lalu) — tertinggal 15 hari bursa
> [ **Perbarui sekarang** ] [ Nanti saja ]

Click **Perbarui sekarang** (*refresh now*) and watch the progress counter (`52 dari 83 · BBRI`).
Refreshing all 82 tickers takes about two minutes. When it finishes, click **Muat ulang
tampilan** to reload the view.

The banner only appears when the data is actually behind; it stays out of the way otherwise.

How staleness is determined: the app compares the newest date in your data against the most
recent trading day that *should* have data — weekdays only, and today only counts after 17:00,
since the exchange closes at 15:49 WIB. Public holidays are unknown to the app, so the banner
can appear during a long holiday even when your data is already current. That is why the
wording says "last data from *date*" rather than claiming the data is definitely stale.

You can also refresh from a terminal:

```
cd idx
.venv\Scripts\python.exe download_data.py
.venv\Scripts\python.exe download_extra.py
```

---

## Troubleshooting

### `'.venv' is not recognized as an internal or external command`

You used forward slashes in Command Prompt. Switch to backslashes:

| ❌ Wrong | ✅ Right |
|---|---|
| `.venv/Scripts/python.exe` | `.venv\Scripts\python.exe` |

### `[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`

Port 8000 is **already taken** — usually a server left running from an earlier attempt. Find
the process in PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object {
  Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" |
    Select-Object ProcessId, Name, CommandLine
}
```

Once you have the PID and you are sure it is your own stale server:

```powershell
Stop-Process -Id <PID> -Force
```

Or use a different port: change `--port 8000` to `--port 8001`, and update the proxy target in
`idx/dashboard/vite.config.js` to match.

### `Failed to fetch`, blank page, or empty tables

The backend is not running. Check that window 1 is still alive, then open
**http://localhost:8000/api/health** — it should return `{"ok":true,"tickers":82}`.

### `python` or `npm` not recognized

Not installed, or not on PATH. Install [Python 3.11+](https://www.python.org/downloads/) —
tick **Add Python to PATH** during setup — and [Node.js](https://nodejs.org/).

---

## First-time setup (if `.venv` or `node_modules` are missing)

`START.bat` does this automatically. To do it by hand:

```
cd idx
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then fetch the data (a few minutes, needs an internet connection):

```
.venv\Scripts\python.exe download_data.py
.venv\Scripts\python.exe download_extra.py
.venv\Scripts\python.exe build_ticker_names.py
```

Finally, the frontend dependencies:

```
cd dashboard
npm install
```

---

## What's in the app

| Tab | Contents |
|---|---|
| **Utama** (Home) | IHSG index, unusual-move detection with matching news, and top gainers / losers / trending / most active / near 52-week high and low |
| **Screener** | Seven strategy templates, each labelled with its test result |
| **Kalender** (Calendar) | Daily profit/loss heatmap, two months per page. Defaults to the IHSG index; switchable to any stock |
| **Lab backtest** | Momentum strategy backtest with adjustable parameters |
| **Sensitivitas** | Rolling walk-forward plus a 36-cell parameter grid |
| **Riset** (Research) | Full report for experiment 001 |

**Stock detail** opens by clicking any table row, or through the search box in the top right —
which matches on ticker **or** company name, so typing "bank" or "asuransi" works. It shows a
summary panel, a line or candlestick chart with SMA20/50/200 and RSI (expandable), an
assessment against the strategy's criteria, profit-target feasibility at the current price, and
corporate actions.

Stocks outside the 82 stored locally can be pulled in from the app itself — pick one from the
search results and its data is fetched from yfinance automatically.

---

## Strategy status

| Template | Status | Numbers |
|---|---|---|
| Cross-sectional momentum | ✅ partially validated | CAGR +16.3% vs +8.8% buy-and-hold (2019–2023) |
| Buy at close → sell at open | ❌ failed: costs | real gross edge (+0.27%/day) but 0 of 44 stocks net positive |
| Buy at open → sell at close | ❌ failed: signal | −0.17%/day even before costs |
| Accumulation (bandarmology proxy) | ❌ failed: backtest | +1.6%, PF 1.17 |
| Consolidation breakout | ❌ failed: backtest | −5.7%, PF 0.83 |
| Trend-following | ❌ failed: backtest | −1.9%, PF 1.05 |
| Pullback in an uptrend | ❌ failed: backtest | −0.4%, 35% monthly win rate |

Test details are in [`idx/experiments/`](idx/experiments/INDEX.md).

⚠️ Even the momentum strategy is **not ready for real money**: its 95th-percentile drawdown
reaches 57%, and 2026 fell −40.1% after 2025 gained +138.6%. It has never been traded live.

---

## AI feature (optional, needs an API key)

The panel on the Home tab flags stocks moving more than two standard deviations beyond their own
volatility, then matches them against RSS headlines from CNBC Indonesia, Kontan, and IDX Channel.
**The statistics and headlines work without any API key.**

The AI commentary is optional. To enable it:

```bash
export ANTHROPIC_API_KEY=sk-ant-...      # Windows: setx ANTHROPIC_API_KEY "sk-ant-..."
```

Then restart the API server. The prompt is deliberately constrained: the model may only use the
headlines actually fetched, and must say "no headline explains this" when none matches, rather
than inventing a cause.

---

## Project layout

```
sahamian/
├── START.bat              double-click to start the app
├── STOP.bat               double-click to stop it
├── README.md              this file
├── METHODOLOGY.md         research methodology — read sections 1 and 4 if short on time
├── FINDINGS.md            full results of the forex study the methodology came from
├── reusable/stats.py      bootstrap CIs and drawdown permutation (market-agnostic)
└── idx/
    ├── engine.py          indicators, momentum backtest, universe ranking
    ├── screeners.py       the seven screener templates
    ├── market.py          home lists, calendar, corporate actions
    ├── news.py            unusual-move detection, news RSS, AI analysis
    ├── updater.py         data freshness check and refresh with progress
    ├── stats.py           copy of reusable/stats.py plus return-space functions
    ├── app/server.py      FastAPI backend
    ├── dashboard/         React + Vite + Recharts frontend
    ├── data/              82 daily price CSVs (LQ45 + IDX80)
    ├── data_index/        IHSG index
    └── experiments/       INDEX.md and experiments 001–003
```

**Start with [`idx/experiments/INDEX.md`](idx/experiments/INDEX.md)** if you want to continue the
research — it lists every finding, what has been tested, and what has not.

> Note: the research documents under `idx/experiments/`, along with `METHODOLOGY.md` and
> `FINDINGS.md`, are still written in Indonesian. They are working research notes rather than
> user-facing documentation.

---

## Data caveats

- Source is yfinance (`.JK` tickers), split- and dividend-adjusted. Verified clean: no single-day
  jump above 40% anywhere in the universe, and BBCA was checked by hand around its 2021-10-13
  split.
- **Survivorship bias is not corrected.** The universe uses today's LQ45 membership applied
  backwards to 2019, so delisted companies are missing.
- Top gainer and loser lists are computed from the 82 stocks stored locally, **not** from all
  ~900 IDX listings — so they are not the exchange's true movers.
- Backtests model neither trading suspensions nor slippage.

---

## Origin: the forex study

The methodology comes from a MetaTrader 5 EA study (EURUSDm M15, 32 experiments) kept in a
neighbouring repository:

- `../ian-skills/mt5-ea/experiments/INDEX.md` — 41 numbered findings
- `../ian-skills/mt5-ea/quant-engine/` — backtest engine and analysis

Its final candidate reached a profit factor of ~1.73 over eight years (CI [1.05–2.49]), a ~59%
win rate, and ~7% planning drawdown. **It was never forward-tested on a live account.**

One finding from that study **replicated on Indonesian stocks**: picking parameters from past
data performed worse than fixing them (+59.3% vs +87.3%). That is why this app deliberately has
no "auto-optimize" button.

---

Not investment advice. Every number here comes from a backtest, and a backtest is not the future.
