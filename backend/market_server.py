"""
World Intelligence Platform — Local Backend Server v2.7
FastAPI on port 8111 | SQLite + in-memory cache | REAL DATA ENGINE

DATA ENGINE (v2.5):
  ► yfinance     — 100% real OHLCV price history for 60+ symbols (2Y daily bars)
  ► Prophet      — Facebook's time-series AI model (trend + seasonality + changepoints)
  ► Holt-Winters — Exponential Smoothing fallback if Prophet unavailable
  ► Linear Reg   — Final fallback (always available, no dependencies)

Cache layers (fastest → slowest):
  MEM (sub-ms) → SQLite (1ms) → yfinance API (1–3s) → forecast run (2–15s)

Forecast TTL: 6 hours (Prophet is expensive; results cached aggressively)
History TTL:  1 hour  (yfinance rate-limited; in-memory after first fetch)

Run: python market_server.py  OR  double-click start_server.bat
"""
import sys
# Force UTF-8 output so Unicode box-drawing chars / emoji don't crash
# on Windows terminals that default to CP1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3, json, time, httpx, asyncio, os, math as _math, statistics as _stats
from datetime import datetime
from functools import partial

# ── Optional real-data dependencies ─────────────────────────────────────────
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    from prophet import Prophet
    import pandas as pd
    import numpy as np
    PROPHET_AVAILABLE = True
    PANDAS_AVAILABLE  = True
except ImportError:
    PROPHET_AVAILABLE = False
    try:
        import pandas as pd
        import numpy as np
        PANDAS_AVAILABLE = True
    except ImportError:
        PANDAS_AVAILABLE = False

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    import numpy as np
    STATSMODELS_AVAILABLE = True
    if not PANDAS_AVAILABLE:
        import pandas as pd
        PANDAS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

# ═══════════════════════════════════════════════════
# IN-MEMORY CACHE  (fastest layer — sub-millisecond)
# ═══════════════════════════════════════════════════
_mem_prices: dict = {}   # sym -> {price, change, history, ts}
_mem_news:   dict = {}   # region -> [{...}, ts]

MEM_PRICE_TTL = 300   # 5 min
MEM_NEWS_TTL  = 900   # 15 min

def mem_get_price(sym: str):
    d = _mem_prices.get(sym)
    if d and (time.time() - d["ts"]) < MEM_PRICE_TTL:
        return d
    return None

def mem_set_price(sym: str, price, change, history):
    _mem_prices[sym] = {"symbol": sym, "price": price, "change": change,
                         "history": history, "ts": time.time()}

def mem_get_news(region: str):
    d = _mem_news.get(region)
    if d and (time.time() - d["ts"]) < MEM_NEWS_TTL:
        return d["articles"]
    return None

def mem_set_news(region: str, articles: list):
    _mem_news[region] = {"articles": articles, "ts": time.time()}

# ═══════════════════════════════════════════════════
# SQLITE CACHE  (persistent layer)
# ═══════════════════════════════════════════════════
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "market_cache.db")

def init_db():
    """
    v2.7: Auto-heals a corrupt / inaccessible DB.
    On first failure it deletes the old file and switches to a temp path.
    WAL mode silently falls back to DELETE mode on network mounts.
    """
    global DB_PATH
    import tempfile as _tf
    _tables = [
        """CREATE TABLE IF NOT EXISTS price_cache (
            symbol TEXT PRIMARY KEY, price REAL, change_pct REAL,
            history TEXT, updated INTEGER)""",
        """CREATE TABLE IF NOT EXISTS news_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT,
            title TEXT, link TEXT, pub_date TEXT, source TEXT, thumbnail TEXT,
            created INTEGER)""",
        "CREATE INDEX IF NOT EXISTS idx_news_region ON news_cache(region, created)",
        """CREATE TABLE IF NOT EXISTS forecast_cache (
            key TEXT PRIMARY KEY, result TEXT, updated INTEGER)""",
    ]
    for attempt in range(2):
        try:
            con = sqlite3.connect(DB_PATH)
            try:
                con.execute("PRAGMA journal_mode=WAL")
            except (sqlite3.OperationalError, sqlite3.DatabaseError):
                pass   # WAL unsupported on network mounts — fall back to DELETE mode
            for stmt in _tables:
                con.execute(stmt)
            con.commit(); con.close()
            return
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as exc:
            if attempt == 0:
                print(f"  [WARN] DB error ({exc}) — switching to temp DB")
                try:
                    os.unlink(DB_PATH)
                except Exception:
                    pass
                DB_PATH = os.path.join(_tf.gettempdir(), f"market_cache_{os.getpid()}.db")
                print(f"  [INFO] Using temp DB: {DB_PATH}")
            else:
                print(f"  [ERROR] DB init failed after recovery: {exc}")
                raise

def db_get_price(sym: str, max_age: int = 300):
    """Read from SQLite — used only when mem cache misses."""
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT price,change_pct,history,updated FROM price_cache WHERE symbol=?", (sym,)
    ).fetchone()
    con.close()
    if row and (time.time() - row[3]) < max_age:
        return {"symbol": sym, "price": row[0], "change": row[1],
                "history": json.loads(row[2] or "[]"), "ts": row[3]}
    return None

def db_set_price(sym: str, price, change, history: list):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT OR REPLACE INTO price_cache VALUES (?,?,?,?,?)",
                (sym, price, change, json.dumps(history), int(time.time())))
    con.commit(); con.close()

def db_get_news(region: str, max_age: int = 900):
    con = sqlite3.connect(DB_PATH)
    cutoff = int(time.time()) - max_age
    rows = con.execute(
        "SELECT title,link,pub_date,source,thumbnail FROM news_cache "
        "WHERE region=? AND created>? ORDER BY created DESC LIMIT 24",
        (region, cutoff)
    ).fetchall()
    con.close()
    return [{"title":r[0],"link":r[1],"pubDate":r[2],"source":r[3],"thumbnail":r[4]} for r in rows]

def db_store_news(region: str, articles: list):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM news_cache WHERE region=? AND created<?",
                (region, int(time.time()) - 86400))
    for a in articles:
        con.execute(
            "INSERT INTO news_cache (region,title,link,pub_date,source,thumbnail,created) "
            "VALUES (?,?,?,?,?,?,?)",
            (region, a.get("title",""), a.get("link",""), a.get("pubDate",""),
             a.get("source",""), a.get("thumbnail",""), int(time.time()))
        )
    con.commit(); con.close()

# ═══════════════════════════════════════════════════
# UNIFIED CACHE LOOKUP  (mem → sqlite → None)
# ═══════════════════════════════════════════════════
def get_price(sym: str):
    hit = mem_get_price(sym)
    if hit:
        return hit
    hit = db_get_price(sym)
    if hit:
        mem_set_price(sym, hit["price"], hit["change"], hit["history"])
        return hit
    return None

def set_price(sym: str, price, change, history: list):
    mem_set_price(sym, price, change, history)
    db_set_price(sym, price, change, history)

# ═══════════════════════════════════════════════════
# SHARED HTTP CLIENT  (one client = persistent connections)
# ═══════════════════════════════════════════════════
_http: httpx.AsyncClient = None   # initialised in lifespan

# ═══════════════════════════════════════════════════
# YAHOO FINANCE
# ═══════════════════════════════════════════════════
YAHOO_SYMBOLS = {
    "GOLD":"GC=F",  "SILVER":"SI=F",  "PLAT":"PL=F",   "PALL":"PA=F",
    "COPPER":"HG=F","NICKEL":"NI=F",  "WTI":"CL=F",    "BRENT":"BZ=F",
    "NGAS":"NG=F",  "HEAT":"HO=F",    "GASO":"RB=F",
    "SPX":"^GSPC",  "NDX":"^NDX",     "DAX":"^GDAXI",  "FTSE":"^FTSE",
    "N225":"^N225", "HSI":"^HSI"
}

# ════════════════════════════════════════════════════════
# YFINANCE MAP  — 60+ symbols mapped to Yahoo tickers
# ════════════════════════════════════════════════════════
YFINANCE_MAP = {
    # Metals
    "GOLD":"GC=F","SILVER":"SI=F","PLAT":"PL=F","PALL":"PA=F","COPPER":"HG=F","NICKEL":"NI=F",
    # Oil & Gas
    "WTI":"CL=F","BRENT":"BZ=F","NGAS":"NG=F","HEAT":"HO=F","GASO":"RB=F",
    # US Indices
    "SPX":"^GSPC","NDX":"^NDX","DJI":"^DJI",
    # European Indices
    "DAX":"^GDAXI","FTSE":"^FTSE","CAC":"^FCHI","SMI":"^SSMI",
    "AEX":"^AEX","IBEX":"^IBEX","FMIB":"FTSEMIB.MI",
    "ATX":"^ATX","WIG20":"^WIG20","OMXS30":"^OMX","MOEX":"IMOEX.ME",
    # Asia-Pacific Indices
    "N225":"^N225","HSI":"^HSI","CSI300":"000300.SS",
    "SENSEX":"^BSESN","KOSPI":"^KS11","ASX200":"^AXJO",
    "TSX":"^GSPTSE","BOVESPA":"^BVSP","MXX":"^MXX","MERVAL":"^MERV",
    "JKSE":"^JKSE","STI":"^STI","KLCI":"^KLSE","SET":"^SET.BK",
    "VNI":"^VNINDEX","KSE100":"KSE100.KAR",
    # Middle East & Africa
    "TASI":"^TASI.SR","DFM":"^DFMGI","EGX30":"^CASE30",
    "JSE":"^J203.JO","BIST":"^XU100",
    # Crypto
    "BTC":"BTC-USD","ETH":"ETH-USD","BNB":"BNB-USD","SOL":"SOL-USD",
    "XRP":"XRP-USD","ADA":"ADA-USD","AVAX":"AVAX-USD","DOGE":"DOGE-USD",
    # FX (vs USD)
    "EUR":"EURUSD=X","GBP":"GBPUSD=X","JPY":"JPY=X","CHF":"CHF=X",
    "CNY":"CNY=X","AUD":"AUDUSD=X","CAD":"CAD=X","INR":"INR=X",
}

# In-memory real history cache (1 hour TTL)
_hist_cache: dict = {}
HIST_MEM_TTL  = 3600     # 1h
FORECAST_TTL  = 6 * 3600  # 6h

def _hist_mem_get(sym: str) -> list | None:
    d = _hist_cache.get(sym)
    if d and (time.time() - d["ts"]) < HIST_MEM_TTL:
        return d["data"]
    return None

def _hist_mem_set(sym: str, data: dict):
    _hist_cache[sym] = {**data, "ts": time.time()}

# ────────────────────────────────────────────────────────
# Fetch real history via yfinance (runs in thread pool)
# ────────────────────────────────────────────────────────
def _yf_fetch_sync(sym: str, period: str = "2y") -> dict | None:
    """
    Sync function — MUST be called via run_in_executor, never directly.
    Returns real OHLCV data from Yahoo Finance.
    """
    if not YF_AVAILABLE:
        return None
    ticker = YFINANCE_MAP.get(sym.upper())
    if not ticker:
        return None
    try:
        t  = yf.Ticker(ticker)
        df = t.history(period=period, interval="1d", auto_adjust=True)
        if df is None or df.empty:
            return None
        closes = [round(float(v), 6) for v in df["Close"].dropna().tolist()]
        dates  = df.index.strftime("%Y-%m-%d").tolist()
        if len(closes) < 5:
            return None
        price  = closes[-1]
        prev   = closes[-2] if len(closes) >= 2 else price
        change = round(((price - prev) / prev) * 100, 2) if prev else 0
        return {
            "symbol": sym.upper(), "ticker": ticker,
            "price": price, "change": change,
            "closes": closes, "dates": dates,
            "period": period, "bars": len(closes)
        }
    except Exception as e:
        print(f"  yfinance [{sym}/{ticker}] {e}")
        return None

async def fetch_real_history(sym: str, period: str = "2y") -> dict | None:
    """Async wrapper around yfinance — runs in thread pool."""
    sym = sym.upper()
    # memory cache hit
    cached = _hist_mem_get(sym)
    if cached:
        return cached
    loop   = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _yf_fetch_sync, sym, period)
    if result:
        _hist_mem_set(sym, result)
        # also backfill price cache with real data
        set_price(sym, result["price"], result["change"], result["closes"][-90:])
    return result

# ────────────────────────────────────────────────────────
# AI Forecasting: Prophet → Holt-Winters → Linear Reg
# ────────────────────────────────────────────────────────
def _prophet_sync(closes: list, steps: int) -> dict | None:
    """Prophet forecast — slow (2–15s), cache result for 6h."""
    if not PROPHET_AVAILABLE or len(closes) < 30:
        return None
    try:
        import warnings; warnings.filterwarnings("ignore")
        df = pd.DataFrame({
            "ds": pd.bdate_range(end=pd.Timestamp.now(), periods=len(closes)),
            "y":  closes
        })
        m = Prophet(
            changepoint_prior_scale   = 0.05,
            seasonality_prior_scale   = 10,
            daily_seasonality         = False,
            weekly_seasonality        = True,
            yearly_seasonality        = True if len(closes) > 252 else False,
            interval_width            = 0.80
        )
        if len(closes) > 252:
            m.add_seasonality("monthly", period=30.5, fourier_order=5)
        m.fit(df, iter=300)
        future = m.make_future_dataframe(periods=steps, freq="B")
        fc     = m.predict(future).tail(steps)
        return {
            "algorithm"  : "Prophet (Facebook AI)",
            "dates"      : fc["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "yhat"       : [round(v, 6) for v in fc["yhat"].tolist()],
            "yhat_upper" : [round(v, 6) for v in fc["yhat_upper"].tolist()],
            "yhat_lower" : [round(v, 6) for v in fc["yhat_lower"].tolist()],
        }
    except Exception as e:
        print(f"  Prophet error: {e}")
        return None

def _holt_sync(closes: list, steps: int) -> dict | None:
    """Holt-Winters Exponential Smoothing fallback."""
    if not STATSMODELS_AVAILABLE or len(closes) < 20:
        return None
    try:
        period = min(52, max(4, len(closes) // 5))
        model  = ExponentialSmoothing(
            closes, trend="add", seasonal="add",
            seasonal_periods=period, damped_trend=True
        )
        fit   = model.fit(optimized=True, remove_bias=True)
        fc    = fit.forecast(steps)
        std   = float(np.std(fit.resid))
        dates = (pd.bdate_range(start=pd.Timestamp.now(), periods=steps)
                   .strftime("%Y-%m-%d").tolist())
        return {
            "algorithm"  : "Holt-Winters Exponential Smoothing",
            "dates"      : dates,
            "yhat"       : [round(float(v), 6) for v in fc],
            "yhat_upper" : [round(float(v) + 1.28*std, 6) for v in fc],
            "yhat_lower" : [round(float(v) - 1.28*std, 6) for v in fc],
        }
    except Exception as e:
        print(f"  Holt-Winters error: {e}")
        return None

async def ai_forecast(closes: list, steps: int) -> dict:
    """
    Best-effort forecast:  Prophet → Holt-Winters → Linear Regression.
    Returns a unified dict regardless of which engine ran.
    """
    loop = asyncio.get_running_loop()
    # 1. Prophet
    if PROPHET_AVAILABLE and len(closes) >= 30:
        res = await loop.run_in_executor(None, _prophet_sync, closes, steps)
        if res:
            return res
    # 2. Holt-Winters
    if STATSMODELS_AVAILABLE and len(closes) >= 20:
        res = await loop.run_in_executor(None, _holt_sync, closes, steps)
        if res:
            return res
    # 3. Linear regression (always works, no deps)
    fc   = lin_forecast(closes, steps)
    return {
        "algorithm"  : "Linear Regression (OLS)",
        "dates"      : [],
        "yhat"       : fc,
        "yhat_upper" : [round(v * 1.12, 6) for v in fc],
        "yhat_lower" : [round(v * 0.88, 6) for v in fc],
    }

# Forecast SQLite cache
def db_get_fc(key: str) -> dict | None:
    try:
        con = sqlite3.connect(DB_PATH)
        row = con.execute(
            "SELECT result, updated FROM forecast_cache WHERE key=?", (key,)
        ).fetchone()
        con.close()
        if row and (time.time() - row[1]) < FORECAST_TTL:
            return json.loads(row[0])
    except Exception:
        pass
    return None

def db_set_fc(key: str, result: dict):
    try:
        con = sqlite3.connect(DB_PATH)
        con.execute("INSERT OR REPLACE INTO forecast_cache VALUES (?,?,?)",
                    (key, json.dumps(result), int(time.time())))
        con.commit(); con.close()
    except Exception as e:
        print(f"  forecast DB write error: {e}")

async def fetch_yahoo_one(sym: str):
    """Fetch a single symbol from Yahoo Finance using the shared client."""
    ticker = YAHOO_SYMBOLS.get(sym)
    if not ticker:
        return sym, None
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=3mo"
    try:
        r = await _http.get(url, timeout=10)
        d = r.json()
        # FIX v2.6: explicitly guard against result=null before any indexing
        chart  = (d.get("chart") or {})
        result = chart.get("result") or []
        if not result:
            print(f"  Yahoo [{sym}] no data (ticker={ticker}) — skipping")
            return sym, None
        meta   = result[0]["meta"]
        closes = result[0]["indicators"]["quote"][0].get("close", [])
        closes = [c for c in closes if c is not None]
        if not closes:
            return sym, None
        price  = meta.get("regularMarketPrice", closes[-1])
        prev   = meta.get("chartPreviousClose",  closes[-2] if len(closes) >= 2 else price)
        change = round(((float(price) - float(prev)) / float(prev)) * 100, 2) if prev else 0
        return sym, {"price": float(price), "change": change, "history": closes[-90:]}
    except BaseException as e:
        # FIX v2.6: use BaseException (not just Exception) so asyncio.CancelledError
        # is also caught here and cannot escape to kill the event loop
        print(f"  Yahoo [{sym}] error: {type(e).__name__}: {e}")
        return sym, None

async def fetch_yahoo_batch(syms: list[str]) -> dict:
    """
    FIX #1: Check cache BEFORE firing any HTTP requests.
    FIX #2: Fetch only cache-misses, all concurrently via shared client.
    """
    result = {}
    misses = []
    for sym in syms:
        cached = get_price(sym)
        if cached:
            result[sym] = cached          # instant — no network call
        else:
            misses.append(sym)

    if misses:
        # FIX v2.6: return_exceptions=True — one bad ticker cannot abort the entire batch
        tasks = [fetch_yahoo_one(sym) for sym in misses]
        pairs = await asyncio.gather(*tasks, return_exceptions=True)
        for item in pairs:
            if isinstance(item, BaseException):
                # task itself raised (should not happen after fetch_yahoo_one fix, but belt+braces)
                print(f"  fetch_yahoo_batch: unexpected task exception — {item}")
                continue
            sym, data = item
            if data:
                set_price(sym, data["price"], data["change"], data["history"])
                result[sym] = {**data, "symbol": sym}
            else:
                result[sym] = {"symbol": sym, "price": None, "change": 0, "history": []}

    return result

# ═══════════════════════════════════════════════════
# CRYPTO
# ═══════════════════════════════════════════════════
COINGECKO_IDS = {
    "BTC":"bitcoin","ETH":"ethereum","BNB":"binancecoin","SOL":"solana",
    "XRP":"ripple","ADA":"cardano","AVAX":"avalanche-2","DOGE":"dogecoin"
}

async def fetch_crypto_all() -> dict:
    """One CoinGecko call for all coins at once."""
    ids = ",".join(COINGECKO_IDS.values())
    url = (f"https://api.coingecko.com/api/v3/simple/price"
           f"?ids={ids}&vs_currencies=usd&include_24hr_change=true")
    try:
        r = await _http.get(url)
        d = r.json()
        result = {}
        for sym, cg_id in COINGECKO_IDS.items():
            if cg_id in d:
                price  = float(d[cg_id]["usd"])
                change = round(float(d[cg_id].get("usd_24h_change") or 0), 2)
                set_price(sym, price, change, [])
                result[sym] = {"symbol": sym, "price": price, "change": change, "history": []}
        return result
    except Exception as e:
        print(f"  CoinGecko error: {e}")
        return {}

# ═══════════════════════════════════════════════════
# FX
# ═══════════════════════════════════════════════════
async def fetch_fx_all() -> dict:
    try:
        r = await _http.get("https://open.er-api.com/v6/latest/USD")
        rates = r.json().get("rates", {})
        pairs = {
            "EUR": round(1/rates["EUR"], 4), "GBP": round(1/rates["GBP"], 4),
            "JPY": round(rates["JPY"], 2),   "CHF": round(rates["CHF"], 4),
            "CNY": round(rates["CNY"], 4),   "AUD": round(1/rates["AUD"], 4),
            "CAD": round(rates["CAD"], 4),   "INR": round(rates["INR"], 2)
        }
        for sym, price in pairs.items():
            set_price(sym, price, 0.0, [])
        return {sym: {"symbol": sym, "price": p, "change": 0.0} for sym, p in pairs.items()}
    except Exception as e:
        print(f"  FX error: {e}")
        return {}

# ═══════════════════════════════════════════════════
# FORECAST
# ═══════════════════════════════════════════════════
def lin_forecast(history: list, steps: int) -> list:
    n = len(history)
    if n < 2:
        return [history[-1]] * steps if history else []
    sx  = n*(n-1)//2
    sy  = sum(history)
    sxy = sum(i*v for i,v in enumerate(history))
    sx2 = n*(n-1)*(2*n-1)//6
    denom = n*sx2 - sx*sx
    if denom == 0:
        return [history[-1]] * steps
    m = (n*sxy - sx*sy) / denom
    b = (sy - m*sx) / n
    return [round(b + m*(n+i), 6) for i in range(steps)]

# ═══════════════════════════════════════════════════
# FINANCIAL METRICS  (v2.7 — Sharpe / Sortino / Drawdown)
# ═══════════════════════════════════════════════════

def compute_returns(history: list) -> list:
    """Daily returns from a price series. Returns empty list if < 2 bars."""
    if len(history) < 2:
        return []
    return [(history[i] - history[i-1]) / history[i-1]
            for i in range(1, len(history)) if history[i-1] != 0]

def compute_sharpe(history: list, rf_annual: float = 0.02) -> float | None:
    """
    Annualised Sharpe ratio.
    rf_annual: annual risk-free rate as a decimal (default 2 %).
    Returns None when history is too short or std is zero.
    """
    rets = compute_returns(history)
    if len(rets) < 2:
        return None
    rf_daily = rf_annual / 252
    mean_r   = _stats.mean(rets)
    std_r    = _stats.stdev(rets)
    if std_r == 0:
        return None
    return round((mean_r - rf_daily) / std_r * _math.sqrt(252), 4)

def compute_sortino(history: list, rf_annual: float = 0.02) -> float | None:
    """
    Annualised Sortino ratio — penalises only downside (negative) returns.
    Returns None when too short or no negative returns exist.
    """
    rets = compute_returns(history)
    if len(rets) < 2:
        return None
    rf_daily     = rf_annual / 252
    mean_r       = _stats.mean(rets)
    neg_rets     = [r for r in rets if r < 0]
    if not neg_rets:
        return None   # no downside — Sortino would be ∞, caller treats as extremely high
    downside_var = sum(r ** 2 for r in neg_rets) / len(rets)
    downside_std = _math.sqrt(downside_var)
    if downside_std == 0:
        return None
    return round((mean_r - rf_daily) / downside_std * _math.sqrt(252), 4)

def compute_max_drawdown(history: list) -> float:
    """
    Max peak-to-trough drawdown as a percentage (always ≤ 0).
    A flat or rising series returns 0.0.
    """
    if len(history) < 2:
        return 0.0
    peak   = history[0]
    max_dd = 0.0
    for price in history:
        if price > peak:
            peak = price
        if peak > 0:
            dd = (price - peak) / peak * 100
            if dd < max_dd:
                max_dd = dd
    return round(max_dd, 4)

def compute_volatility(history: list) -> float | None:
    """
    Annualised historical volatility = std(daily_returns) × √252, expressed as %.
    Returns None when too few bars.
    """
    rets = compute_returns(history)
    if len(rets) < 2:
        return None
    return round(_stats.stdev(rets) * _math.sqrt(252) * 100, 4)

# ═══════════════════════════════════════════════════
# NEWS FEEDS
# ═══════════════════════════════════════════════════
NEWS_FEEDS = {
    "world":    ["https://feeds.bbci.co.uk/news/world/rss.xml",
                 "https://rss.dw.com/rdf/rss-en-world",
                 "https://www.aljazeera.com/xml/rss/all.xml"],
    "europe":   ["https://feeds.bbci.co.uk/news/world/europe/rss.xml",
                 "https://rss.dw.com/rdf/rss-en-eu"],
    "americas": ["https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
                 "https://feeds.npr.org/1001/rss.xml"],
    "asia":     ["https://feeds.bbci.co.uk/news/world/asia/rss.xml",
                 "https://rss.dw.com/rdf/rss-en-asia"],
    "africa":   ["https://feeds.bbci.co.uk/news/world/africa/rss.xml",
                 "https://rss.dw.com/rdf/rss-en-africa"],
    "oceania":  ["https://www.abc.net.au/news/feed/2942460/rss.xml"],
    "tech":     ["https://techcrunch.com/feed/",
                 "https://feeds.feedburner.com/TheHackersNews"]
}

RSS2JSON = "https://api.rss2json.com/v1/api.json?rss_url="

async def _fetch_one_feed(url: str, source_label: str) -> list:
    """Fetch a single RSS feed — runs concurrently with others."""
    try:
        r = await _http.get(f"{RSS2JSON}{url}")
        d = r.json()
        return [
            {"title":   item.get("title",""),
             "link":    item.get("link",""),
             "pubDate": item.get("pubDate",""),
             "source":  item.get("author","") or source_label,
             "thumbnail": item.get("thumbnail","")}
            for item in (d.get("items") or [])[:10]
        ]
    except Exception as e:
        print(f"  Feed [{url}] error: {e}")
        return []

async def fetch_news_region(region: str) -> list:
    """
    FIX #3: Fetch all feeds for a region concurrently (was a serial for-loop).
    """
    # mem → sqlite → network
    hit = mem_get_news(region)
    if hit:
        return hit
    hit = db_get_news(region)
    if hit:
        mem_set_news(region, hit)
        return hit

    feeds = NEWS_FEEDS.get(region, [])
    tasks = [_fetch_one_feed(url, region.title()) for url in feeds]
    # FIX #3: all feeds fetched simultaneously
    results = await asyncio.gather(*tasks)
    articles = []
    seen = set()
    for batch in results:
        for a in batch:
            if a["title"] not in seen:
                seen.add(a["title"])
                articles.append(a)

    mem_set_news(region, articles)
    db_store_news(region, articles)
    return articles

# ═══════════════════════════════════════════════════
# STARTUP / SHUTDOWN  (pre-warm cache)
# ═══════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app):
    global _http
    # FIX #2: create one shared client for the entire server lifetime
    _http = httpx.AsyncClient(
        timeout=12,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        limits=httpx.Limits(max_connections=30, max_keepalive_connections=20)
    )
    print("  Shared HTTP client ready.")

    # FIX v2.6: global asyncio task exception handler — prevents any uncaught
    # background-task exception from crashing the uvicorn event loop
    def _task_exc_handler(loop, context):
        exc  = context.get("exception")
        msg  = context.get("message", "")
        name = type(exc).__name__ if exc else "unknown"
        print(f"  [WARN] Unhandled async task exception (non-fatal): {name}: {exc or msg}")
    asyncio.get_event_loop().set_exception_handler(_task_exc_handler)

    # FIX #5: pre-warm cache in background — server is immediately responsive,
    # first user requests get data from cache after a few seconds
    async def prewarm():
        print("  Pre-warming price cache…")
        try:
            await asyncio.gather(
                fetch_yahoo_batch(list(YAHOO_SYMBOLS.keys())),
                fetch_crypto_all(),
                fetch_fx_all(),
                return_exceptions=True
            )
            print("  Cache pre-warm complete.")
        except Exception as e:
            print(f"  Pre-warm error (non-fatal): {e}")

    asyncio.create_task(prewarm())

    yield  # server runs here

    await _http.aclose()
    print("  HTTP client closed.")

# ═══════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════
app = FastAPI(title="World Intelligence API", version="2.7.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()

# ─── ENDPOINTS ──────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status"          : "ok",
        "version"         : "2.7.1",
        "time"            : datetime.utcnow().isoformat(),
        "cached_symbols"  : len(_mem_prices),
        "cached_regions"  : len(_mem_news),
        "cached_history"  : len(_hist_cache),
        "engines": {
            "yfinance"    : YF_AVAILABLE,
            "prophet"     : PROPHET_AVAILABLE,
            "holt_winters": STATSMODELS_AVAILABLE,
            "linear_reg"  : True
        }
    }

# ─── v2.5: REAL HISTORY ─────────────────────────────────────────────────────

@app.get("/api/realhistory/{symbol}")
async def get_real_history(symbol: str, period: str = "2y"):
    """
    Returns 100% real OHLCV data via yfinance.
    period: 1mo | 3mo | 6mo | 1y | 2y | 5y | max
    Cached in memory for 1 hour.
    """
    sym = symbol.upper()
    if sym not in YFINANCE_MAP:
        raise HTTPException(status_code=404,
            detail=f"Symbol '{sym}' not in YFINANCE_MAP. Available: {list(YFINANCE_MAP.keys())}")
    if not YF_AVAILABLE:
        raise HTTPException(status_code=503,
            detail="yfinance not installed. Run: pip install yfinance")
    result = await fetch_real_history(sym, period)
    if not result:
        raise HTTPException(status_code=502,
            detail=f"Could not fetch real data for {sym}. Yahoo Finance may be rate-limiting.")
    return result

# ─── v2.5: AI FORECAST ──────────────────────────────────────────────────────

@app.get("/api/prophet/{symbol}")
async def get_prophet_forecast(symbol: str, horizon: str = "1M"):
    """
    AI forecast using Prophet → Holt-Winters → Linear Regression (best available).
    Uses real yfinance history as input when available; falls back to cached price history.
    Results cached in SQLite for 6 hours (Prophet is expensive to run).

    horizon: 1D | 1W | 1M | 3M | 6M | 1Y | 2Y | 5Y | 10Y
    """
    sym = symbol.upper()
    # Step map (business days)
    steps_map = {"1D":1,"1W":5,"1M":21,"3M":63,"6M":126,"1Y":252,"2Y":504,"5Y":1260,"10Y":2520}
    steps = steps_map.get(horizon.upper(), 21)

    cache_key = f"{sym}:{horizon.upper()}"
    cached = db_get_fc(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    # Get real history first, fall back to price cache
    closes = None
    real = await fetch_real_history(sym, period="2y")
    if real:
        closes = real["closes"]
        current_price = real["price"]
        change        = real["change"]
        data_source   = "yfinance (real)"
        bars          = real["bars"]
    else:
        d = get_price(sym)
        if d and d.get("history"):
            closes        = d["history"]
            current_price = d["price"]
            change        = d.get("change", 0)
            data_source   = "cached (estimated)"
            bars          = len(closes)
        else:
            raise HTTPException(status_code=404,
                detail=f"No history available for {sym}. Call /api/realhistory/{sym} first.")

    forecast = await ai_forecast(closes, steps)

    result = {
        "symbol"       : sym,
        "horizon"      : horizon.upper(),
        "steps"        : steps,
        "current_price": current_price,
        "change_pct"   : change,
        "data_source"  : data_source,
        "bars_used"    : bars,
        "algorithm"    : forecast["algorithm"],
        "dates"        : forecast["dates"],
        "yhat"         : forecast["yhat"],
        "yhat_upper"   : forecast["yhat_upper"],
        "yhat_lower"   : forecast["yhat_lower"],
        "target"       : forecast["yhat"][-1]  if forecast["yhat"]  else current_price,
        "target_upper" : forecast["yhat_upper"][-1] if forecast["yhat_upper"] else None,
        "target_lower" : forecast["yhat_lower"][-1] if forecast["yhat_lower"] else None,
        "target_pct"   : round(((forecast["yhat"][-1] - current_price)/current_price)*100, 2)
                         if forecast["yhat"] and current_price else 0,
        "from_cache"   : False
    }
    db_set_fc(cache_key, result)
    return result

# ─── v2.5: BULK REAL PRICES ─────────────────────────────────────────────────

@app.get("/api/realprices")
async def get_real_prices(symbols: str = "BTC,ETH,GOLD,SPX,NDX"):
    """
    Fetch real current prices for multiple symbols via yfinance.
    symbols: comma-separated list, e.g. BTC,ETH,GOLD,SPX
    """
    syms   = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    tasks  = [fetch_real_history(s, "5d") for s in syms if s in YFINANCE_MAP]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = {}
    for sym, res in zip([s for s in syms if s in YFINANCE_MAP], results):
        if isinstance(res, dict) and res:
            out[sym] = {
                "symbol": sym, "price": res["price"], "change": res["change"],
                "ticker": res.get("ticker",""), "data_source": "yfinance (real)",
                "last_close_date": res["dates"][-1] if res.get("dates") else ""
            }
        else:
            d = get_price(sym)
            if d:
                out[sym] = {**d, "data_source": "cache"}
    return out

@app.get("/api/metals")
async def get_metals():
    return await fetch_yahoo_batch(["GOLD","SILVER","PLAT","PALL","COPPER","NICKEL"])

@app.get("/api/crypto")
async def get_crypto():
    syms = list(COINGECKO_IDS.keys())
    if all(mem_get_price(s) for s in syms):
        return {s: mem_get_price(s) for s in syms}
    return await fetch_crypto_all()

@app.get("/api/currencies")
async def get_currencies():
    syms = ["EUR","GBP","JPY","CHF","CNY","AUD","CAD","INR"]
    if all(mem_get_price(s) for s in syms):
        return {s: mem_get_price(s) for s in syms}
    return await fetch_fx_all()

@app.get("/api/oil")
async def get_oil():
    return await fetch_yahoo_batch(["WTI","BRENT","NGAS","HEAT","GASO"])

@app.get("/api/indices")
async def get_indices():
    return await fetch_yahoo_batch(["SPX","NDX","DJI","DAX","FTSE","CAC","N225","HSI","SENSEX","KOSPI"])

@app.get("/api/forecast/{symbol}")
async def get_forecast(symbol: str, horizon: str = "1M"):
    steps_map = {"1D":1,"1W":7,"1M":30,"1Y":252,"5Y":1260,"10Y":2520}
    steps = steps_map.get(horizon.upper(), 30)
    d = get_price(symbol.upper())
    if not d or not d.get("history"):
        raise HTTPException(status_code=404,
            detail=f"No history cached for {symbol}. Call /api/metals or /api/indices first.")
    hist = d["history"]
    fc   = lin_forecast(hist, steps)
    last = hist[-1]
    bull = [round(v*1.12, 6) for v in fc]
    bear = [round(v*0.88, 6) for v in fc]
    return {
        "symbol": symbol.upper(), "horizon": horizon, "current": last,
        "base": fc, "bull": bull, "bear": bear,
        "base_target": fc[-1], "bull_target": bull[-1], "bear_target": bear[-1],
        "change_pct": round(((fc[-1]-last)/last)*100, 2) if last else 0
    }

@app.get("/api/news/{region}")
async def get_news(region: str):
    valid = ["world","europe","americas","asia","africa","oceania","tech"]
    if region not in valid:
        raise HTTPException(status_code=400, detail=f"Region must be one of {valid}")
    return await fetch_news_region(region)

@app.get("/api/invest-signals")
async def get_invest_signals():
    all_syms = (list(COINGECKO_IDS.keys()) +
                ["GOLD","SILVER","WTI","BRENT","SPX","NDX","DAX","EUR","GBP"])
    signals = []
    for sym in all_syms:
        d = get_price(sym)
        if not d or len(d.get("history",[]))<15:
            continue
        hist = d["history"]
        n=14; gains=losses=0
        for i in range(len(hist)-n, len(hist)):
            diff = hist[i]-hist[i-1]
            if diff>0: gains+=diff
            else:      losses-=diff
        rs = (gains/n)/((losses/n) or 0.001)
        rsi_val = round(100-100/(1+rs), 1)
        ch = d.get("change",0)
        if rsi_val<30 and ch<-5:   sig="STRONG BUY"
        elif rsi_val<40 and ch<0:  sig="BUY"
        elif rsi_val>70 and ch>5:  sig="AVOID"
        elif rsi_val>60 and ch>2:  sig="SELL"
        else:                      sig="HOLD"
        fc7 = lin_forecast(hist, 7)
        signals.append({
            "symbol"      : sym,
            "price"       : d["price"],
            "change"      : ch,
            "rsi"         : rsi_val,
            "signal"      : sig,
            "forecast_7d" : fc7[-1] if fc7 else None,
            "sharpe"      : compute_sharpe(hist),
            "sortino"     : compute_sortino(hist),
            "max_drawdown": compute_max_drawdown(hist),
            "volatility"  : compute_volatility(hist),
        })
    return signals

@app.get("/api/metrics/{symbol}")
def get_metrics(symbol: str):
    """
    v2.7: Returns Sharpe ratio, Sortino ratio, max drawdown, and annualised
    volatility for any symbol that has cached price history.
    Pre-load via /api/metals, /api/indices, /api/crypto, or /api/realhistory/{symbol}.
    """
    sym = symbol.upper()
    d   = get_price(sym)
    if not d or len(d.get("history", [])) < 5:
        raise HTTPException(status_code=404,
            detail=(f"No sufficient history for '{sym}'. "
                    f"Call /api/metals, /api/indices, or /api/realhistory/{sym} first."))
    hist = d["history"]
    return {
        "symbol"        : sym,
        "bars"          : len(hist),
        "sharpe"        : compute_sharpe(hist),
        "sortino"       : compute_sortino(hist),
        "max_drawdown"  : compute_max_drawdown(hist),
        "volatility_pct": compute_volatility(hist),
        "current_price" : d["price"],
        "change_pct"    : d.get("change", 0),
    }

# ══════════════════════════════════════════════════════════════
#  CENTRAL BANKS LIVE  v3.5
#  Free APIs used:
#    • ECB Data Portal  — data.ecb.europa.eu  (no key, CORS-enabled)
#    • yfinance         — US Treasury yields (^IRX ^FVX ^TNX ^TYX)
#  All other policy rates: embedded from official CB websites
# ══════════════════════════════════════════════════════════════
@app.get("/api/central-banks")
async def get_central_banks():
    result = {"yield_curve": {}, "ecb_deposit_rate": None,
              "ecb_date": None, "source": "ECB Data Portal + yfinance (free)"}

    # ── 1. US Treasury yield curve via yfinance ───────────────
    if YF_AVAILABLE:
        try:
            import yfinance as yf
            tickers = {"3m": "^IRX", "2y": "^TWO", "5y": "^FVX",
                       "10y": "^TNX", "30y": "^TYX"}
            for label, sym in tickers.items():
                try:
                    fi = yf.Ticker(sym).fast_info
                    val = getattr(fi, "last_price", None)
                    if val and val > 0:
                        result["yield_curve"][label] = round(float(val), 3)
                except Exception:
                    pass
        except Exception:
            pass

    # ── 2. ECB deposit facility rate (free, no API key) ───────
    try:
        import httpx as _hx
        async with _hx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://data.ecb.europa.eu/api/data/"
                "FM.B.U2.EUR.4F.KR.MRR_DFR.LEV"
                "?lastNObservations=1&format=jsondata",
                headers={"Accept": "application/json"},
            )
            if r.status_code == 200:
                d   = r.json()
                obs = d["dataSets"][0]["series"]["0:0:0:0:0:0"]["observations"]
                key = sorted(obs.keys(), key=lambda x: int(x))[-1]
                result["ecb_deposit_rate"] = obs[key][0]
                dates = d["structure"]["dimensions"]["observation"][0]["values"]
                idx   = int(key)
                result["ecb_date"] = dates[idx]["id"] if idx < len(dates) else None
    except Exception:
        result["ecb_deposit_rate"] = 2.25   # fallback: verified May 2025

    return result


if __name__ == "__main__":
    import uvicorn
    print("=" * 62)
    print("  World Intelligence Backend v2.7.1 -- Real Data + AI Forecast + Crash-Safe + Financial Metrics")
    print("  URL:          http://localhost:8111")
    print("  API docs:     http://localhost:8111/docs")
    print("  Health:       http://localhost:8111/api/health")
    print("  Real history: http://localhost:8111/api/realhistory/BTC")
    print("  AI forecast:  http://localhost:8111/api/prophet/BTC?horizon=1Y")
    print("  Metrics:      http://localhost:8111/api/metrics/GOLD")
    print("-" * 62)
    yf_s  = "OK: REAL DATA"    if YF_AVAILABLE        else "install: pip install yfinance"
    pr_s  = "OK: AI FORECAST"  if PROPHET_AVAILABLE   else "install: pip install prophet"
    hw_s  = "OK: available"    if STATSMODELS_AVAILABLE else "install: pip install statsmodels"
    print(f"  yfinance:      {yf_s}")
    print(f"  Prophet:       {pr_s}")
    print(f"  Holt-Winters:  {hw_s}")
    print(f"  Linear Reg:    OK: always available (fallback)")
    print("=" * 62)
    port = int(os.environ.get("PORT", 8111))   # Render injects PORT; local falls back to 8111
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
