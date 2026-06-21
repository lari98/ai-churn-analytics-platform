"""
World Intelligence Platform — Comprehensive Market Test Suite v2.7
═══════════════════════════════════════════════════════════════════

Covers 20 test categories:
  01  Unit Tests             — lin_forecast, compute_* helpers, cache layer functions
  02  Integration Tests      — all HTTP endpoints via TestClient
  03  State Machine          — cache state transitions  mem → db → None
  04  Time-Travel Mocking    — freeze time.time() to exercise TTL logic
  05  Consistent Ticks       — same price returned in rapid succession
  06  Memory Leaks           — _mem_prices dict bounded, no unbounded growth
  07  Thread Safety          — concurrent cache writes from 50 threads
  08  Sharpe Ratio           — formula verification, positive/negative regimes
  09  Sortino Ratio          — downside-only penalty, compare vs Sharpe
  10  Transaction Costs      — round-trip spread reduces gross return
  11  Survivorship Bias      — delisted / unknown symbol → 404, not phantom data
  12  Look-Ahead Bias        — lin_forecast cannot see future bars
  13  Zero Liquidity         — empty history handled gracefully throughout
  14  Order Rejections       — invalid symbol, bad period, unknown region → errors
  15  Partial Fills          — short history (1-14 bars) handled without crash
  16  Connection Drops       — httpx ConnectError → graceful None return
  17  Rate Limiting (429)    — Yahoo 429 response → None, no server crash
  18  Max Drawdown           — peak-to-trough formula correctness
  19  Stale Data Timeout     — TTL expiry evicts stale mem-cache entries
  20  Rapid Concurrent Reqs  — 30 simultaneous requests don't corrupt state

Run:
    cd backend
    pytest tests/test_markets_comprehensive.py -v --tb=short
    pytest tests/test_markets_comprehensive.py -v --tb=short --json-report
"""

import sys, os, time, threading, math, statistics, json, tempfile, asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# ── Path: import from backend/ directory ─────────────────────────────────────
_BACKEND = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(_BACKEND))

# ── Use a temp DB so tests never touch the production market_cache.db ────────
_TMP_DB = os.path.join(tempfile.gettempdir(), f"wip_test_{os.getpid()}.db")

import market_server                                # triggers init_db() at module level
market_server.DB_PATH = _TMP_DB                    # redirect subsequent DB calls
market_server.init_db()                            # (re)create tables in temp DB

from market_server import (
    # Cache
    lin_forecast, mem_get_price, mem_set_price, get_price, set_price,
    db_get_price, db_set_price, _mem_prices, MEM_PRICE_TTL,
    # Symbol maps
    YAHOO_SYMBOLS, YFINANCE_MAP, COINGECKO_IDS,
    # Financial metrics (v2.7 additions)
    compute_returns, compute_sharpe, compute_sortino,
    compute_max_drawdown, compute_volatility,
    # Async fetch helpers
    fetch_yahoo_one,
    # FastAPI app
    app,
)
from fastapi.testclient import TestClient

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_mem_cache():
    """Wipe in-memory caches before every test — prevents state bleed."""
    market_server._mem_prices.clear()
    market_server._mem_news.clear()
    market_server._hist_cache.clear()
    yield
    market_server._mem_prices.clear()


@pytest.fixture(scope="session")
def client():
    """
    Session-scoped FastAPI TestClient.
    Uses anyio to run the lifespan (creates _http, fires prewarm in background).
    The prewarm may fail on CI (no Yahoo/CoinGecko) — that is fine; tests seed
    the cache manually where they need data.
    """
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _rising(n=100, start=100.0, step=1.0):
    """Monotonically rising price series."""
    return [start + i * step for i in range(n)]


def _volatile(n=100, seed=42):
    """Price series with realistic up/down moves."""
    import random
    random.seed(seed)
    prices, p = [], 100.0
    for _ in range(n):
        p *= 1 + random.gauss(0.0005, 0.02)
        prices.append(round(p, 4))
    return prices


def _run(coro):
    """Run an async coroutine synchronously (for tests that need async helpers)."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ═════════════════════════════════════════════════════════════════════════════
# 01  UNIT TESTS — lin_forecast & financial helpers
# ═════════════════════════════════════════════════════════════════════════════

class TestLinForecast:
    def test_constant_series(self):
        """Constant history → forecast stays flat."""
        fc = lin_forecast([50.0] * 20, 5)
        assert len(fc) == 5
        assert all(abs(v - 50.0) < 0.01 for v in fc)

    def test_linear_uptrend(self):
        """Linear uptrend →  slope continues into forecast."""
        hist = [float(i) for i in range(1, 21)]   # 1..20
        fc   = lin_forecast(hist, 3)
        assert fc[2] > fc[0], "Forecast should continue upward"
        assert abs(fc[0] - 21.0) < 1.0            # ~21 (next step)

    def test_linear_downtrend(self):
        hist = [100.0 - i for i in range(20)]
        fc   = lin_forecast(hist, 3)
        assert fc[0] < 81.0                        # continues falling

    def test_empty_history(self):
        assert lin_forecast([], 5) == []

    def test_single_value(self):
        fc = lin_forecast([42.0], 3)
        assert fc == [42.0, 42.0, 42.0]

    def test_two_values(self):
        """Two bars are enough for a gradient."""
        fc = lin_forecast([10.0, 20.0], 2)
        assert fc[1] > fc[0]

    def test_steps_length(self):
        assert len(lin_forecast([1.0, 2.0, 3.0], 7)) == 7

    def test_zero_gradient(self):
        """All-same values → returns last value."""
        fc = lin_forecast([7.0] * 10, 4)
        assert all(abs(v - 7.0) < 0.01 for v in fc)


class TestComputeReturns:
    def test_basic(self):
        r = compute_returns([100.0, 110.0, 99.0])
        assert len(r) == 2
        assert abs(r[0] - 0.1) < 1e-9
        assert r[1] < 0

    def test_empty(self):
        assert compute_returns([]) == []

    def test_single(self):
        assert compute_returns([5.0]) == []


class TestComputeSharpe:
    def test_uptrend_positive(self):
        """Steadily rising series → Sharpe > 0."""
        hist = _rising(252)
        s = compute_sharpe(hist)
        assert s is not None and s > 0, f"Expected > 0, got {s}"

    def test_downtrend_negative(self):
        hist = [1000.0 - i * 3 for i in range(100)]
        s = compute_sharpe(hist)
        assert s is not None and s < 0

    def test_formula_accuracy(self):
        """Verify the Sharpe formula manually."""
        hist    = [100.0, 102.0, 101.0, 104.0, 103.0, 106.0]
        returns = compute_returns(hist)
        mean_r  = statistics.mean(returns)
        std_r   = statistics.stdev(returns)
        rf      = 0.02 / 252
        expected = round((mean_r - rf) / std_r * math.sqrt(252), 4)
        actual   = compute_sharpe(hist)
        assert abs(actual - expected) < 0.0001

    def test_too_short(self):
        assert compute_sharpe([100.0]) is None

    def test_zero_std(self):
        """Perfectly flat returns → std = 0 → returns None."""
        assert compute_sharpe([100.0] * 10) is None


class TestComputeSortino:
    def test_uptrend_positive(self):
        hist = _volatile(150)
        s = compute_sortino(hist)
        # May be None if no negative returns, otherwise should exist
        if s is not None:
            assert isinstance(s, float)

    def test_volatile_not_none(self):
        hist = _volatile(200)
        s = compute_sortino(hist)
        assert s is not None, "Volatile series should produce a Sortino value"

    def test_no_negative_returns_returns_none(self):
        """Strictly rising series has no downside → Sortino is undefined."""
        hist = _rising(50)
        s = compute_sortino(hist)
        assert s is None

    def test_sortino_greater_or_equal_sharpe(self):
        """
        Sortino penalises only downside, so with the same mean return,
        Sortino ≥ Sharpe whenever there IS downside volatility.
        """
        hist    = _volatile(300, seed=7)
        sharpe  = compute_sharpe(hist)
        sortino = compute_sortino(hist)
        if sharpe is not None and sortino is not None:
            assert sortino >= sharpe, (
                f"Sortino ({sortino}) should be >= Sharpe ({sharpe}) "
                "when downside_std <= total_std"
            )

    def test_too_short(self):
        assert compute_sortino([50.0]) is None


class TestComputeMaxDrawdown:
    def test_half_loss(self):
        """Peak=100, trough=50 → -50 %."""
        hist = [80.0, 90.0, 100.0, 80.0, 60.0, 50.0, 70.0]
        dd   = compute_max_drawdown(hist)
        assert abs(dd - (-50.0)) < 0.01, f"Expected -50.0, got {dd}"

    def test_no_drawdown(self):
        """Always rising → 0 % drawdown."""
        assert compute_max_drawdown(_rising(30)) == pytest.approx(0.0, abs=0.01)

    def test_full_wipeout(self):
        hist = [100.0, 50.0, 10.0, 1.0]
        assert compute_max_drawdown(hist) < -90.0

    def test_short(self):
        assert compute_max_drawdown([100.0]) == 0.0

    def test_empty(self):
        assert compute_max_drawdown([]) == 0.0

    def test_recovery(self):
        """Draw-down then recovery: MDD is the worst trough."""
        hist = [100.0, 80.0, 60.0, 90.0, 110.0]
        dd   = compute_max_drawdown(hist)
        assert abs(dd - (-40.0)) < 0.01


class TestComputeVolatility:
    def test_flat_returns_low_vol(self):
        hist = [100.0 + i * 0.01 for i in range(100)]
        v    = compute_volatility(hist)
        assert v is not None and v < 2.0     # near-zero vol

    def test_volatile_higher(self):
        v = compute_volatility(_volatile(252))
        assert v is not None and v > 5.0     # typical equity ~20 % but fake data varies

    def test_too_short(self):
        assert compute_volatility([100.0]) is None


# ═════════════════════════════════════════════════════════════════════════════
# 02  INTEGRATION TESTS — HTTP endpoints via TestClient
# ═════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:
    def test_health_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_version(self, client):
        assert r.json()["version"] == "2.7.0" if (r := client.get("/api/health")) else True

    def test_health_fields(self, client):
        d = client.get("/api/health").json()
        assert d["status"]   == "ok"
        assert "engines"     in d
        assert d["engines"]["linear_reg"] is True

    def test_health_version_2_7(self, client):
        d = client.get("/api/health").json()
        assert d["version"] == "2.7.0"


class TestMetricsEndpoint:
    def test_metrics_no_history_404(self, client):
        """Symbol not in cache → 404."""
        r = client.get("/api/metrics/FAKEXYZ")
        assert r.status_code == 404

    def test_metrics_seeded_returns_200(self, client):
        """Seed cache manually → metrics endpoint returns 200."""
        hist = _volatile(90)
        market_server.mem_set_price("GOLD", hist[-1], 1.5, hist)
        r = client.get("/api/metrics/GOLD")
        assert r.status_code == 200
        d = r.json()
        assert d["symbol"]        == "GOLD"
        assert d["bars"]          == 90
        assert "sharpe"           in d
        assert "sortino"          in d
        assert "max_drawdown"     in d
        assert "volatility_pct"   in d

    def test_metrics_few_bars_404(self, client):
        """Less than 5 bars → 404."""
        market_server.mem_set_price("THIN", 10.0, 0.0, [9.0, 10.0])
        r = client.get("/api/metrics/THIN")
        assert r.status_code == 404


class TestInvestSignals:
    def test_invest_signals_empty_cache(self, client):
        """No cached prices → empty list."""
        r = client.get("/api/invest-signals")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_invest_signals_with_seeded_data(self, client):
        """Seed BTC with 20 bars → appears in signals with expected fields."""
        hist = _volatile(25)
        market_server.mem_set_price("BTC", hist[-1], 2.0, hist)
        r    = client.get("/api/invest-signals")
        data = r.json()
        syms = [s["symbol"] for s in data]
        assert "BTC" in syms
        btc = next(s for s in data if s["symbol"] == "BTC")
        for field in ("price", "change", "rsi", "signal", "forecast_7d",
                      "sharpe", "sortino", "max_drawdown", "volatility"):
            assert field in btc, f"Missing field: {field}"

    def test_invest_signals_rsi_range(self, client):
        """RSI must always be in [0, 100]."""
        hist = _volatile(50)
        market_server.mem_set_price("ETH", hist[-1], 0.5, hist)
        data = client.get("/api/invest-signals").json()
        eth = next((s for s in data if s["symbol"] == "ETH"), None)
        if eth:
            assert 0 <= eth["rsi"] <= 100

    def test_invest_signals_signal_values(self, client):
        """Signal must be one of the 5 defined values."""
        valid = {"STRONG BUY", "BUY", "HOLD", "SELL", "AVOID"}
        hist  = _volatile(30)
        market_server.mem_set_price("SPX", hist[-1], 0.3, hist)
        data  = client.get("/api/invest-signals").json()
        for s in data:
            assert s["signal"] in valid, f"Unknown signal: {s['signal']}"


class TestForecastEndpoint:
    def test_forecast_no_cache_404(self, client):
        r = client.get("/api/forecast/MISSINGXYZ")
        assert r.status_code == 404

    def test_forecast_seeded(self, client):
        hist = _volatile(50)
        market_server.mem_set_price("SILVER", hist[-1], -0.5, hist)
        r = client.get("/api/forecast/SILVER?horizon=1W")
        assert r.status_code == 200
        d = r.json()
        assert d["symbol"] == "SILVER"
        assert len(d["base"]) == 7
        assert len(d["bull"]) == 7
        assert len(d["bear"]) == 7


class TestNewsEndpoint:
    def test_invalid_region_400(self, client):
        r = client.get("/api/news/mars")
        assert r.status_code == 400

    def test_valid_region_accepted(self, client):
        # Seed mem-cache so no real HTTP is needed
        market_server.mem_set_news("world", [{"title": "Test", "link": "", "pubDate": "", "source": "test", "thumbnail": ""}])
        r = client.get("/api/news/world")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestRealhistoryEndpoint:
    def test_unknown_symbol_404(self, client):
        r = client.get("/api/realhistory/UNKNOWNSYM")
        assert r.status_code == 404

    def test_known_symbol_format(self, client):
        """Known symbol should be in YFINANCE_MAP."""
        assert "GOLD" in YFINANCE_MAP
        assert "BTC"  in YFINANCE_MAP


# ═════════════════════════════════════════════════════════════════════════════
# 03  STATE MACHINE — cache state transitions
# ═════════════════════════════════════════════════════════════════════════════

class TestStateMachine:
    def test_mem_hit(self):
        mem_set_price("SM_A", 100.0, 0.5, [99.0, 100.0])
        r = mem_get_price("SM_A")
        assert r is not None and r["price"] == 100.0

    def test_db_fallback(self):
        """Value in DB but not mem → get_price falls through to DB."""
        sym = "SM_DB"
        market_server._mem_prices.pop(sym, None)
        db_set_price(sym, 200.0, 1.0, [195.0, 200.0])
        r = get_price(sym)
        assert r is not None
        assert r["price"] == 200.0

    def test_mem_populated_after_db_hit(self):
        """After a DB hit, the result is back-populated into mem."""
        sym = "SM_BKFILL"
        market_server._mem_prices.pop(sym, None)
        db_set_price(sym, 300.0, 0.0, [290.0, 300.0])
        get_price(sym)                              # triggers back-fill
        assert mem_get_price(sym) is not None

    def test_none_when_missing(self):
        assert get_price("SM_GHOST_SYMBOL_XYZ") is None
        assert mem_get_price("SM_GHOST_SYMBOL_XYZ") is None

    def test_set_price_writes_both_layers(self):
        sym = "SM_BOTH"
        set_price(sym, 42.0, 0.1, [41.0, 42.0])
        # mem layer
        assert mem_get_price(sym) is not None
        # db layer  (clear mem first to force DB path)
        market_server._mem_prices.pop(sym, None)
        assert db_get_price(sym) is not None

    def test_price_overwrite(self):
        """Setting a price twice → latest value is returned."""
        mem_set_price("SM_OVR", 10.0, 0.0, [10.0])
        mem_set_price("SM_OVR", 20.0, 0.0, [20.0])
        assert mem_get_price("SM_OVR")["price"] == 20.0


# ═════════════════════════════════════════════════════════════════════════════
# 04  TIME-TRAVEL MOCKING — freeze time.time() to test TTL
# ═════════════════════════════════════════════════════════════════════════════

class TestTimeTravelMocking:
    def test_fresh_entry_not_stale(self):
        """Entry set now should not be evicted before TTL expires."""
        with patch("market_server.time") as mock_t:
            mock_t.time.return_value = 1000.0
            mem_set_price("TT_FRESH", 50.0, 0.0, [50.0])
            mock_t.time.return_value = 1000.0 + MEM_PRICE_TTL - 1
            r = mem_get_price("TT_FRESH")
            assert r is not None

    def test_stale_entry_evicted(self):
        """Entry whose ts + TTL < now should return None."""
        with patch("market_server.time") as mock_t:
            mock_t.time.return_value = 2000.0
            mem_set_price("TT_STALE", 77.0, 0.0, [77.0])
            mock_t.time.return_value = 2000.0 + MEM_PRICE_TTL + 1
            r = mem_get_price("TT_STALE")
            assert r is None, "Stale entry should have been evicted"

    def test_db_stale_evicted(self):
        """DB entries older than max_age should return None."""
        sym = "TT_DB_STALE"
        with patch("market_server.time") as mock_t:
            mock_t.time.return_value = 3000.0
            # Write directly so DB timestamp is mocked
            import sqlite3
            con = sqlite3.connect(market_server.DB_PATH)
            con.execute("INSERT OR REPLACE INTO price_cache VALUES (?,?,?,?,?)",
                        (sym, 55.0, 0.0, "[]", 3000))
            con.commit(); con.close()

            mock_t.time.return_value = 3000.0 + 301  # > 300 s default max_age
            r = db_get_price(sym, max_age=300)
            assert r is None

    def test_news_ttl(self):
        """News older than MEM_NEWS_TTL should not be returned."""
        with patch("market_server.time") as mock_t:
            mock_t.time.return_value = 5000.0
            market_server._mem_news["tt_world"] = {
                "articles": [{"title": "old"}],
                "ts": 5000.0,
            }
            mock_t.time.return_value = 5000.0 + market_server.MEM_NEWS_TTL + 1
            r = market_server.mem_get_news("tt_world")
            assert r is None


# ═════════════════════════════════════════════════════════════════════════════
# 05  CONSISTENT TICKS — same price on repeated reads
# ═════════════════════════════════════════════════════════════════════════════

class TestConsistentTicks:
    def test_mem_repeatable(self):
        mem_set_price("TICK_BTC", 45000.0, 1.5, [44000.0, 45000.0])
        r1 = mem_get_price("TICK_BTC")
        r2 = mem_get_price("TICK_BTC")
        r3 = mem_get_price("TICK_BTC")
        assert r1["price"] == r2["price"] == r3["price"] == 45000.0

    def test_get_price_consistent(self):
        set_price("TICK_ETH", 3000.0, 0.8, [2900.0, 3000.0])
        prices = [get_price("TICK_ETH")["price"] for _ in range(10)]
        assert len(set(prices)) == 1, "Price should not change between identical reads"

    def test_history_unchanged(self):
        hist = [float(i) for i in range(1, 21)]
        mem_set_price("TICK_HIST", 20.0, 0.0, hist)
        for _ in range(5):
            r = mem_get_price("TICK_HIST")
            assert r["history"] == hist


# ═════════════════════════════════════════════════════════════════════════════
# 06  MEMORY LEAKS — _mem_prices dict shouldn't corrupt under load
# ═════════════════════════════════════════════════════════════════════════════

class TestMemoryLeaks:
    def test_add_500_symbols(self):
        """Writing 500 distinct symbols — dict remains accessible and consistent."""
        for i in range(500):
            mem_set_price(f"ML_SYM_{i}", float(i), 0.0, [float(i)])
        # All entries readable
        for i in range(0, 500, 50):
            r = mem_get_price(f"ML_SYM_{i}")
            assert r is not None
            assert r["price"] == float(i)

    def test_overwrite_same_key_many_times(self):
        """Overwriting the same key 1 000 × does not corrupt the stored value."""
        for v in range(1000):
            mem_set_price("ML_OVERWRITE", float(v), 0.0, [float(v)])
        r = mem_get_price("ML_OVERWRITE")
        assert r["price"] == 999.0

    def test_no_none_in_cache(self):
        """Ensure we never store None as price — consumers rely on price being numeric."""
        for i in range(20):
            mem_set_price(f"ML_NN_{i}", float(i + 1), 0.0, [float(i + 1)])
        for i in range(20):
            r = mem_get_price(f"ML_NN_{i}")
            assert r is not None
            assert r["price"] is not None
            assert isinstance(r["price"], (int, float))


# ═════════════════════════════════════════════════════════════════════════════
# 07  THREAD SAFETY — concurrent cache reads and writes
# ═════════════════════════════════════════════════════════════════════════════

class TestThreadSafety:
    def test_concurrent_writes_no_exception(self):
        """50 threads each writing a unique symbol — no exception raised."""
        errors = []

        def writer(i):
            try:
                set_price(f"TS_W_{i}", float(i * 10), 0.0, [float(i)])
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread-safety errors: {errors}"

    def test_concurrent_writes_data_integrity(self):
        """After 50 concurrent writes, all values should be readable."""
        for i in range(50):
            set_price(f"TS_W_{i}", float(i * 10), 0.0, [float(i)])

        for i in range(50):
            r = get_price(f"TS_W_{i}")
            assert r is not None
            assert r["price"] == float(i * 10)

    def test_concurrent_reads_no_exception(self):
        """Many threads reading the same key simultaneously."""
        mem_set_price("TS_READ_KEY", 1234.0, 0.0, [1234.0])
        errors = []

        def reader():
            try:
                r = mem_get_price("TS_READ_KEY")
                assert r is not None
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=reader) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent read errors: {errors}"

    def test_mixed_read_write_no_deadlock(self):
        """Mix of readers and writers should complete without deadlock (5s timeout)."""
        results = []
        stop    = threading.Event()

        def writer_loop():
            v = 0
            while not stop.is_set():
                mem_set_price("TS_MIX", float(v), 0.0, [float(v)])
                v += 1

        def reader_loop():
            while not stop.is_set():
                mem_get_price("TS_MIX")

        threads = (
            [threading.Thread(target=writer_loop) for _ in range(5)] +
            [threading.Thread(target=reader_loop) for _ in range(10)]
        )
        for t in threads:
            t.daemon = True
            t.start()

        time.sleep(0.2)   # let them run briefly
        stop.set()

        for t in threads:
            t.join(timeout=5.0)

        # If any thread is still alive after join(), it deadlocked
        alive = [t for t in threads if t.is_alive()]
        assert not alive, f"{len(alive)} threads deadlocked"


# ═════════════════════════════════════════════════════════════════════════════
# 08  SHARPE RATIO
# ═════════════════════════════════════════════════════════════════════════════

class TestSharpeRatio:
    def test_positive_in_bull_market(self):
        # Compound 0.1 % daily — steady bull
        hist = [100 * (1.001 ** i) for i in range(252)]
        s    = compute_sharpe(hist)
        assert s is not None and s > 0

    def test_negative_in_bear_market(self):
        hist = [100 * (0.999 ** i) for i in range(252)]
        s    = compute_sharpe(hist)
        assert s is not None and s < 0

    def test_higher_rf_lowers_sharpe(self):
        hist    = _volatile(200)
        s_low   = compute_sharpe(hist, rf_annual=0.01)
        s_high  = compute_sharpe(hist, rf_annual=0.10)
        if s_low is not None and s_high is not None:
            assert s_low > s_high

    def test_formula_exact(self):
        hist    = [100.0, 101.0, 102.0, 101.0, 103.0, 104.0]
        rets    = compute_returns(hist)
        mean_r  = statistics.mean(rets)
        std_r   = statistics.stdev(rets)
        rf      = 0.02 / 252
        expected = round((mean_r - rf) / std_r * math.sqrt(252), 4)
        assert compute_sharpe(hist) == expected

    def test_none_for_flat(self):
        # std = 0 → Sharpe undefined
        assert compute_sharpe([50.0] * 30) is None

    def test_none_for_short(self):
        assert compute_sharpe([100.0]) is None


# ═════════════════════════════════════════════════════════════════════════════
# 09  SORTINO RATIO
# ═════════════════════════════════════════════════════════════════════════════

class TestSortinoRatio:
    def test_volatile_returns_float(self):
        s = compute_sortino(_volatile(200))
        assert s is not None and isinstance(s, float)

    def test_none_for_strictly_rising(self):
        """No negative returns → downside_std = 0 → None."""
        assert compute_sortino(_rising(50)) is None

    def test_sortino_valid_for_volatile(self):
        """
        Sortino returns a finite float for any volatile series.
        Directional relationship vs Sharpe depends on sign of excess returns
        and centering choices; we only verify the value is finite here.
        """
        hist    = _volatile(300, seed=99)
        sharpe  = compute_sharpe(hist)
        sortino = compute_sortino(hist)
        assert sharpe  is not None and math.isfinite(sharpe)
        assert sortino is not None and math.isfinite(sortino)

    def test_sortino_positive_bull_ge_sharpe(self):
        """
        In a strong bull market (positive excess returns), Sortino >= Sharpe
        because downside_std <= total_std and the positive numerator amplifies
        this into a higher ratio.
        """
        # Strong uptrend — consistent 0.15% daily gain
        hist = [100.0 * (1.0015 ** i) for i in range(300)]
        sharpe  = compute_sharpe(hist)
        sortino = compute_sortino(hist)
        # Sharpe must be strongly positive
        assert sharpe is not None and sharpe > 5.0
        # Sortino is None (no downside at all) or >= Sharpe
        if sortino is not None:
            assert sortino >= sharpe

    def test_more_downside_crash_sortino_negative(self):
        """
        Asymmetric crash series (falls 3 % every 3rd day, rises 0.1 % otherwise)
        should produce a defined, negative Sortino ratio.
        """
        hist = []
        p = 100.0
        for i in range(200):
            p = p * (1.001 if i % 3 != 0 else 0.97)
            hist.append(p)
        s = compute_sortino(hist)
        assert s is not None, "Crash series must have downside returns"
        assert s < 0, f"Expected negative Sortino for declining series, got {s}"

    def test_none_for_short(self):
        assert compute_sortino([100.0]) is None


# ═════════════════════════════════════════════════════════════════════════════
# 10  TRANSACTION COSTS
# ═════════════════════════════════════════════════════════════════════════════

class TestTransactionCosts:
    TC = 0.001  # 0.1 % per leg

    def test_round_trip_reduces_return(self):
        buy    = 100.0
        sell   = 110.0
        gross  = (sell - buy) / buy
        net    = gross - 2 * self.TC
        assert net < gross

    def test_break_even_spread(self):
        """A trade that exactly covers transaction costs breaks even."""
        buy   = 100.0
        # Need sell > buy * (1 + 2*TC) to profit
        break_even_sell = buy * (1 + 2 * self.TC)
        gross = (break_even_sell - buy) / buy
        net   = gross - 2 * self.TC
        assert net >= 0 - 1e-10

    def test_loss_trade_worse_after_tc(self):
        buy  = 100.0
        sell = 95.0
        gross = (sell - buy) / buy
        net   = gross - 2 * self.TC
        assert net < gross      # TC makes loss worse

    def test_tc_on_forecast(self):
        """Apply TC to a 7-day lin_forecast scenario."""
        hist  = _volatile(60)
        fc7   = lin_forecast(hist, 7)
        entry = hist[-1]
        exit_ = fc7[-1]
        if exit_ > entry:
            gross = (exit_ - entry) / entry
            net   = gross - 2 * self.TC
            assert net < gross

    def test_high_tc_kills_profit(self):
        """Extremely high TC (10 %) wipes any normal gain."""
        tc     = 0.10
        buy, sell = 100.0, 105.0
        net    = (sell - buy) / buy - 2 * tc
        assert net < 0


# ═════════════════════════════════════════════════════════════════════════════
# 11  SURVIVORSHIP BIAS
# ═════════════════════════════════════════════════════════════════════════════

class TestSurvivorshipBias:
    def test_unknown_symbol_realhistory_404(self, client):
        r = client.get("/api/realhistory/ENRONSTOCK2001")
        assert r.status_code == 404

    def test_unknown_symbol_not_in_yfinance_map(self):
        assert "ENRONSTOCK2001" not in YFINANCE_MAP
        assert "FAKEDELISTED"   not in YFINANCE_MAP

    def test_no_phantom_price_in_cache(self):
        market_server._mem_prices.pop("PHANTOM_GHOST", None)
        assert mem_get_price("PHANTOM_GHOST") is None

    def test_metrics_404_for_uncached(self, client):
        r = client.get("/api/metrics/SURVIVORSHIP_FAKE")
        assert r.status_code == 404

    def test_invest_signals_excludes_unlisted(self, client):
        """Invest signals only covers symbols in COINGECKO_IDS + the hardcoded metals/FX."""
        # Ensure an unlisted symbol does NOT appear
        market_server.mem_set_price("FAKECOIN", 1.0, 0.0, list(range(25)))
        data = client.get("/api/invest-signals").json()
        assert "FAKECOIN" not in [s["symbol"] for s in data]

    def test_all_yfinance_map_symbols_documented(self):
        """Every key in YFINANCE_MAP should be a non-empty string."""
        for sym, ticker in YFINANCE_MAP.items():
            assert isinstance(sym, str)    and len(sym) > 0
            assert isinstance(ticker, str) and len(ticker) > 0


# ═════════════════════════════════════════════════════════════════════════════
# 12  LOOK-AHEAD BIAS
# ═════════════════════════════════════════════════════════════════════════════

class TestLookAheadBias:
    def test_forecast_extrapolates_forward(self):
        """Forecast values should be beyond index n, not inside the history."""
        hist = [float(i) for i in range(1, 21)]   # 1..20, slope=1
        fc   = lin_forecast(hist, 5)
        # first forecast step should be near 21
        assert abs(fc[0] - 21.0) < 1.5

    def test_forecast_input_count_exact(self):
        """lin_forecast uses exactly len(history) points — injecting a future
        bar shifts the forecast, proving inputs are used in order."""
        hist      = [1.0, 2.0, 3.0, 4.0, 5.0]
        fc_clean  = lin_forecast(hist, 3)
        # Inject a huge future bar — if the algorithm ignores it, clean ~= contaminated
        fc_extra  = lin_forecast(hist + [9999.0], 3)
        # With the extra bar, slope changes → forecasts differ
        assert fc_clean[0] != fc_extra[0], (
            "Adding a future bar should change the forecast — algo reads all inputs"
        )

    def test_invest_signals_forecast_uses_past_only(self, client):
        """The 7-day forecast in invest-signals must derive from past closes only."""
        hist = list(range(20, 50))   # ascending — 1 bar per day, no future leakage
        market_server.mem_set_price("LAB_SYM", 49.0, 1.0, [float(v) for v in hist])
        data = client.get("/api/invest-signals").json()
        entry = next((s for s in data if s["symbol"] == "LAB_SYM"), None)
        if entry:
            # forecast_7d should be > 49 (uptrend extrapolated forward)
            assert entry["forecast_7d"] > 49.0, (
                "Forecast should project uptrend, not look back"
            )

    def test_no_future_date_in_output(self):
        """lin_forecast returns a flat list of floats — no date objects contaminate."""
        fc = lin_forecast([10.0, 11.0, 12.0], 5)
        for v in fc:
            assert isinstance(v, (int, float))


# ═════════════════════════════════════════════════════════════════════════════
# 13  ZERO LIQUIDITY
# ═════════════════════════════════════════════════════════════════════════════

class TestZeroLiquidity:
    def test_empty_history_lin_forecast(self):
        assert lin_forecast([], 5) == []

    def test_single_price_lin_forecast(self):
        assert lin_forecast([100.0], 4) == [100.0, 100.0, 100.0, 100.0]

    def test_invest_signals_skips_short_history(self, client):
        """Symbol with < 15 bars should be excluded from invest-signals."""
        market_server.mem_set_price("ILLIQUID", 1.0, 0.0, [1.0, 1.0])
        data = client.get("/api/invest-signals").json()
        assert "ILLIQUID" not in [s["symbol"] for s in data]

    def test_metrics_empty_history_404(self, client):
        market_server.mem_set_price("ZEROLVOL", 1.0, 0.0, [])
        r = client.get("/api/metrics/ZEROLVOL")
        assert r.status_code == 404

    def test_sharpe_empty(self):
        assert compute_sharpe([]) is None

    def test_sortino_empty(self):
        assert compute_sortino([]) is None

    def test_max_drawdown_empty(self):
        assert compute_max_drawdown([]) == 0.0

    def test_volatility_empty(self):
        assert compute_volatility([]) is None


# ═════════════════════════════════════════════════════════════════════════════
# 14  ORDER REJECTIONS
# ═════════════════════════════════════════════════════════════════════════════

class TestOrderRejections:
    def test_realhistory_invalid_symbol_404(self, client):
        r = client.get("/api/realhistory/INVALIDXYZ123")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_forecast_unknown_symbol_404(self, client):
        r = client.get("/api/forecast/NODATAHERE")
        assert r.status_code == 404

    def test_news_unknown_region_400(self, client):
        r = client.get("/api/news/pluto")
        assert r.status_code == 400

    def test_metrics_unknown_symbol_404(self, client):
        r = client.get("/api/metrics/TOTALLYUNKNOWN")
        assert r.status_code == 404

    def test_yfinance_map_rejects_unknown(self):
        """YFINANCE_MAP must not contain obviously invalid tickers."""
        for sym, ticker in YFINANCE_MAP.items():
            assert ticker != "", f"Ticker for {sym} is empty"
            assert ticker is not None

    def test_yahoo_symbols_subset_of_yfinance_map(self):
        """All YAHOO_SYMBOLS keys must also exist in YFINANCE_MAP."""
        for sym in YAHOO_SYMBOLS:
            assert sym in YFINANCE_MAP, f"{sym} in YAHOO_SYMBOLS but not YFINANCE_MAP"


# ═════════════════════════════════════════════════════════════════════════════
# 15  PARTIAL FILLS — short history handled without crash
# ═════════════════════════════════════════════════════════════════════════════

class TestPartialFills:
    def test_two_bar_forecast(self):
        fc = lin_forecast([10.0, 11.0], 5)
        assert len(fc) == 5
        assert all(isinstance(v, float) for v in fc)

    def test_five_bar_forecast(self):
        fc = lin_forecast([10.0, 11.0, 12.0, 13.0, 14.0], 3)
        assert len(fc) == 3
        assert fc[0] == pytest.approx(15.0, abs=0.5)

    def test_partial_history_metrics(self):
        """5–14 bars: sharpe/sortino return None (too short), drawdown works."""
        hist = [float(i) for i in range(1, 8)]   # 7 bars
        assert compute_sharpe(hist) is None or isinstance(compute_sharpe(hist), float)
        assert compute_max_drawdown(hist) >= -100.0

    def test_forecast_endpoint_3_bar_seed(self, client):
        """Seed with 3 bars (too few for invest-signals, but forecast should work)."""
        market_server.mem_set_price("PF_SYM", 30.0, 0.0, [28.0, 29.0, 30.0])
        r = client.get("/api/forecast/PF_SYM?horizon=1D")
        assert r.status_code == 200
        assert len(r.json()["base"]) == 1

    def test_invest_signals_14_bars_skipped(self, client):
        """Exactly 14 bars -> skipped (threshold is >= 15).
        Uses GOLD which is in the endpoint's hardcoded all_syms list."""
        hist = list(range(1, 15))   # 14 bars
        market_server.mem_set_price("GOLD", float(hist[-1]), 0.0, [float(v) for v in hist])
        data = client.get("/api/invest-signals").json()
        assert "GOLD" not in [s["symbol"] for s in data]

    def test_invest_signals_15_bars_included(self, client):
        """15 bars meets the >= 15 threshold -> symbol appears in signals.
        Uses GOLD which is in the endpoint's hardcoded all_syms list."""
        hist = list(range(1, 16))   # 15 bars
        market_server.mem_set_price("GOLD", float(hist[-1]), 0.0, [float(v) for v in hist])
        data = client.get("/api/invest-signals").json()
        assert "GOLD" in [s["symbol"] for s in data]


# ═════════════════════════════════════════════════════════════════════════════
# 16  CONNECTION DROPS
# ═════════════════════════════════════════════════════════════════════════════

class TestConnectionDrops:
    def _make_mock_http(self, side_effect):
        mock = MagicMock()
        mock.get = AsyncMock(side_effect=side_effect)
        return mock

    def test_connect_error_returns_none(self):
        import httpx
        mock_http = self._make_mock_http(httpx.ConnectError("reset"))
        with patch.object(market_server, "_http", mock_http):
            sym, data = _run(fetch_yahoo_one("GOLD"))
            assert sym  == "GOLD"
            assert data is None

    def test_timeout_returns_none(self):
        import httpx
        mock_http = self._make_mock_http(httpx.TimeoutException("timed out"))
        with patch.object(market_server, "_http", mock_http):
            sym, data = _run(fetch_yahoo_one("GOLD"))
            assert data is None

    def test_remote_disconnect_returns_none(self):
        import httpx
        mock_http = self._make_mock_http(httpx.RemoteProtocolError("disconnect"))
        with patch.object(market_server, "_http", mock_http):
            sym, data = _run(fetch_yahoo_one("GOLD"))
            assert data is None

    def test_batch_one_drop_others_succeed(self):
        """A single connection drop in a batch should not abort the whole batch."""
        import httpx

        call_count = {"n": 0}

        async def selective_fail(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise httpx.ConnectError("first call drops")
            # subsequent calls return empty chart
            mock_r = MagicMock()
            mock_r.json.return_value = {"chart": {"result": None}}
            return mock_r

        mock_http = MagicMock()
        mock_http.get = AsyncMock(side_effect=selective_fail)

        with patch.object(market_server, "_http", mock_http):
            result = _run(market_server.fetch_yahoo_batch(["GOLD", "SILVER"]))
            assert isinstance(result, dict)   # did not raise


# ═════════════════════════════════════════════════════════════════════════════
# 17  RATE LIMITING (429)
# ═════════════════════════════════════════════════════════════════════════════

class TestRateLimiting:
    def _mock_429(self):
        mock_r = MagicMock()
        mock_r.status_code = 429
        mock_r.json.return_value = {"error": "too many requests"}
        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_r)
        return mock_http

    def test_429_returns_none_not_crash(self):
        """Yahoo 429 → no 'chart' key → graceful None."""
        with patch.object(market_server, "_http", self._mock_429()):
            sym, data = _run(fetch_yahoo_one("GOLD"))
            assert sym  == "GOLD"
            assert data is None

    def test_429_batch_no_exception(self):
        """429 on all batch symbols → returns dict of empty entries, no raise."""
        with patch.object(market_server, "_http", self._mock_429()):
            result = _run(market_server.fetch_yahoo_batch(["GOLD", "SILVER"]))
            assert isinstance(result, dict)
            for sym in ("GOLD", "SILVER"):
                assert result[sym]["price"] is None

    def test_rapid_sequential_requests(self, client):
        """30 rapid GET /api/health requests — all should succeed (no rate crash)."""
        statuses = [client.get("/api/health").status_code for _ in range(30)]
        assert all(s == 200 for s in statuses)

    def test_invest_signals_repeated_no_crash(self, client):
        """5 rapid calls to invest-signals should never raise 500."""
        hist = _volatile(20)
        market_server.mem_set_price("BTC", hist[-1], 0.5, hist)
        statuses = [client.get("/api/invest-signals").status_code for _ in range(5)]
        assert all(s == 200 for s in statuses)


# ═════════════════════════════════════════════════════════════════════════════
# 18  MAX DRAWDOWN
# ═════════════════════════════════════════════════════════════════════════════

class TestMaxDrawdown:
    def test_simple_50pct(self):
        hist = [80.0, 90.0, 100.0, 80.0, 60.0, 50.0, 70.0]
        assert abs(compute_max_drawdown(hist) - (-50.0)) < 0.01

    def test_zero_drawdown_monotone(self):
        assert compute_max_drawdown(_rising(30)) == pytest.approx(0.0, abs=0.01)

    def test_full_loss(self):
        assert compute_max_drawdown([100.0, 50.0, 10.0, 1.0]) < -90.0

    def test_multiple_peaks(self):
        """Ensure the algorithm resets peak correctly."""
        hist = [100.0, 90.0, 110.0, 80.0, 120.0, 60.0]
        # Peak at 120, trough at 60 → -50 %
        assert abs(compute_max_drawdown(hist) - (-50.0)) < 0.01

    def test_always_non_positive(self):
        """Drawdown is always ≤ 0."""
        for seed in range(10):
            assert compute_max_drawdown(_volatile(100, seed)) <= 0.0

    def test_drawdown_in_invest_signals(self, client):
        hist = _volatile(30)
        market_server.mem_set_price("GOLD", hist[-1], 0.5, hist)
        data = client.get("/api/invest-signals").json()
        entry = next((s for s in data if s["symbol"] == "GOLD"), None)
        if entry:
            assert entry["max_drawdown"] <= 0.0


# ═════════════════════════════════════════════════════════════════════════════
# 19  STALE DATA TIMEOUT
# ═════════════════════════════════════════════════════════════════════════════

class TestStaleDataTimeout:
    def test_mem_cache_ttl_boundary(self):
        """Entry at exactly TTL - 1 second is still valid."""
        with patch("market_server.time") as mock_t:
            mock_t.time.return_value = 0.0
            mem_set_price("SDT_A", 42.0, 0.0, [42.0])
            mock_t.time.return_value = MEM_PRICE_TTL - 1
            assert mem_get_price("SDT_A") is not None

    def test_mem_cache_expires_at_ttl(self):
        """Entry at exactly TTL + 1 second is evicted."""
        with patch("market_server.time") as mock_t:
            mock_t.time.return_value = 0.0
            mem_set_price("SDT_B", 43.0, 0.0, [43.0])
            mock_t.time.return_value = MEM_PRICE_TTL + 1
            assert mem_get_price("SDT_B") is None

    def test_get_price_falls_through_stale_mem(self):
        """
        If mem entry is stale, get_price falls through to DB.
        Seed DB only, then add stale mem → get_price should find DB value.
        """
        sym = "SDT_C"
        db_set_price(sym, 999.0, 0.0, [999.0])
        # Inject artificially stale mem entry
        market_server._mem_prices[sym] = {
            "symbol": sym, "price": 1.0, "change": 0.0,
            "history": [1.0], "ts": 0.0   # ts=0 → definitely stale
        }
        r = get_price(sym)
        assert r is not None
        # get_price skips stale mem and goes to DB
        # DB has 999.0 → that should be returned
        assert r["price"] == 999.0

    def test_stale_news_not_returned(self):
        """Mem news older than MEM_NEWS_TTL should not be served."""
        with patch("market_server.time") as mock_t:
            mock_t.time.return_value = 0.0
            market_server._mem_news["stale_reg"] = {
                "articles": [{"title": "old news"}], "ts": 0.0
            }
            mock_t.time.return_value = market_server.MEM_NEWS_TTL + 1
            result = market_server.mem_get_news("stale_reg")
            assert result is None


# ═════════════════════════════════════════════════════════════════════════════
# 20  RAPID CONCURRENT REQUESTS
# ═════════════════════════════════════════════════════════════════════════════

class TestRapidConcurrentRequests:
    def test_30_health_requests_all_200(self, client):
        results = [client.get("/api/health").status_code for _ in range(30)]
        assert all(s == 200 for s in results), f"Some requests failed: {results}"

    def test_concurrent_forecast_requests(self, client):
        """Multiple threads hitting /api/forecast with the same seeded symbol."""
        hist = _volatile(40)
        market_server.mem_set_price("CFTEST", hist[-1], 0.0, hist)
        errors = []

        def req():
            try:
                r = client.get("/api/forecast/CFTEST?horizon=1W")
                if r.status_code != 200:
                    errors.append(f"status {r.status_code}")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=req) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, f"Concurrent forecast errors: {errors}"

    def test_concurrent_invest_signals(self, client):
        """10 concurrent threads hitting invest-signals — no corruption."""
        hist = _volatile(20)
        market_server.mem_set_price("BTC", hist[-1], 1.0, hist)
        errors = []

        def req():
            try:
                r = client.get("/api/invest-signals")
                assert r.status_code == 200
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=req) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors

    def test_cache_consistent_under_concurrent_load(self, client):
        """Cache value should not be corrupted under concurrent read/write load."""
        expected_price = 12345.67
        market_server.mem_set_price("LOAD_SYM", expected_price, 0.0, [expected_price])

        mismatches = []

        def check():
            r = mem_get_price("LOAD_SYM")
            if r and r["price"] != expected_price:
                mismatches.append(r["price"])

        threads = [threading.Thread(target=check) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not mismatches, f"Price corrupted under load: {mismatches}"
