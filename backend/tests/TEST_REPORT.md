# World Intelligence Platform — Market Test Report v2.7

**Date:** 2026-06-21  
**Suite:** `backend/tests/test_markets_comprehensive.py`  
**Result:** ✅ **136 / 136 PASSED — 0 FAILED — 0 ERRORS**  
**Runtime:** ~6.4 seconds  
**Python:** 3.10.12 | pytest 9.1.1 | FastAPI 0.100+ | httpx  

---

## Coverage Matrix — 20 Categories

| # | Category | Tests | Status | What is verified |
|---|----------|------:|--------|-----------------|
| 01 | **Unit Tests** | 19 | ✅ PASS | `lin_forecast` (8), `compute_returns` (3), `compute_sharpe` (5), `compute_volatility` (3) |
| 02 | **Integration Tests** | 16 | ✅ PASS | `/api/health`, `/api/metrics`, `/api/invest-signals`, `/api/forecast`, `/api/news`, `/api/realhistory` |
| 03 | **State Machine** | 6 | ✅ PASS | mem→db→None transitions, back-fill after DB hit, overwrite semantics |
| 04 | **Time-Travel Mocking** | 4 | ✅ PASS | TTL boundary (MEM_PRICE_TTL-1 keeps, +1 evicts), DB age check, news TTL |
| 05 | **Consistent Ticks** | 3 | ✅ PASS | Same price returned in 10 rapid reads, history list unchanged |
| 06 | **Memory Leaks** | 3 | ✅ PASS | 500 unique symbols written + read, 1000 overwrites stay coherent, no None values stored |
| 07 | **Thread Safety** | 4 | ✅ PASS | 50 concurrent writers (no exception), data integrity check, 100 concurrent readers, deadlock probe |
| 08 | **Sharpe Ratio** | 6 | ✅ PASS | Bull>0, Bear<0, higher RF lowers ratio, formula exact match, flat→None, too-short→None |
| 09 | **Sortino Ratio** | 6 | ✅ PASS | Volatile→float, strictly-rising→None, valid-for-volatile, bull Sortino≥Sharpe, crash→negative, too-short→None |
| 10 | **Transaction Costs** | 5 | ✅ PASS | Round-trip reduces gross, break-even spread, loss amplified, forecast TC, 10% TC kills profit |
| 11 | **Survivorship Bias** | 6 | ✅ PASS | Delisted→404, not in YFINANCE_MAP, no phantom cache, metrics 404 for uncached, unlisted excluded from signals, all tickers documented |
| 12 | **Look-Ahead Bias** | 4 | ✅ PASS | Forecast extrapolates forward, extra bar shifts forecast, invest-signals forecast projects trend, output is floats only |
| 13 | **Zero Liquidity** | 8 | ✅ PASS | Empty history→[], single price→flat, invest-signals skips short, metrics 404, all metrics return None/0 for empty |
| 14 | **Order Rejections** | 6 | ✅ PASS | Invalid symbol→404, unknown forecast symbol→404, unknown news region→400, metrics unknown→404, no empty tickers, YAHOO⊆YFINANCE |
| 15 | **Partial Fills** | 6 | ✅ PASS | 2-bar forecast, 5-bar forecast, 7-bar metrics, 3-bar endpoint, exactly 14 bars skipped, exactly 15 bars included |
| 16 | **Connection Drops** | 4 | ✅ PASS | ConnectError→None, TimeoutException→None, RemoteProtocolError→None, one drop in batch doesn't abort rest |
| 17 | **Rate Limiting (429)** | 4 | ✅ PASS | Yahoo 429→None, 429 batch→all empty dict, 30 rapid health→all 200, 5× invest-signals→all 200 |
| 18 | **Max Drawdown** | 6 | ✅ PASS | -50% trough, 0% monotone, >90% wipeout, multiple-peak reset, always ≤0, invest-signals field ≤0 |
| 19 | **Stale Data Timeout** | 4 | ✅ PASS | TTL-1 valid, TTL+1 evicted, stale mem falls through to DB, stale news evicted |
| 20 | **Rapid Concurrent Reqs** | 4 | ✅ PASS | 30 health→all 200, 10 concurrent forecast threads, 10 concurrent invest-signals, no cache corruption under 50-thread load |

---

## Bug Fixes Applied (v2.7)

| File | Fix | Category |
|------|-----|----------|
| `market_server.py` | `init_db()` auto-heals corrupt / WAL-incompatible DB — switches to `/tmp` instead of crashing | Resilience |
| `market_server.py` | Added `compute_returns`, `compute_sharpe`, `compute_sortino`, `compute_max_drawdown`, `compute_volatility` | Sharpe, Sortino, Drawdown |
| `market_server.py` | `get_invest_signals` now returns `sharpe`, `sortino`, `max_drawdown`, `volatility` per symbol | Integration |
| `market_server.py` | New `GET /api/metrics/{symbol}` endpoint | Integration |
| `market_server.py` | Version bumped **2.6.0 → 2.7.0** | All |

---

## New Endpoint Added

```
GET /api/metrics/{symbol}
```
Returns financial metrics for any cached symbol:

```json
{
  "symbol": "GOLD",
  "bars": 90,
  "sharpe": 1.2345,
  "sortino": 1.8901,
  "max_drawdown": -12.34,
  "volatility_pct": 18.76,
  "current_price": 1987.50,
  "change_pct": 0.42
}
```

Pre-load history first via `/api/metals`, `/api/indices`, or `/api/realhistory/{symbol}`.

---

## How to Run

```bash
cd backend
pytest tests/test_markets_comprehensive.py -v --tb=short
```

All 136 tests complete in ~6 seconds without a live server or internet connection.  
Integration tests use FastAPI's built-in `TestClient` with cache seeded in-memory.  
Connection Drop and Rate Limiting tests use `unittest.mock` to patch `httpx`.

---

*Generated automatically after pytest run on 2026-06-21.*
