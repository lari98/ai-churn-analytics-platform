# Test Report — Rising Powers Sub-tabs + World Map Ultra-Advanced v3.16
**World Intelligence Platform v3.16**
**Author: Muhammad Umer Lari | Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**
**Free APIs: World Bank (SP.POP.TOTL, ST.INT.ARVL, NY.GDP.MKTP.KD.ZG) · Leaflet.js · Zero paid APIs**

---

## What Changed in v3.16

| # | Change | Detail |
|---|--------|--------|
| 1 | **🛂 Passport Power sub-tab** | Henley Index 2024 Top 10 · Rising Fastest table · 2035 Projections · Investment Citizenship programs |
| 2 | **🗣 Language Future sub-tab** | 8 post-English languages with speaker counts, career sectors, 2050 power ratings · AI language impact panel |
| 3 | **🌐 New Nations sub-tab** | De facto states · Very High/Medium/Wildcard independence movements with probability % · Timeline of nations born since 2000 |
| 4 | **`showRpSubTab` extended** | forEach now covers 6 tabs: cards/nextchina/migration/passport/language/newnations |
| 5 | **Passport lazy-load** | `_fetchPassportLive()` called once on first passport tab open — WB ST.INT.ARVL tourism arrivals |
| 6 | **🌍 Population layer (World Map)** | "Pop" button added to map layer controls · colours by log-scale population |
| 7 | **`_popCol(pop)` function** | 6-tier logarithmic colour scale (>800M red → <8M indigo) |
| 8 | **`_fetchWBPopulation()`** | WB SP.POP.TOTL lazy-load on first Pop layer click · static fallback for 55 countries |
| 9 | **⚔ Alliance Layer (World Map)** | 5 toggle buttons: NATO 🔵 / SCO 🔴 / BRICS+ 🟠 / ASEAN 🟡 / EU 🟣 |
| 10 | **`_ALLIANCES` constant** | 5 alliance definitions with members + hex colour |
| 11 | **`toggleAlliancesLayer(key,btn)`** | Draws/removes outer rings on member countries via L.circleMarker. Multiple alliances stackable. |
| 12 | **`setMapLayer` updated** | forEach includes 'population' · population branch + lazy-load guard |
| 13 | **Version bumped to v3.16** | `<title>`, `.badge`, `version.py` all updated |

---

## Phase PP — Passport Power Sub-tab

| # | Test | Expected | Result |
|---|------|----------|--------|
| 1 | `#rp-st-passport` button present | Button with id rp-st-passport in sub-tab nav | PASS |
| 2 | Button label "🛂 Passport Power" | Text content correct | PASS |
| 3 | `#rp-panel-passport` panel present | Hidden panel div with correct id | PASS |
| 4 | Panel initially hidden | `display:none` | PASS |
| 5 | Clicking passport button shows panel | `showRpSubTab('passport',this)` | PASS |
| 6 | Henley Top 10 table present | 10 country rows in current rankings | PASS |
| 7 | Japan #1 with 193 destinations | First row correct | PASS |
| 8 | Singapore #2 with 192 | Second row correct | PASS |
| 9 | US shows declining forecast (180) | Red colour on 2035 column | PASS |
| 10 | Rising table: UAE +152 | Fastest riser in 20 years | PASS |
| 11 | `#pp-live-badge` element | Live WB tourism badge | PASS |
| 12 | `#pp-gain-ae` cell for live update | UAE gain cell updatable by `_fetchPassportLive` | PASS |
| 13 | 2035 projections grid: 6 cards | UAE Top5 / India Top30 / SA Top40 / US Declining / China / Singapore | PASS |
| 14 | Investment citizenship: 6 programs | Malta/Portugal/St Kitts/Dominica/UAE/Jordan | PASS |
| 15 | Source attribution present | Henley/Arton/OECD/WB cited | PASS |
| 16 | `_fetchPassportLive()` defined | Function in JS scope | PASS |
| 17 | Lazy-load guard: `!window._ppLiveLoaded` | Called only once on first open | PASS |
| 18 | WB indicator ST.INT.ARVL used | Tourism arrivals endpoint | PASS |
| 19 | Free API: WB public endpoint | No key required | PASS |

## Phase LF — Language Future Sub-tab

| # | Test | Expected | Result |
|---|------|----------|--------|
| 20 | `#rp-st-language` button present | Button with correct id | PASS |
| 21 | Button label "🗣 Language Future" | Text content correct | PASS |
| 22 | `#rp-panel-language` panel present | Hidden panel div | PASS |
| 23 | 8 language cards in grid | Mandarin/Spanish/Arabic/Hindi/French/Swahili/Indonesian/Bengali | PASS |
| 24 | Mandarin: 1.12B native speakers | Largest native base | PASS |
| 25 | Spanish: 2050 power "VERY HIGH" | Americas + US demographics | PASS |
| 26 | French: 321M now → 700M by 2050 | Africa boom projection | PASS |
| 27 | Each card has border-left colour | Unique accent per language | PASS |
| 28 | Each card has career sector chips | Finance/Trade/MENA etc. | PASS |
| 29 | Each card has 2050 power badge | GREEN chip with rating | PASS |
| 30 | AI impact panel present | 4 quadrants: Amplify/Threaten/Hybrid/Career Bets | PASS |
| 31 | Bengali "UNDERRATED" badge | 7th most spoken, underrated | PASS |
| 32 | Swahili "EMERGING" badge | AfCFTA integration language | PASS |
| 33 | Source attribution | Ethnologue/UN/OIF/WEF cited | PASS |

## Phase NN — New Nations Sub-tab

| # | Test | Expected | Result |
|---|------|----------|--------|
| 34 | `#rp-st-newnations` button present | Button with correct id | PASS |
| 35 | Button label "🌐 New Nations" | Text content correct | PASS |
| 36 | `#rp-panel-newnations` panel present | Hidden panel div | PASS |
| 37 | De facto states section (4 entries) | Kosovo/Palestine/Somaliland/Taiwan | PASS |
| 38 | Kosovo: 101/193 recognition badge | Partial recognition shown | PASS |
| 39 | Palestine: 146/193 nations | Growing recognition wave detail | PASS |
| 40 | Taiwan: TSMC geopolitical detail | "Makes Taiwan irreplaceable" | PASS |
| 41 | Very High probability section | Bougainville 92% / New Caledonia 65% | PASS |
| 42 | Bougainville: 98.31% referendum detail | "2019 referendum" | PASS |
| 43 | Medium probability section | Scotland 45% / Iraqi Kurdistan 40% / Flanders 30% | PASS |
| 44 | Scotland 45% probability | SNP majority + Brexit fallout | PASS |
| 45 | Wild Cards section: 6 entries | Azawad/Catalonia/Cabinda/Quebec/Hawaii/E.DRC | PASS |
| 46 | Recent independence timeline (4 nations) | Timor-Leste 2002 / Montenegro 2006 / Kosovo 2008 / South Sudan 2011 | PASS |
| 47 | South Sudan: "193rd UN member" | Youngest nation detail | PASS |
| 48 | Probability scores shown | % badges on each entry | PASS |
| 49 | Source attribution | UN/CFR/RAND/Carnegie/ICJ cited | PASS |

## Phase ST — Sub-tab System

| # | Test | Expected | Result |
|---|------|----------|--------|
| 50 | `showRpSubTab` forEach includes 6 tabs | cards/nextchina/migration/passport/language/newnations | PASS |
| 51 | Only one panel visible at a time | forEach sets display:none on all others | PASS |
| 52 | Active button accent-coloured | `background:var(--accent);color:#fff` | PASS |
| 53 | Inactive buttons muted | `background:var(--card);color:var(--muted)` | PASS |
| 54 | Existing 3 tabs still work | cards/nextchina/migration unchanged | PASS |
| 55 | `_ncLiveLoaded` guard preserved | Next China lazy-load intact | PASS |
| 56 | `_ppLiveLoaded` guard added | Passport lazy-load new | PASS |

## Phase POP — Population Layer (World Map)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 57 | `#mlbtn-population` button present | 4th layer button in map-stats | PASS |
| 58 | Button label "Pop" | Compact label | PASS |
| 59 | `setMapLayer('population',this)` onclick | Correct handler | PASS |
| 60 | `_popCol(pop)` defined | Function in JS scope | PASS |
| 61 | _popCol(1.5e9) = #dc2626 (red) | >800M tier | PASS |
| 62 | _popCol(5e7) = #0891b2 (cyan) | 8M-80M tier | PASS |
| 63 | _popCol(null) = #475569 (muted) | Unknown/null case | PASS |
| 64 | `_fetchWBPopulation()` defined | Function in JS scope | PASS |
| 65 | WB indicator SP.POP.TOTL | Correct population endpoint | PASS |
| 66 | Lazy-load guard: `!window._popLoaded` | Fetch triggered only once | PASS |
| 67 | Static fallback: 55 countries | fp object with major nations | PASS |
| 68 | setMapLayer forEach includes 'population' | Button styling works for all 4 modes | PASS |
| 69 | Population branch in colour loop | `else if(mode==='population')` | PASS |
| 70 | Free API: WB public endpoint | No key required | PASS |

## Phase AL — Alliance Layer (World Map)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 71 | `_ALLIANCES` constant defined | 5 alliance objects with col/label/members | PASS |
| 72 | NATO: col #3b82f6, 28 members | Blue ring | PASS |
| 73 | SCO: col #ef4444, 9 members | Red ring | PASS |
| 74 | BRICS+: col #f97316, 9 members | Orange ring | PASS |
| 75 | ASEAN: col #eab308, 10 members | Yellow ring | PASS |
| 76 | EU: col #8b5cf6, 26 members | Purple ring | PASS |
| 77 | `#albtn-nato` button present | NATO toggle button in map-stats | PASS |
| 78 | `#albtn-sco` button present | SCO toggle button | PASS |
| 79 | `#albtn-brics` button present | BRICS+ toggle button | PASS |
| 80 | `#albtn-asean` button present | ASEAN toggle button | PASS |
| 81 | `#albtn-eu` button present | EU toggle button | PASS |
| 82 | `toggleAlliancesLayer(key,btn)` defined | Function in JS scope | PASS |
| 83 | Toggle on: draws L.circleMarker rings | `L.circleMarker` with fill:false | PASS |
| 84 | Toggle off: removes all rings | `leafMap.removeLayer(m)` | PASS |
| 85 | Multiple alliances stackable | `_allianceActive` per-key state | PASS |
| 86 | Ring has tooltip with alliance name | `m.bindTooltip(al.label+':'+name)` | PASS |
| 87 | Ring non-interactive | `interactive:false` | PASS |
| 88 | Active button semi-fill colour | `background:al.col+'22'` | PASS |
| 89 | `typeof leafMap!=='undefined'` guard | Safe if map not loaded | PASS |
| 90 | Alliance section in map-stats panel | Under "⚔ Alliances" heading | PASS |

## Phase REG — Regression

| # | Test | Expected | Result |
|---|------|----------|--------|
| 91 | Existing 3 Rising Powers sub-tabs intact | cards/nextchina/migration panels unchanged | PASS |
| 92 | Drill-down modal intact | #rp-modal inside template literal | PASS |
| 93 | Auto-refresh 8min intact | `_rpRefreshTimer` unchanged | PASS |
| 94 | World Map 56+ markers intact | `initMap` unchanged | PASS |
| 95 | Risk/GDP%/Inflation layers intact | Original 3 modes unchanged | PASS |
| 96 | Map search + region filter intact | filterMapSearch/filterMapRegion unchanged | PASS |
| 97 | Future Geopolitics panel intact | `#map-future-panel` + `toggleFuturePanel` | PASS |
| 98 | News parallel fetch intact | `loadNewsTab` unchanged | PASS |
| 99 | Markets 5 tabs intact | `initMarkets` unchanged | PASS |
| 100 | JS syntax clean | `new Function(jsBlock)` → OK | PASS |
| 101 | File ends `</html>` | No truncation | PASS |
| 102 | File size: 466KB (up from 417KB) | Content added, nothing lost | PASS |
| 103 | Version badge shows v3.16 | `<span class="badge">v3.16</span>` | PASS |
| 104 | version.py shows 3.16.0 | `APP_VERSION = "3.16.0"` | PASS |

---

## Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| Passport Power Sub-tab | 19 | 19 | 0 |
| Language Future Sub-tab | 14 | 14 | 0 |
| New Nations Sub-tab | 16 | 16 | 0 |
| Sub-tab System | 7 | 7 | 0 |
| Population Layer | 14 | 14 | 0 |
| Alliance Layer | 20 | 20 | 0 |
| Regression | 14 | 14 | 0 |
| **TOTAL** | **104** | **104** | **0** |

**All 104 tests pass. Rising Powers now has 6 sub-tabs: Rising Powers cards, Next China, Future Migration, Passport Power (Henley Index + 2035 projections + investment citizenship), Language Future (8 post-English languages + AI impact), and New Nations (independence movements with probability scores). World Map has Population layer (WB live data) and 5 Alliance overlays (NATO/SCO/BRICS+/ASEAN/EU) as stackable rings. Zero paid APIs.**

---

## Architecture Notes

| Component | Details |
|-----------|---------|
| New sub-tabs | `#rp-panel-passport`, `#rp-panel-language`, `#rp-panel-newnations` inside `el.innerHTML` template |
| Passport live data | WB `ST.INT.ARVL` (tourism arrivals) — lazy on first tab open |
| Population live data | WB `SP.POP.TOTL` — lazy on first Pop layer click; 55-country static fallback |
| Alliance rings | `L.circleMarker` radius=base+6, fill:false, non-interactive, tooltip bound |
| Alliance state | `window._allianceActive{}` + `window._allianceCircles{}` per alliance key |
| Paid APIs | None — all World Bank public endpoints, no key |

*— Muhammad Umer Lari, World Intelligence Platform v3.16*
