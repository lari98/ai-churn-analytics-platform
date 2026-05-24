"""
World Intelligence Platform — Local Backend Server
FastAPI on port 8111 | SQLite cache | Yahoo Finance + CoinGecko + Open ER API
Run: python market_server.py  OR  double-click start_server.bat
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3, json, time, httpx, asyncio, os
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI(title="World Intelligence API", version="2.3")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH = os.path.join(os.path.dirname(__file__), "market_cache.db")

# ─── DB INIT ────────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS price_cache (
        symbol TEXT PRIMARY KEY, price REAL, change_pct REAL,
        history TEXT, updated INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS news_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT,
        title TEXT, link TEXT, pub_date TEXT, source TEXT, thumbnail TEXT,
        created INTEGER)""")
    con.commit(); con.close()

init_db()

def db():
    return sqlite3.connect(DB_PATH)

def ts():
    return int(time.time())

# ─── PRICE CACHE HELPERS ────────────────────────────────────
def get_cached_price(sym: str, max_age: int = 300):
    con = db()
    row = con.execute("SELECT price,change_pct,history,updated FROM price_cache WHERE symbol=?", (sym,)).fetchone()
    con.close()
    if row and ts() - row[3] < max_age:
        return {"symbol": sym, "price": row[0], "change": row[1], "history": json.loads(row[2] or "[]")}
    return None

def set_cached_price(sym: str, price: float, change: float, history: list):
    con = db()
    con.execute("INSERT OR REPLACE INTO price_cache VALUES (?,?,?,?,?)",
                (sym, price, change, json.dumps(history), ts()))
    con.commit(); con.close()

# ─── NEWS CACHE HELPERS ─────────────────────────────────────
def get_cached_news(region: str, max_age: int = 900):
    con = db()
    cutoff = ts() - max_age
    rows = con.execute("SELECT title,link,pub_date,source,thumbnail FROM news_cache WHERE region=? AND created>? ORDER BY created DESC LIMIT 24", (region, cutoff)).fetchall()
    con.close()
    return [{"title":r[0],"link":r[1],"pubDate":r[2],"source":r[3],"thumbnail":r[4]} for r in rows]

def store_news(region: str, articles: list):
    con = db()
    # purge old
    cutoff = ts() - 86400
    con.execute("DELETE FROM news_cache WHERE region=? AND created<?", (region, cutoff))
    for a in articles:
        con.execute("INSERT INTO news_cache (region,title,link,pub_date,source,thumbnail,created) VALUES (?,?,?,?,?,?,?)",
                    (region, a.get("title",""), a.get("link",""), a.get("pubDate",""), a.get("source",""), a.get("thumbnail",""), ts()))
    con.commit(); con.close()

# ─── YAHOO FINANCE ──────────────────────────────────────────
YAHOO_SYMBOLS = {
    "GOLD":  "GC=F",  "SILVER": "SI=F",  "PLAT": "PL=F",   "PALL": "PA=F",
    "COPPER":"HG=F",  "NICKEL": "NI=F",  "WTI":  "CL=F",   "BRENT": "BZ=F",
    "NGAS":  "NG=F",  "HEAT":   "HO=F",  "GASO": "RB=F",
    "SPX":   "^GSPC", "NDX":    "^NDX",  "DAX":  "^GDAXI", "FTSE":  "^FTSE",
    "N225":  "^N225", "HSI":    "^HSI"
}

async def fetch_yahoo(sym: str):
    ticker = YAHOO_SYMBOLS.get(sym)
    if not ticker:
        return None
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=3mo"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            d = r.json()
        meta = d["chart"]["result"][0]["meta"]
        closes = d["chart"]["result"][0]["indicators"]["quote"][0].get("close", [])
        closes = [c for c in closes if c is not None]
        price = meta.get("regularMarketPrice", closes[-1] if closes else 0)
        prev = meta.get("chartPreviousClose", closes[-2] if len(closes) >= 2 else price)
        change = round(((price - prev) / prev) * 100, 2) if prev else 0
        return {"price": price, "change": change, "history": closes[-90:]}
    except Exception as e:
        print(f"Yahoo Finance error for {sym}: {e}")
        return None

# ─── CRYPTO ─────────────────────────────────────────────────
COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "SOL": "solana",  "XRP": "ripple",   "ADA": "cardano",
    "AVAX": "avalanche-2", "DOGE": "dogecoin"
}

async def fetch_crypto_prices():
    ids = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            d = r.json()
        result = {}
        for sym, cg_id in COINGECKO_IDS.items():
            if cg_id in d:
                result[sym] = {"price": d[cg_id]["usd"], "change": round(d[cg_id].get("usd_24h_change", 0), 2)}
        return result
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return {}

# ─── FX ─────────────────────────────────────────────────────
async def fetch_fx():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://open.er-api.com/v6/latest/USD")
            d = r.json()
        rates = d.get("rates", {})
        return {
            "EUR": round(1/rates["EUR"], 4), "GBP": round(1/rates["GBP"], 4),
            "JPY": round(rates["JPY"], 2),   "CHF": round(rates["CHF"], 4),
            "CNY": round(rates["CNY"], 4),   "AUD": round(1/rates["AUD"], 4),
            "CAD": round(rates["CAD"], 4),   "INR": round(rates["INR"], 2)
        }
    except Exception as e:
        print(f"FX error: {e}")
        return {}

# ─── LINEAR REGRESSION FORECAST ─────────────────────────────
def lin_forecast(history: list, steps: int) -> list:
    n = len(history)
    if n < 2:
        return [history[-1]] * steps if history else []
    sx = n*(n-1)//2; sy = sum(history); sxy = sum(i*v for i,v in enumerate(history)); sx2 = n*(n-1)*(2*n-1)//6
    m = (n*sxy - sx*sy) / (n*sx2 - sx*sx)
    b = (sy - m*sx) / n
    return [round(b + m*(n+i), 6) for i in range(steps)]

# ─── ENDPOINTS ──────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.3", "time": datetime.utcnow().isoformat()}

@app.get("/api/metals")
async def get_metals():
    metals = ["GOLD", "SILVER", "PLAT", "PALL", "COPPER", "NICKEL"]
    result = {}
    tasks = [fetch_yahoo(sym) for sym in metals]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for sym, resp in zip(metals, responses):
        cached = get_cached_price(sym)
        if cached:
            result[sym] = cached
        elif isinstance(resp, dict):
            set_cached_price(sym, resp["price"], resp["change"], resp["history"])
            result[sym] = {**resp, "symbol": sym}
        else:
            result[sym] = {"symbol": sym, "price": None, "change": 0, "history": []}
    return result

@app.get("/api/crypto")
async def get_crypto():
    prices = await fetch_crypto_prices()
    result = {}
    for sym in COINGECKO_IDS:
        cached = get_cached_price(sym, max_age=120)
        if cached:
            result[sym] = cached
        elif sym in prices:
            d = prices[sym]
            set_cached_price(sym, d["price"], d["change"], [])
            result[sym] = {**d, "symbol": sym, "history": []}
    return result

@app.get("/api/currencies")
async def get_currencies():
    fx = await fetch_fx()
    result = {}
    for sym, price in fx.items():
        set_cached_price(sym, price, 0, [])
        result[sym] = {"symbol": sym, "price": price, "change": 0}
    return result

@app.get("/api/oil")
async def get_oil():
    syms = ["WTI", "BRENT", "NGAS", "HEAT", "GASO"]
    result = {}
    tasks = [fetch_yahoo(sym) for sym in syms]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for sym, resp in zip(syms, responses):
        cached = get_cached_price(sym)
        if cached:
            result[sym] = cached
        elif isinstance(resp, dict):
            set_cached_price(sym, resp["price"], resp["change"], resp["history"])
            result[sym] = {**resp, "symbol": sym}
        else:
            result[sym] = {"symbol": sym, "price": None, "change": 0, "history": []}
    return result

@app.get("/api/indices")
async def get_indices():
    syms = ["SPX", "NDX", "DAX", "FTSE", "N225", "HSI"]
    result = {}
    tasks = [fetch_yahoo(sym) for sym in syms]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for sym, resp in zip(syms, responses):
        cached = get_cached_price(sym)
        if cached:
            result[sym] = cached
        elif isinstance(resp, dict):
            set_cached_price(sym, resp["price"], resp["change"], resp["history"])
            result[sym] = {**resp, "symbol": sym}
        else:
            result[sym] = {"symbol": sym, "price": None, "change": 0, "history": []}
    return result

@app.get("/api/forecast/{symbol}")
async def get_forecast(symbol: str, horizon: str = "1M"):
    steps_map = {"1D": 1, "1W": 7, "1M": 30, "1Y": 252, "5Y": 1260, "10Y": 2520}
    steps = steps_map.get(horizon.upper(), 30)
    cached = get_cached_price(symbol.upper())
    if not cached or not cached["history"]:
        raise HTTPException(status_code=404, detail=f"No history for {symbol}")
    history = cached["history"]
    fc = lin_forecast(history, steps)
    last = history[-1]
    bull = [round(v * 1.12, 6) for v in fc]
    bear = [round(v * 0.88, 6) for v in fc]
    return {
        "symbol": symbol.upper(),
        "horizon": horizon,
        "current": last,
        "base": fc,
        "bull": bull,
        "bear": bear,
        "base_target": fc[-1],
        "bull_target": bull[-1],
        "bear_target": bear[-1],
        "change_pct": round(((fc[-1] - last) / last) * 100, 2) if last else 0
    }

@app.get("/api/news/{region}")
async def get_news(region: str):
    valid = ["world", "europe", "americas", "asia", "africa", "oceania", "tech"]
    if region not in valid:
        raise HTTPException(status_code=400, detail=f"Region must be one of: {valid}")
    cached = get_cached_news(region)
    if cached:
        return cached
    # Fetch via rss2json
    feeds = {
        "world":    ["https://feeds.bbci.co.uk/news/world/rss.xml", "https://rss.dw.com/rdf/rss-en-world"],
        "europe":   ["https://feeds.bbci.co.uk/news/world/europe/rss.xml", "https://rss.dw.com/rdf/rss-en-eu"],
        "americas": ["https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"],
        "asia":     ["https://feeds.bbci.co.uk/news/world/asia/rss.xml"],
        "africa":   ["https://feeds.bbci.co.uk/news/world/africa/rss.xml"],
        "oceania":  ["https://www.abc.net.au/news/feed/2942460/rss.xml"],
        "tech":     ["https://techcrunch.com/feed/"]
    }
    articles = []
    async with httpx.AsyncClient(timeout=12) as client:
        for url in feeds.get(region, []):
            try:
                r = await client.get(f"https://api.rss2json.com/v1/api.json?rss_url={url}")
                d = r.json()
                for item in (d.get("items") or [])[:10]:
                    articles.append({
                        "title": item.get("title",""),
                        "link": item.get("link",""),
                        "pubDate": item.get("pubDate",""),
                        "source": item.get("author","") or region.title(),
                        "thumbnail": item.get("thumbnail","")
                    })
            except Exception as e:
                print(f"News fetch error ({url}): {e}")
    store_news(region, articles)
    return articles

@app.get("/api/invest-signals")
async def get_invest_signals():
    """Return RSI-based investment signals for all tracked assets."""
    all_syms = list(COINGECKO_IDS.keys()) + ["GOLD","SILVER","WTI","BRENT","SPX","NDX","DAX","EUR","GBP"]
    signals = []
    for sym in all_syms:
        cached = get_cached_price(sym)
        if not cached:
            continue
        hist = cached["history"]
        if len(hist) < 15:
            continue
        # RSI calculation
        n = 14
        gains = losses = 0
        for i in range(len(hist)-n, len(hist)):
            d = hist[i] - hist[i-1]
            if d > 0: gains += d
            else: losses -= d
        rs = (gains/n) / ((losses/n) or 0.001)
        rsi_val = round(100 - 100/(1+rs), 1)
        change = cached.get("change", 0)
        if rsi_val < 30 and change < -5:   sig = "STRONG BUY"
        elif rsi_val < 40 and change < 0:  sig = "BUY"
        elif rsi_val > 70 and change > 5:  sig = "AVOID"
        elif rsi_val > 60 and change > 2:  sig = "SELL"
        else:                               sig = "HOLD"
        fc_7d = lin_forecast(hist, 7)
        signals.append({
            "symbol": sym,
            "price": cached["price"],
            "change": change,
            "rsi": rsi_val,
            "signal": sig,
            "forecast_7d": fc_7d[-1] if fc_7d else None
        })
    return signals

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  World Intelligence Backend v2.3")
    print("  URL: http://localhost:8111")
    print("  API docs: http://localhost:8111/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8111, reload=False)
