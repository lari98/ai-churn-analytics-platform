"""
World Intelligence Platform — Local Backend Server v2.5
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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3, json, time, httpx, asyncio, os
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
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL")   # much faster concurrent writes
    con.execute("""CREATE TABLE IF NOT EXISTS price_cache (
        symbol TEXT PRIMARY KEY, price REAL, change_pct REAL,
        history TEXT, updated INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS news_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT,
        title TEXT, link TEXT, pub_date TEXT, source TEXT, thumbnail TEXT,
        created INTEGER)""")
    con.execute("CREATE INDEX IF NOT EXISTS idx_news_region ON news_cache(region, created)")
    # v2.5: AI forecast cache
    con.execute("""CREATE TABLE IF NOT EXISTS forecast_cache (
        key TEXT PRIMARY KEY, result TEXT, updated INTEGER)""")
    con.commit(); con.close()

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
        r = await _http.get(url)
        d = r.json()
        meta   = d["chart"]["result"][0]["meta"]
        closes = d["chart"]["result"][0]["indicators"]["quote"][0].get("close", [])
        closes = [c for c in closes if c is not None]
        price  = meta.get("regularMarketPrice", closes[-1] if closes else 0)
        prev   = meta.get("chartPreviousClose",  closes[-2] if len(closes) >= 2 else price)
        change = round(((price - prev) / prev) * 100, 2) if prev else 0
        return sym, {"price": float(price), "change": change, "history": closes[-90:]}
    except Exception as e:
        print(f"  Yahoo [{sym}] error: {e}")
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
        # FIX #2: all misses fetched concurrently (not sequentially)
        tasks = [fetch_yahoo_one(sym) for sym in misses]
        pairs = await asyncio.gather(*tasks, return_exceptions=False)
        for sym, data in pairs:
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
app = FastAPI(title="World Intelligence API", version="2.5.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()

# ─── ENDPOINTS ──────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status"          : "ok",
        "version"         : "2.5.0",
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
    # Check if all are cached first
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
    return await fetch_yahoo_batch(["SPX","NDX","DAX","FTSE","N225","HSI"])

@app.get("/api/forecast/{symbol}")
async def get_forecast(symbol: str, horizon: str = "1M"):
    steps_map = {"1D":1,"1W":7,"1M":30,"1Y":252,"5Y":1260,"10Y":2520}
    steps = steps_map.get(horizon.upper(), 30)
    d = get_price(symbol.upper())
    if not d or not d.get("history"):
        raise HTTPException(status_code=404, detail=f"No history cached for {symbol}. Call /api/metals or /api/indices first.")
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
            "symbol":sym,"price":d["price"],"change":ch,
            "rsi":rsi_val,"signal":sig,"forecast_7d":fc7[-1] if fc7 else None
        })
    return signals

if __name__ == "__main__":
    import uvicorn
    print("=" * 62)
    print("  World Intelligence Backend v2.5.0  — Real Data + AI Forecast")
    print("  URL:          http://localhost:8111")
    print("  API docs:     http://localhost:8111/docs")
    print("  Health:       http://localhost:8111/api/health")
    print("  Real history: http://localhost:8111/api/realhistory/BTC")
    print("  AI forecast:  http://localhost:8111/api/prophet/BTC?horizon=1Y")
    print("─" * 62)
    print(f"  yfinance:      {'✓ REAL DATA' if YF_AVAILABLE else '✗ install: pip install yfinance'}")
    print(f"  Prophet:       {'✓ AI FORECAST' if PROPHET_AVAILABLE else '✗ install: pip install prophet'}")
    print(f"  Holt-Winters:  {'✓ available' if STATSMODELS_AVAILABLE else '✗ install: pip install statsmodels'}")
    print(f"  Linear Reg:    ✓ always available (fallback)")
    print("=" * 62)
    uvicorn.run(app, host="0.0.0.0", port=8111, reload=False)
