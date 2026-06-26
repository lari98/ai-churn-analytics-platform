# Test Report — Sub-tab Persistence Fix + 5 New News Tabs v3.17
**World Intelligence Platform v3.17**
**Author: Muhammad Umer Lari | Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**
**Free APIs: Google News RSS · BBC Sport · DW · Sky Sports · ESPN · TechCrunch · Wired · VentureBeat · CleanTechnica · Electrek · PV Magazine · Edutopia · EdSurge · Kitco · Mining.com — Zero paid APIs**

---

## What Changed in v3.17

| # | Change | Detail |
|---|--------|--------|
| 1 | **🐛 Sub-tab persistence fix** | Rising Powers sub-tab no longer resets to 'cards' on page revisit |
| 2 | **`window._lastRpSubTab` tracker** | Set at top of `showRpSubTab()` — persists chosen tab in memory |
| 3 | **Auto-restore in `initRisingPowers`** | After `renderRpCards`, restores last tab via `requestAnimationFrame` if not 'cards' |
| 4 | **⚽ Sports news tab** | BBC Sport, DW Sports, Sky Sports, ESPN + Google News Sports |
| 5 | **🤖 AI news tab** | TechCrunch AI, Wired AI, VentureBeat AI, Ars Technica AI + Google News AI |
| 6 | **⚡ Future Energy news tab** | CleanTechnica, Electrek, PV Magazine, Reuters Business + Google News Energy |
| 7 | **🎓 Education news tab** | BBC Education, Edutopia, EdSurge, Campus Technology + Google News Education |
| 8 | **🪙 Metals news tab** | Kitco, Mining.com, Reuters Commodities + 2× Google News (Metals + Rare Earth) |
| 9 | **Fallback headlines** | 3 fallback headlines per new tab (offline-safe display) |
| 10 | **Version bumped to v3.17** | `<title>`, `.badge`, `version.py` all updated |

---

## Phase SP — Sub-tab Persistence Fix

| # | Test | Expected | Result |
|---|------|----------|--------|
| 1 | `window._lastRpSubTab=tab` in `showRpSubTab` | First line of function sets tracker | PASS |
| 2 | Tracker set for all 6 sub-tabs | cards/nextchina/migration/passport/language/newnations | PASS |
| 3 | Restore block present in `initRisingPowers` | After `renderRpCards(rpCountries)` | PASS |
| 4 | Guard: `window._lastRpSubTab!=='cards'` | No restore needed for default tab | PASS |
| 5 | Restore uses `requestAnimationFrame` | After DOM is updated | PASS |
| 6 | Restore fetches correct button | `getElementById('rp-st-'+window._lastRpSubTab)` | PASS |
| 7 | Calls `showRpSubTab` with btn reference | Active button styling restored correctly | PASS |
| 8 | No restore if `_lastRpSubTab` undefined | First visit still shows cards | PASS |
| 9 | Navigate to "Passport Power" → leave → return | Stays on Passport Power tab | PASS |
| 10 | Navigate to "Language Future" → leave → return | Stays on Language Future tab | PASS |
| 11 | Navigate to "New Nations" → leave → return | Stays on New Nations tab | PASS |
| 12 | Lazy-load guards still fire on restore | `_ppLiveLoaded` / `_ncLiveLoaded` unchanged | PASS |

## Phase NT — News Tabs: Sports ⚽

| # | Test | Expected | Result |
|---|------|----------|--------|
| 13 | `ntab-btn` with `showNewsTab('sports',this)` | Button in nav bar | PASS |
| 14 | Button label "⚽ Sports" | Emoji + text | PASS |
| 15 | `#news-sports` div present | news-region div with spinner | PASS |
| 16 | `NFEEDS.sports` defined | 5 feeds array | PASS |
| 17 | Google News Sports URL | `q=sports+football+cricket+tennis` | PASS |
| 18 | BBC Sport feed | `feeds.bbci.co.uk/sport/rss.xml` | PASS |
| 19 | DW Sports feed | `rss.dw.com/rdf/rss-en-sports` | PASS |
| 20 | Sky Sports feed | `skysports.com/rss/12040` | PASS |
| 21 | ESPN feed | `espn.com/espn/rss/news` | PASS |
| 22 | Sports fallback headline | World Cup 2026 qualifying entry | PASS |
| 23 | All sports feeds free, no key | Zero paid/authenticated APIs | PASS |

## Phase NT — News Tabs: AI 🤖

| # | Test | Expected | Result |
|---|------|----------|--------|
| 24 | `ntab-btn` with `showNewsTab('ai',this)` | Button in nav bar | PASS |
| 25 | Button label "🤖 AI" | Emoji + text | PASS |
| 26 | `#news-ai` div present | news-region div with spinner | PASS |
| 27 | `NFEEDS.ai` defined | 5 feeds array | PASS |
| 28 | Google News AI URL | `q=artificial+intelligence+machine+learning` | PASS |
| 29 | TechCrunch AI feed | `techcrunch.com/category/artificial-intelligence/feed/` | PASS |
| 30 | Wired AI feed | `wired.com/feed/tag/artificial-intelligence/rss` | PASS |
| 31 | VentureBeat AI feed | `venturebeat.com/category/ai/feed/` | PASS |
| 32 | Ars Technica AI feed | `arstechnica.com/technology-lab` | PASS |
| 33 | AI fallback headline | LLM benchmark milestones entry | PASS |
| 34 | All AI feeds free, no key | Zero paid APIs | PASS |

## Phase NT — News Tabs: Future Energy ⚡

| # | Test | Expected | Result |
|---|------|----------|--------|
| 35 | `ntab-btn` with `showNewsTab('energy',this)` | Button in nav bar | PASS |
| 36 | Button label "⚡ Future Energy" | Emoji + text | PASS |
| 37 | `#news-energy` div present | news-region div with spinner | PASS |
| 38 | `NFEEDS.energy` defined | 5 feeds array | PASS |
| 39 | Google News Energy URL | `q=renewable+energy+solar+wind+hydrogen` | PASS |
| 40 | Reuters Business feed | `feeds.reuters.com/reuters/businessNews` | PASS |
| 41 | CleanTechnica feed | `cleantechnica.com/feed/` | PASS |
| 42 | Electrek feed | `electrek.co/feed/` | PASS |
| 43 | PV Magazine feed | `pv-magazine.com/feed/` | PASS |
| 44 | Energy fallback headline | Solar capacity record entry | PASS |
| 45 | All energy feeds free, no key | Zero paid APIs | PASS |

## Phase NT — News Tabs: Education 🎓

| # | Test | Expected | Result |
|---|------|----------|--------|
| 46 | `ntab-btn` with `showNewsTab('education',this)` | Button in nav bar | PASS |
| 47 | Button label "🎓 Education" | Emoji + text | PASS |
| 48 | `#news-education` div present | news-region div with spinner | PASS |
| 49 | `NFEEDS.education` defined | 5 feeds array | PASS |
| 50 | Google News Education URL | `q=future+education+edtech+learning` | PASS |
| 51 | BBC Education feed | `feeds.bbci.co.uk/news/education/rss.xml` | PASS |
| 52 | Edutopia feed | `edutopia.org/feeds/all` | PASS |
| 53 | EdSurge feed | `edsurge.com/news.rss` | PASS |
| 54 | Campus Technology feed | `campustechnology.com/rss-feeds/ct-news.aspx` | PASS |
| 55 | Education fallback headline | AI tutoring systems entry | PASS |
| 56 | All education feeds free, no key | Zero paid APIs | PASS |

## Phase NT — News Tabs: Metals & Commodities 🪙

| # | Test | Expected | Result |
|---|------|----------|--------|
| 57 | `ntab-btn` with `showNewsTab('metals',this)` | Button in nav bar | PASS |
| 58 | Button label "🪙 Metals" | Emoji + text | PASS |
| 59 | `#news-metals` div present | news-region div with spinner | PASS |
| 60 | `NFEEDS.metals` defined | 5 feeds array | PASS |
| 61 | Google News Metals URL | `q=gold+silver+copper+lithium+commodities` | PASS |
| 62 | Reuters Commodities feed | `feeds.reuters.com/reuters/companyNews` | PASS |
| 63 | Kitco feed | `kitco.com/rss/kitconews.rss` | PASS |
| 64 | Mining.com feed | `mining.com/feed/` | PASS |
| 65 | Google News Rare Earth feed | `q=iron+ore+cobalt+rare+earth+metals` | PASS |
| 66 | Metals fallback headline | Gold record highs entry | PASS |
| 67 | All metals feeds free, no key | Zero paid APIs | PASS |

## Phase NS — News System Integration

| # | Test | Expected | Result |
|---|------|----------|--------|
| 68 | Total news tabs now 12 | world/europe/americas/asia/africa/oceania/tech + 5 new | PASS |
| 69 | `showNewsTab` works for all 12 keys | `NFEEDS[region]` resolves correctly | PASS |
| 70 | `NEWS_FALLBACK` populated for all 12 | Fallback for every tab | PASS |
| 71 | Existing 7 tabs unaffected | world/europe/americas/asia/africa/oceania/tech unchanged | PASS |
| 72 | Parallel fetch fires for new tabs | `Promise.allSettled([...allFetches])` same pattern | PASS |
| 73 | CORS proxy chain applies to new tabs | corsproxy.io → allorigins → rss2json | PASS |
| 74 | New news-region divs initially hidden | `.news-region` CSS `display:none` except active | PASS |
| 75 | News ticker shows new tab items if active | `renderNewsTab` renders all 12 tabs same way | PASS |

## Phase REG — Regression

| # | Test | Expected | Result |
|---|------|----------|--------|
| 76 | showRpSubTab 6-tab forEach unchanged | cards/nextchina/migration/passport/language/newnations | PASS |
| 77 | Lazy-load guards intact | `_ncLiveLoaded` / `_ppLiveLoaded` preserved | PASS |
| 78 | Rising Powers 6 sub-tabs still function | All panels show/hide correctly | PASS |
| 79 | initRisingPowers render cycle unchanged | renderRpCards → fetch → autoRefresh timer | PASS |
| 80 | World Map all layers intact | risk/growth/inflation/population unchanged | PASS |
| 81 | Alliance layer intact | NATO/SCO/BRICS+/ASEAN/EU toggles unchanged | PASS |
| 82 | Future Geopolitics panel intact | `#map-future-panel` + `toggleFuturePanel` | PASS |
| 83 | Existing 7 NFEEDS entries intact | world/europe/americas/asia/africa/oceania/tech unchanged | PASS |
| 84 | Markets 5 tabs intact | `initMarkets` unchanged | PASS |
| 85 | JS syntax clean | `new Function(jsBlock)` → OK | PASS |
| 86 | File ends `</html>` | No truncation | PASS |
| 87 | File size: 472KB (up from 466KB) | Content added, nothing lost | PASS |
| 88 | Version badge shows v3.17 | `<span class="badge">v3.17</span>` | PASS |
| 89 | version.py shows 3.17.0 | `APP_VERSION = "3.17.0"` | PASS |

---

## Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| Sub-tab Persistence Fix | 12 | 12 | 0 |
| Sports Tab | 11 | 11 | 0 |
| AI Tab | 11 | 11 | 0 |
| Future Energy Tab | 11 | 11 | 0 |
| Education Tab | 11 | 11 | 0 |
| Metals Tab | 11 | 11 | 0 |
| News System Integration | 8 | 8 | 0 |
| Regression | 14 | 14 | 0 |
| **TOTAL** | **89** | **89** | **0** |

**All 89 tests pass. Rising Powers sub-tab state now persists when navigating away and back — no more reset to 'cards'. News section expanded from 7 to 12 tabs: added Sports (BBC/DW/Sky/ESPN), AI (TechCrunch/Wired/VentureBeat/Ars Technica), Future Energy (CleanTechnica/Electrek/PV Magazine/Reuters), Education (BBC/Edutopia/EdSurge), Metals (Kitco/Mining.com/Reuters). All 25 new RSS feeds are free with no API key. Parallel proxy-chain fetch applies to all new tabs automatically.**

---

## Architecture Notes

| Component | Details |
|-----------|---------|
| Persistence mechanism | `window._lastRpSubTab` (in-memory JS var, session-scoped) |
| Restore trigger | `requestAnimationFrame` after `renderRpCards` in `initRisingPowers` |
| New feed count | 25 new RSS feeds across 5 tabs (5 per tab) |
| Feed sources | Google News RSS (free, no key) + BBC/DW/Reuters/TechCrunch/Wired/Kitco etc. (free public RSS) |
| Proxy chain | corsproxy.io → allorigins.win → rss2json.com (unchanged) |
| Fallback headlines | 3 per new tab, hardcoded for offline-safe display |
| Paid APIs | None — all free public RSS feeds |

*— Muhammad Umer Lari, World Intelligence Platform v3.17*
