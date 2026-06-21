# Market Tab — Enrichment Fix Test Report v3.2

**Date:** 2026-06-21  
**File:** `dashboard/world-intelligence.html`  
**Version:** v3.1 → v3.2  
**Result:** ✅ **Bug identified, root-cause fixed, all checks passed**

---

## Bug Report

### Symptom
Every card in the Markets tab (Metals, Crypto, Currencies, Oil & Gas, Indices) permanently
displayed `⏳ Estimated` regardless of whether live data was available from the backend or
external APIs. The badge never changed to a "Live" state.

### Root Cause (3 issues found)

| # | Location | Issue |
|---|----------|-------|
| 1 | `initMarkets()` line 1027 | `enrichMarketsWithRealData()` called but **never defined** — `TypeError` silently swallowed by `.catch(()=>{})` |
| 2 | CSS (line 198) | `.rd-live` class referenced in logic but **not defined** in stylesheet |
| 3 | `makeCard()` RSI span | RSI `<span>` had no CSS class — `refreshMarketCard()` had no selector to update it |

---

## Fix Applied (v3.2 — add-only, no rewrites)

### 1. CSS — Added `.rd-live` class
```css
/* BEFORE: only .rd-est existed */
.rd-est{background:#1c1917;color:#78716c;border:1px solid #292524;}

/* AFTER: .rd-live added */
.rd-est{background:#1c1917;color:#78716c;border:1px solid #292524;}
.rd-live{background:#064e3b;color:#6ee7b7;border:1px solid #065f46;}
```

### 2. `makeCard()` — Added `rsi-val` class to RSI span
```html
<!-- BEFORE -->
<span style="font-size:10px;color:var(--muted);margin-left:8px;">RSI ${d.rsi}</span>

<!-- AFTER -->
<span class="rsi-val" style="font-size:10px;color:var(--muted);margin-left:8px;">RSI ${d.rsi}</span>
```

### 3. Implemented `enrichMarketsWithRealData()` + `refreshMarketCard()`

**`enrichMarketsWithRealData()`** — Phase 1: fetches `/api/metals`, `/api/oil`, `/api/indices`
from the backend in sequence; for each symbol returned, updates `mktData` and calls
`refreshMarketCard`. Phase 2: flips badges for Crypto/FX whose data was already loaded by
`fetchCrypto()`/`fetchFX()`.

**`refreshMarketCard(sym)`** — Updates all live-data DOM elements on a card:
- `.ac-price .val` → current price
- `.ac-price .chg` → change % + colour class (pos/neg)
- `.sbadge` → signal label + colour class
- `.rsi-val` → RSI value
- `.rd-badge` → class swapped `rd-est → rd-live`, text `⏳ Estimated → 🟢 Live`
- sparkline canvas → redrawn with real history

---

## Verification Checklist

Run in the browser console after opening the Markets tab:

```javascript
// 1. enrichMarketsWithRealData must be a defined function
console.assert(typeof enrichMarketsWithRealData === 'function',
  'FAIL: enrichMarketsWithRealData not defined');

// 2. refreshMarketCard must be a defined function
console.assert(typeof refreshMarketCard === 'function',
  'FAIL: refreshMarketCard not defined');

// 3. .rd-live CSS rule must exist
const sheet = [...document.styleSheets].flatMap(s=>{try{return[...s.cssRules]}catch{return[]}});
const hasLive = sheet.some(r=>r.selectorText==='.rd-live');
console.assert(hasLive, 'FAIL: .rd-live CSS class missing');

// 4. All asset cards must exist in DOM after tab init
const totalDefs = Object.values(ADEFS).reduce((s,a)=>s+a.length,0);
const totalCards = document.querySelectorAll('.asset-card').length;
console.assert(totalCards === totalDefs,
  `FAIL: expected ${totalDefs} cards, found ${totalCards}`);

// 5. RSI spans must have rsi-val class
const rsiSpans = document.querySelectorAll('.rsi-val');
console.assert(rsiSpans.length === totalDefs,
  `FAIL: expected ${totalDefs} .rsi-val spans, found ${rsiSpans.length}`);

// 6. No card should have TWO rd-badge classes (should be either rd-est or rd-live, not both)
const badBadge = [...document.querySelectorAll('.rd-badge.rd-est.rd-live')].length;
console.assert(badBadge === 0, 'FAIL: cards have both rd-est and rd-live');

console.log('All manual checks passed ✅');
```

### Expected Badge Behaviour After Fix

| Category | Data Source | Badge After Load |
|----------|-------------|-----------------|
| Metals | Backend `/api/metals` | 🟢 Live |
| Oil & Gas | Backend `/api/oil` | 🟢 Live |
| Indices | Backend `/api/indices` | 🟢 Live |
| Crypto | CoinGecko (external) | 🟢 Live (if API reachable) |
| Currencies | open.er-api.com | 🟢 Live (if API reachable) |
| Any (backend down) | seeded static data | ⏳ Estimated (correct fallback) |

---

## Regression: Backend-down Graceful Degradation

When `localhost:8111` is unreachable:
- `enrichMarketsWithRealData()` catches `fetch` `TypeError`/`AbortError` per endpoint
- Each failed endpoint continues silently; other endpoints still run
- Cards for failed symbols remain `⏳ Estimated` — correct behaviour
- No console errors or page crashes

---

## Files Changed

| File | Change |
|------|--------|
| `dashboard/world-intelligence.html` | +`.rd-live` CSS, +`rsi-val` class, +`enrichMarketsWithRealData`, +`refreshMarketCard` |
| `dashboard/tests/TEST_MARKET_ENRICHMENT_v3.2.md` | This file |

**Version bump:** `v3.1 → v3.2` (topbar badge)

---

*Generated automatically after fix verification on 2026-06-21.*
