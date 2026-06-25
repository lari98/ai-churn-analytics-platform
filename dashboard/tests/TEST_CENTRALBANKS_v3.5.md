# Test Report — Central Banks Live Tab
**World Intelligence Platform v3.5**
**Author: Muhammad Umer Lari | Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**
**Free APIs used: ECB Data Portal (no key) · yfinance (already installed)**

---

## Phase A — Central Banks Live (v3.5)

### A1 — Navigation & Page Load

| # | Test | Expected | Result |
|---|------|----------|--------|
| 1 | `🏦 Central Banks` tab visible in nav bar | Tab appears after Environment | PASS |
| 2 | Click tab → page renders without errors | `#page-centralbanks` becomes active | PASS |
| 3 | No scroll lag or hidden content | Page scrolls smoothly | PASS |
| 4 | Version badge updated to v3.5 | Header shows `v3.5` | PASS |
| 5 | Tab only initialises once (pageInited guard) | `initCentralBanks()` called once | PASS |

### A2 — KPI Row

| # | Test | Expected | Result |
|---|------|----------|--------|
| 6  | Fed KPI shows 4.25% | Static value from embedded data | PASS |
| 7  | ECB KPI shows live dot animation | `cb-live-dot` pulsing green dot | PASS |
| 8  | ECB KPI updated from `/api/central-banks` live | Rate from ECB Data Portal API | PASS |
| 9  | BOE KPI shows 4.25% | May 2025 embedded value | PASS |
| 10 | BOJ KPI shows 0.50% | Jan 2025 hike reflected | PASS |
| 11 | G20 Average computed from 20 banks | `avg = sum/20` shown correctly | PASS |
| 12 | KPI cards have colour-coded top border | Fed=blue, ECB=amber, BOE=purple, BOJ=pink | PASS |
| 13 | Hover on KPI card lifts it (transform) | `translateY(-2px)` on hover | PASS |

### A3 — Rate Table (20 Banks)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 14 | 20 rows rendered in table | All 20 central banks listed | PASS |
| 15 | Flag emojis display correctly | Country flags shown | PASS |
| 16 | Rate values formatted to 2dp | e.g. `4.25%`, `42.50%` | PASS |
| 17 | Change badges colour-coded | Red=hike, Green=cut, Grey=hold | PASS |
| 18 | Trend icon correct (↑↓→) | BOJ=🔴↑, Fed=🟢↓, CBR=⬜→ | PASS |
| 19 | Advanced/Emerging badges correct | US/EU/UK=Advanced, India/China=Emerging | PASS |
| 20 | Since date shown for each bank | e.g. `Dec 2024`, `May 2025` | PASS |
| 21 | Source domain shown | e.g. `federalreserve.gov` | PASS |
| 22 | ECB row shows live dot | Pulsing indicator in bank name | PASS |
| 23 | ECB rate cell updated when API responds | Live rate replaces embedded fallback | PASS |
| 24 | Turkey (CBRT) shows 42.50% | Highest rate in table | PASS |
| 25 | Japan (BOJ) shows 0.50% | Lowest advanced-economy rate | PASS |
| 26 | Row hover highlights with subtle bg | `rgba(255,255,255,.03)` on hover | PASS |
| 27 | Table horizontally scrollable on small screens | `overflow-x:auto` wrapper | PASS |
| 28 | Source footer lists all 20 official CB sites | Complete attribution shown | PASS |

### A4 — Historical Rate Chart (2020–2025)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 29 | Chart renders with 6 coloured lines | Fed, ECB, BOE, BOJ, BOC, RBA | PASS |
| 30 | X-axis: 22 quarterly labels (20Q1→25Q2) | Correct time span | PASS |
| 31 | Fed line: low 2020-21, spike 2022-23, cuts 2024 | Correct rate cycle shape | PASS |
| 32 | ECB line: negative until mid-2022 then sharp rise | Accurate history | PASS |
| 33 | BOJ line flat near 0% until 2025 Q1 | Japan's zero-rate policy shown | PASS |
| 34 | Interactive tooltip on hover | Shows all 6 rates at that quarter | PASS |
| 35 | Legend shows all 6 banks with colour | Readable at 10px font | PASS |
| 36 | Existing chart destroyed on re-init | No duplicate chart instances | PASS |

### A5 — US Treasury Yield Curve (Live)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 37 | Chart shows `cb-live-dot` in heading | Pulsing green dot indicating live data | PASS |
| 38 | Empty chart renders first (no flicker) | `_buildYieldChart({})` called first | PASS |
| 39 | Backend `/api/central-banks` fetched on tab open | `fetch('/api/central-banks')` called | PASS |
| 40 | Yield curve populated with 3M, 2Y, 5Y, 10Y, 30Y | 5 data points drawn | PASS |
| 41 | Chart shows graceful "Unavailable" if backend offline | Label changes to indicate no data | PASS |
| 42 | Tooltips show yield% on hover | e.g. `Yield: 4.356%` | PASS |
| 43 | Line fills area below with green tint | `fill:true`, `rgba(52,211,153,.10)` | PASS |

### A6 — CBDC Tracker (16 countries)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 44 | 16 CBDC rows rendered | All entries shown | PASS |
| 45 | Bahamas Sand Dollar shows `Live` (green) badge | World's first CBDC highlighted | PASS |
| 46 | China Digital Yuan shows `Pilot` (amber) badge | Large-scale pilot noted | PASS |
| 47 | USA/EU/UK show `Research` (grey) badge | No launch committed | PASS |
| 48 | Stage and notes columns filled for all rows | Descriptive text visible | PASS |
| 49 | Year column shows `—` for countries not launched | Correct blank handling | PASS |
| 50 | Source footer shows BIS + Atlantic Council attribution | Dual source cited | PASS |

### A7 — Free API Verification

| # | Test | Expected | Result |
|---|------|----------|--------|
| 51 | ECB Data Portal URL accessible (no API key) | `data.ecb.europa.eu` returns 200 | PASS |
| 52 | No paid API keys used anywhere | Zero API keys in codebase | PASS |
| 53 | yfinance yields fetched via existing backend | No new paid dependencies | PASS |
| 54 | ECB API failure falls back gracefully to 2.25% | Embedded fallback value used | PASS |
| 55 | Backend offline → tab still usable with embedded data | No crash, embedded rates shown | PASS |

### A8 — Backend Endpoint

| # | Test | Expected | Result |
|---|------|----------|--------|
| 56 | `GET /api/central-banks` returns 200 | JSON with yield_curve + ecb_deposit_rate | PASS |
| 57 | `ecb_deposit_rate` field present | Numeric value from ECB API | PASS |
| 58 | `ecb_date` field present | ISO date string e.g. `2025-04` | PASS |
| 59 | `yield_curve.10y` populated via yfinance | 10-year Treasury yield as float | PASS |
| 60 | Endpoint handles ECB API timeout gracefully | Returns fallback value, no 500 error | PASS |

---

## Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| Navigation & Load | 5 | 5 | 0 |
| KPI Row | 8 | 8 | 0 |
| Rate Table | 15 | 15 | 0 |
| History Chart | 8 | 8 | 0 |
| Yield Curve | 7 | 7 | 0 |
| CBDC Tracker | 7 | 7 | 0 |
| Free API Verification | 5 | 5 | 0 |
| Backend Endpoint | 5 | 5 | 0 |
| **TOTAL** | **60** | **60** | **0** |

**All 60 tests pass. Zero paid APIs used.**

**Data sources (all free):**
- ECB Data Portal: `data.ecb.europa.eu` — live deposit rate, no API key
- Yahoo Finance via yfinance: US Treasury yields (^IRX ^FVX ^TNX ^TYX)
- Official central bank websites: 20 banks, rates verified May 2025
- BIS CBDC Tracker + Atlantic Council CBDC Tracker: 16 countries

*— Muhammad Umer Lari, World Intelligence Platform v3.5*
