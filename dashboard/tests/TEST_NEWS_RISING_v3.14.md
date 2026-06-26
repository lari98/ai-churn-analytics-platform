# Test Report — News Parallel Fix + Rising Powers Sub-tabs v3.14
**World Intelligence Platform v3.14**
**Author: Muhammad Umer Lari | Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**
**Free APIs: Google News RSS (free, no key) · corsproxy.io · allorigins.win · rss2json.com · World Bank (4 indicators) — Zero paid APIs**

---

## What Changed in v3.14

| # | Change | Detail |
|---|--------|--------|
| 1 | **CRITICAL FIX: News tab parallel fetch** | Sequential fetch (27s wait) → ALL sources fired simultaneously → max 8s wait. Tabs now always show content. |
| 2 | **`renderNewsTab` restored** | Function was missing from v3.13 (dropped during block replacement). Cards now render correctly. |
| 3 | **Google News RSS added as primary** | `news.google.com/rss/search?q={topic}` added to all 7 regions as first feed — highly reliable via proxy |
| 4 | **11 world news sources** | Google News + BBC + DW + Al Jazeera + Reuters + Guardian + NPR + France 24 + Euronews + NHK + CSMonitor |
| 5 | **Live loading indicator** | Shows source names during fetch, turns green when articles arrive |
| 6 | **Refresh button on news tabs** | Each region has a "↺ Refresh" button to force-reload |
| 7 | **Live article count badge** | Shows "🟢 N Live Articles" vs "📌 Cached" on each region |
| 8 | **Fallback links now go to Google News search** | Embedded fallback articles link to Google News searches instead of `#` |
| 9 | **`nextChina:true` removed from PK CTRY** | Pakistan treated same as all other countries — no special flag |
| 10 | **Rising Powers 3 sub-tabs** | Navigation bar: 🃏 Rising Powers \| 🏭 Next China \| ✈️ Future Migration |
| 11 | **"Next China" sub-tab** | Scorecard: 6 candidates × 6 WB indicators. India/Vietnam/Indonesia deep-dive cards. Live WB fetch on tab open. |
| 12 | **"Future Migration" sub-tab** | Top 10 near-future (2025–2035) job destinations + 8 extended-future (2035–2050) projected destinations |
| 13 | **`showRpSubTab(tab,btn)`** | Sub-tab switcher with active state styling |
| 14 | **`_fetchNextChinaLive()`** | WB FDI + Exports + GDP for 6 Next China candidates — lazy-loads on tab open |
| 15 | **Version bumped to v3.14** | title, badge, version.py all updated |

---

## Phase N — News Parallel Fix

| # | Test | Expected | Result |
|---|------|----------|--------|
| 1 | `renderNewsTab` function defined | Function in JS scope (was missing in v3.13) | PASS |
| 2 | Parallel fetch — all sources fired at once | `Promise.allSettled([backendFetch,...cproxFetches,...aoFetches,...r2jFetches])` | PASS |
| 3 | Max wait time ~8s (was 27s) | Single `await Promise.allSettled(allFetches)` | PASS |
| 4 | Loading indicator shown immediately | `el.innerHTML` set before any await | PASS |
| 5 | Source dots shown during load | `id="nsd-{region}-{i}"` spans | PASS |
| 6 | Source dots turn green when articles arrive | `dot.style.background='rgba(16,185,129,.2)'` | PASS |
| 7 | Live count badge shown | `liveCount>0` → "🟢 N Live Articles" | PASS |
| 8 | "📌 Cached" shown for fallback | `liveCount===0` branch | PASS |
| 9 | Refresh button per region | `onclick="delete newsCache[...];loadNewsTab(...)` | PASS |
| 10 | Fallback links go to Google News search | `link:'https://news.google.com/search?q=...'` | PASS |
| 11 | renderNewsTab handles 0-article edge case | "⚠ No articles found" message | PASS |
| 12 | newsCache stores 30 articles (was 24) | `arts.slice(0,30)` | PASS |
| 13 | Ticker gets 15 articles | `arts.slice(0,15)` | PASS |

## Phase G — Google News RSS + 11 World Sources

| # | Test | Expected | Result |
|---|------|----------|--------|
| 14 | Google News in world feeds | `news.google.com/rss/search?q=world+news` | PASS |
| 15 | Google News in all 7 regions | europe/americas/asia/africa/oceania/tech all have Google feed | PASS |
| 16 | BBC World present | `feeds.bbci.co.uk/news/world/rss.xml` | PASS |
| 17 | DW World present | `rss.dw.com/rdf/rss-en-world` | PASS |
| 18 | Al Jazeera present | `aljazeera.com/xml/rss/all.xml` | PASS |
| 19 | Reuters present | `feeds.reuters.com/reuters/topNews` | PASS |
| 20 | The Guardian present | `theguardian.com/world/rss` | PASS |
| 21 | NPR World present | `feeds.npr.org/1004/rss.xml` | PASS |
| 22 | France 24 present | `france24.com/en/rss` | PASS |
| 23 | Euronews present | `euronews.com/rss` | PASS |
| 24 | NHK World present | `nhk.or.jp/nhkworld/en/news/feeds/rss.xml` | PASS |
| 25 | CSMonitor present | `rss.csmonitor.com/feeds/world` | PASS |
| 26 | Total world feeds = 11 | Array length 11 | PASS |

## Phase RP — Rising Powers Sub-tabs

| # | Test | Expected | Result |
|---|------|----------|--------|
| 27 | Sub-tab nav buttons present | 3 buttons: 🃏 Rising Powers / 🏭 Next China / ✈️ Future Migration | PASS |
| 28 | `showRpSubTab(tab,btn)` defined | Function in JS scope | PASS |
| 29 | `#rp-panel-cards` present | Default visible panel | PASS |
| 30 | `#rp-panel-nextchina` present | Initially hidden (`display:none`) | PASS |
| 31 | `#rp-panel-migration` present | Initially hidden (`display:none`) | PASS |
| 32 | Active button styled (accent colour) | `background:var(--accent);color:#fff` | PASS |
| 33 | Inactive buttons muted | `background:var(--card);color:var(--muted)` | PASS |
| 34 | Panel switch shows only one panel | `['cards','nextchina','migration'].forEach` sets display | PASS |
| 35 | _fetchNextChinaLive called lazily | `!window._ncLiveLoaded` guard | PASS |
| 36 | `nextChina:true` removed from PK CTRY | `rising:true` only — neutral flag | PASS |
| 37 | showCtt badge uses generic 'RISING' | No more 'NEXT CHINA' special badge | PASS |

## Phase NC — Next China Sub-tab

| # | Test | Expected | Result |
|---|------|----------|--------|
| 38 | Next China scorecard table present | 6 candidates × 7 columns | PASS |
| 39 | India ranked #1 (82/100) | Score 82 shown | PASS |
| 40 | Vietnam ranked #2 (79/100) | Score 79 shown | PASS |
| 41 | Indonesia ranked #3 (74/100) | Score 74 shown | PASS |
| 42 | Bangladesh, Mexico, Ethiopia included | Scores 71/68/58 | PASS |
| 43 | `nc-fdi-{iso}` cells for live update | `_fetchNextChinaLive` targets them | PASS |
| 44 | `nc-exp-{iso}` cells for live update | Exports % GDP live | PASS |
| 45 | `nc-gdp-{iso}` cells for live update | GDP growth live | PASS |
| 46 | `_fetchNextChinaLive()` defined | Function in JS scope | PASS |
| 47 | WB FDI fetch: `BX.KLT.DINV.WD.GD.ZS` | Correct indicator | PASS |
| 48 | WB Exports fetch: `NE.EXP.GNFS.ZS` | Correct indicator | PASS |
| 49 | WB GDP fetch: `NY.GDP.MKTP.KD.ZG` | Correct indicator | PASS |
| 50 | India deep-dive card present | border-top orange, 6 bullet points | PASS |
| 51 | Vietnam deep-dive card present | border-top green, export stats | PASS |
| 52 | Indonesia deep-dive card present | border-top purple, nickel stats | PASS |
| 53 | Free APIs — no key required | All 3 WB endpoints are public | PASS |

## Phase MIG — Future Migration Sub-tab

| # | Test | Expected | Result |
|---|------|----------|--------|
| 54 | Near Future section (2025–2035) | 10 destination country cards | PASS |
| 55 | Canada ranked #1 (96/100) | Express Entry, 485K/yr target | PASS |
| 56 | Germany ranked #2 (94/100) | Opportunity Card 2024 | PASS |
| 57 | UAE ranked #3 (92/100) | Golden Visa 10yr | PASS |
| 58 | Australia, UK, Singapore, NL, CH, PT, NZ in top 10 | All 10 cards rendered | PASS |
| 59 | Each card shows: jobs, visa path, why text | 3 data fields per card | PASS |
| 60 | Cards colour-coded by opportunity score | `border-left:3px solid ${r.col}` | PASS |
| 61 | Extended Future (2035–2050) table present | 8 countries in table | PASS |
| 62 | Malaysia, Romania, Poland, S.Korea, Japan in extended table | 5 of 8 checked | PASS |
| 63 | Projected arrivals/yr column | Numbers like "600K+" | PASS |
| 64 | "3 Forces" megatrend panel | Demographic Gravity, Climate, Supply Chain | PASS |
| 65 | Source footnote: IOM/UNHCR/OECD | Attribution at bottom | PASS |

## Phase REG — Regression

| # | Test | Expected | Result |
|---|------|----------|--------|
| 66 | 15 Rising Powers cards still render | renderRpCards(['IN','CN',...'TH']) | PASS |
| 67 | Drill-down modal still works | rpDrillDown + closeRpModal intact | PASS |
| 68 | Auto-refresh 8min still active | `window._rpRefreshTimer` | PASS |
| 69 | WB live data (GDP/FDI/Pop/Exports) intact | `_fetchRpLiveData` unaffected | PASS |
| 70 | World Map all 56 markers intact | initMap unchanged | PASS |
| 71 | Markets 5 tabs intact | initMarkets unchanged | PASS |
| 72 | Forecast volatility bands intact | `_calcVolBands` unchanged | PASS |
| 73 | All 12 tabs init correctly | showPage switches intact | PASS |
| 74 | JS syntax clean | `node --check` → 0 errors | PASS |
| 75 | File ends `</html>` | No truncation | PASS |
| 76 | Version badge shows v3.14 | `<span class="badge">v3.14</span>` | PASS |

---

## Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| News Parallel Fix | 13 | 13 | 0 |
| Google News RSS + 11 Sources | 13 | 13 | 0 |
| Rising Powers Sub-tabs | 11 | 11 | 0 |
| Next China Sub-tab | 16 | 16 | 0 |
| Future Migration Sub-tab | 12 | 12 | 0 |
| Regression | 11 | 11 | 0 |
| **TOTAL** | **76** | **76** | **0** |

**All 76 tests pass. News tabs now load in max 8s (was 27s+). renderNewsTab restored. Google News RSS added. Rising Powers has 3 sub-tabs: Rising Powers cards, Next China scorecard with live WB data, and Future Migration with 10 near-future + 8 extended-future destinations. Zero paid APIs.**

---

## Root Cause Analysis

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| News tabs showed spinner forever | Sequential fallback: backend(3s)→corsproxy(9s)→allorigins(9s)→rss2json(8s) = up to 29s before fallback | Parallel: all sources fired simultaneously, 8s max |
| News cards never rendered | `renderNewsTab()` function was missing — dropped when news block was replaced in v3.13 | Function restored with improved card rendering + live badge |
| Pakistan-hero remnant | `nextChina:true` still in `CTRY['PK']` and `showCtt` badge showed "NEXT CHINA" | Flag removed, badge uses generic "RISING" |

*— Muhammad Umer Lari, World Intelligence Platform v3.14*
