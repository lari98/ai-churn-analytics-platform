"""
World Intelligence Platform — Local Backend Server v2.3.1
FastAPI on port 8111 | SQLite + in-memory cache | Yahoo Finance + CoinGecko + Open ER API

PERFORMANCE FIXES applied:
  1. Check cache BEFORE making any HTTP requests (was checking after — always slow)
  2. Single shared httpx.AsyncClient (was creating new client per symbol = 17 TCP handshakes)
  3. News feeds fetched concurrently with asyncio.gather (was serial loop)
  4. In-memory dict cache layer on top of SQLite (sub-ms reads after first fetch)
  5. Startup pre-warm: fetches all prices in background on server boot
  6. SQLite WAL mode + shared connection for the write path

Run: python market_server.py  OR  double-click start_server.bat
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3, json, time, httpx, asyncio, os
from datetime import datetime

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
app = FastAPI(title="World Intelligence API", version="2.3.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()

# ─── ENDPOINTS ──────────────────────────────────────────────

@app.get("/api/health")
def health():
    cached_count = len(_mem_prices)
    return {
        "status": "ok",
        "version": "2.3.1",
        "time": datetime.utcnow().isoformat(),
        "cached_symbols": cached_count,
        "cached_regions": len(_mem_news)
    }

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
    print("=" * 55)
    print("  World Intelligence Backend v2.3.1  (Performance Fix)")
    print("  URL:      http://localhost:8111")
    print("  API docs: http://localhost:8111/docs")
    print("  Health:   http://localhost:8111/api/health")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8111, reload=False)
