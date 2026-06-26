# Test Report — 4 Bug Fixes v3.18
**World Intelligence Platform v3.18**
**Author: Muhammad Umer Lari | Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**
**Free APIs: Google News RSS · BBC · DW · Reuters · TechCrunch · Kitco · codetabs.com · thingproxy.freeboard.io — Zero paid APIs**

---

## What Changed in v3.18

| # | Change | Detail |
|---|--------|--------|
| 1 | **🐛 Live-pulse div structure fixed** | Moved outside `ntabs` flex container — was crowding tab buttons |
| 2 | **🐛 Sub-tab persistence (full fix)** | `localStorage.setItem('wip_rp_subtab')` added — survives F5 page refresh |
| 3 | **🐛 Rising Powers restore reads localStorage** | `initRisingPowers` now reads localStorage on page refresh — not just in-memory |
| 4 | **🐛 News 2 new CORS proxies** | `codetabs.com` + `thingproxy.freeboard.io` added as 4th/5th proxy chains |
| 5 | **🐛 Modal close button always visible** | Sticky header bar in modal — close button never scrolls away |
| 6 | **Modal max-height** | `max-height:calc(100vh - 40px)` + `overflow-y:auto` on modal box |
| 7 | **5-proxy parallel fetch** | News now fires 5 proxy chains simultaneously (was 3) |
| 8 | **Version bumped to v3.18** | `<title>`, `.badge`, `version.py` all updated |

---

## Phase LP — Live-Pulse HTML Structure Fix

| # | Test | Expected | Result |
|---|------|----------|--------|
| 1 | `ntabs` div closes before live-pulse div | `</div>` after last `.ntab-btn` | PASS |
| 2 | Live-pulse div is sibling of `ntabs`, not child | Not inside flex container | PASS |
| 3 | Tab buttons not crowded by live-pulse div | 12 tabs display cleanly in 2 rows | PASS |
| 4 | `news-refresh-badge` present | `id="news-refresh-badge"` in DOM | PASS |
| 5 | `map-live-pulse` span present | Pulse animation shows | PASS |
| 6 | Live-pulse div has margin `4px 0 10px` | Visible spacing between tabs and news | PASS |
| 7 | `showNewsTab` active class still works | `.ntab-btn.active` applied on click | PASS |

## Phase SP — Sub-tab Persistence (Full Fix)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 8 | `localStorage.setItem('wip_rp_subtab',tab)` in `showRpSubTab` | Fires on every sub-tab click | PASS |
| 9 | Saves for all 6 sub-tabs | cards/nextchina/migration/passport/language/newnations | PASS |
| 10 | `window._lastRpSubTab` still set (in-memory) | Backwards compatible | PASS |
| 11 | `_rpRestore` reads `window._lastRpSubTab` first | Memory preferred over storage | PASS |
| 12 | Falls back to `localStorage.getItem('wip_rp_subtab')` if memory undefined | F5 scenario covered | PASS |
| 13 | Restore uses `requestAnimationFrame` | After DOM updated | PASS |
| 14 | `if(btn)` guard before calling `showRpSubTab` | No null ref if button missing | PASS |
| 15 | Navigate to "Passport Power" → F5 → returns to Passport Power | Full page refresh test | PASS |
| 16 | Navigate to "Next China" → F5 → returns to Next China | Full page refresh test | PASS |
| 17 | Navigate to "New Nations" → F5 → returns to New Nations | Full page refresh test | PASS |
| 18 | First visit (no localStorage key) → shows Cards | Default tab unchanged | PASS |
| 19 | `try/catch` around localStorage calls | No crash in private browsing | PASS |

## Phase NX — News Proxy Expansion

| # | Test | Expected | Result |
|---|------|----------|--------|
| 20 | `CODETABS` constant defined | `https://api.codetabs.com/v1/proxy?quest=` | PASS |
| 21 | `THINGPROXY` constant defined | `https://thingproxy.freeboard.io/fetch/` | PASS |
| 22 | `_fetchFeedCodetabs(feed)` function exists | Async, uses feed.u + feed.s | PASS |
| 23 | `_fetchFeedThingproxy(feed)` function exists | Async, uses feed.u + feed.s | PASS |
| 24 | Both new functions call `_parseRSS` | Consistent RSS parsing | PASS |
| 25 | Both new functions have 8s timeout | `AbortSignal.timeout(8000)` | PASS |
| 26 | Both new functions return `[]` on error | No throw, safe failure | PASS |
| 27 | `allFetches` includes `...feeds.map(_fetchFeedCodetabs)` | 4th proxy chain added | PASS |
| 28 | `allFetches` includes `...feeds.map(_fetchFeedThingproxy)` | 5th proxy chain added | PASS |
| 29 | `Promise.allSettled` handles all 5 chains | 5× feeds count + 1 backend | PASS |
| 30 | News loads when corsproxy.io unavailable | codetabs/thingproxy fallback | PASS |
| 31 | liveCount reflects articles from all 5 chains | Aggregate dedup count | PASS |
| 32 | codetabs.com is free, no API key | Zero paid APIs | PASS |
| 33 | thingproxy.freeboard.io is free, no API key | Zero paid APIs | PASS |
| 34 | Fallback headlines shown if all 5 proxies fail | `NEWS_FALLBACK[region]` appended | PASS |
| 35 | News ticker updates with live articles | `updateTicker` called | PASS |
| 36 | 90s auto-refresh still applies | `_startNewsAutoRefresh` unchanged | PASS |

## Phase MD — Modal Close Button Fix

| # | Test | Expected | Result |
|---|------|----------|--------|
| 37 | `rp-modal-box` has `max-height:calc(100vh - 40px)` | Modal never exceeds viewport | PASS |
| 38 | `rp-modal-box` has `overflow-y:auto` | Box scrolls internally | PASS |
| 39 | `rp-modal-box` has `display:flex;flex-direction:column` | Flex column layout | PASS |
| 40 | Sticky header bar present inside modal box | `position:sticky;top:0` | PASS |
| 41 | Close button inside sticky header | Never scrolls out of view | PASS |
| 42 | Sticky header has `z-index:5` | Stays above scrolled content | PASS |
| 43 | Sticky header has matching `background:var(--card)` | No bleed-through | PASS |
| 44 | Sticky header has `border-bottom` separator | Visual separation from content | PASS |
| 45 | Close button text "✕ Close" | Clearly labelled | PASS |
| 46 | Close button uses `border-radius:8px` styled button | Visible, not just an ✕ character | PASS |
| 47 | `rp-modal-content` has `padding:24px 28px 28px` | Content spacing preserved | PASS |
| 48 | Backdrop click still calls `closeRpModal()` | `onclick="if(event.target===this)..."` | PASS |
| 49 | `rp-modal` overlay has `padding:20px 12px` | Box centered with breathing room | PASS |
| 50 | Tall country card (6 data sections) shows close | Close always in view regardless of content height | PASS |

## Phase REG — Regression Tests

| # | Test | Expected | Result |
|---|------|----------|--------|
| 51 | All 12 news tabs still present | world/europe/americas/asia/africa/oceania/tech/sports/ai/energy/education/metals | PASS |
| 52 | `showNewsTab` active class still works | `.ntab-btn.active` applied on click | PASS |
| 53 | News 90s auto-refresh unchanged | `_startNewsAutoRefresh` IIFE present | PASS |
| 54 | `NEWS_FALLBACK` populated for all 12 tabs | Offline display safe | PASS |
| 55 | Original 3 proxies still present | corsproxy.io + allorigins + rss2json | PASS |
| 56 | `showRpSubTab` 6-tab forEach unchanged | All panels show/hide correctly | PASS |
| 57 | Lazy-load guards intact | `_ncLiveLoaded` / `_ppLiveLoaded` preserved | PASS |
| 58 | Rising Powers 6 sub-tabs function | Cards/NextChina/Migration/Passport/Language/NewNations | PASS |
| 59 | `initRisingPowers` render cycle unchanged | `renderRpCards` → fetch → autoRefresh | PASS |
| 60 | World Map all layers intact | risk/growth/inflation/population/alliance | PASS |
| 61 | Future Geopolitics panel intact | `#map-future-panel` + `toggleFuturePanel` | PASS |
| 62 | Trade Corridors panel intact | `initTradeCorridor` | PASS |
| 63 | Country Compare panel intact | `initCountryCompare` | PASS |
| 64 | Markets 5 tabs intact | `initMarkets` unchanged | PASS |
| 65 | World Bank APIs unchanged | GDP/Population/Tourism free API calls | PASS |
| 66 | JS syntax clean | `new Function(jsBlock)` → no SyntaxError | PASS |
| 67 | File ends `</html>` | No truncation | PASS |
| 68 | File size ~489KB | Content added, nothing lost | PASS |
| 69 | Version title = v3.18 | `<title>World Intelligence Platform v3.18</title>` | PASS |
| 70 | Version badge = v3.18 | `<span class="badge">v3.18</span>` | PASS |
| 71 | `version.py` = 3.18.0 | `APP_VERSION = "3.18.0"` | PASS |

---

## Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| Live-Pulse Structure Fix | 7 | 7 | 0 |
| Sub-tab Persistence (Full Fix) | 12 | 12 | 0 |
| News Proxy Expansion | 17 | 17 | 0 |
| Modal Close Button Fix | 14 | 14 | 0 |
| Regression | 21 | 21 | 0 |
| **TOTAL** | **71** | **71** | **0** |

**All 71 tests pass. Rising Powers sub-tab now fully persists across F5 page refreshes via localStorage. News tab has 5 CORS proxy chains (codetabs.com + thingproxy.freeboard.io added) — significantly reduces "not connecting" failures. Modal close button now in a sticky header bar that is always visible regardless of content height. Live-pulse indicator moved outside the ntabs flex container for clean tab display.**

---

## Architecture Notes

| Component | Details |
|-----------|---------|
| Sub-tab persistence key | `localStorage.getItem/setItem('wip_rp_subtab')` |
| Restore priority | `window._lastRpSubTab` (memory) → localStorage → default Cards |
| Proxy chain count | 5 parallel chains: corsproxy.io + allorigins + rss2json + codetabs + thingproxy |
| Proxy chain selection | All fire simultaneously via `Promise.allSettled` |
| Modal layout | flex-direction:column, sticky header, scrollable content div |
| Paid APIs | None — all free public RSS + free CORS proxies |
| GitHub README | Screenshots use `./screenshots/` relative paths (correct for private repo) |

*— Muhammad Umer Lari, World Intelligence Platform v3.18*
