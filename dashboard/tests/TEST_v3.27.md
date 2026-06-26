# Test Report — Markets & World Stocks AI Intelligence Layer v3.27
**World Intelligence Platform v3.27**
**Author: Muhammad Umer Lari | Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**
**Free LLM: MiniMax API · MiniMax-M2.7 · 100% free · Zero paid APIs**

---

## What Changed in v3.27

| # | Change | Detail |
|---|--------|--------|
| 1 | **🤖 AI Market Pulse** | Cross-asset macro regime analysis — all 5 categories in one brief |
| 2 | **🔄 AI Sector Rotation Model** | Category-level allocation signals (overweight/underweight/neutral) |
| 3 | **🤖 AI Asset Analysis** | Per-asset deep dive in every drilldown panel (Metals/Crypto/FX/Oil/Indices) |
| 4 | **🤖 AI Global Equity Outlook** | 28-exchange regime analysis — breadth, opportunities, risks |
| 5 | **🌱 EM Opportunity Scanner** | Emerging market screener — top picks, red flags, EM macro theme |
| 6 | **🤖 AI Exchange Analysis** | Per-exchange deep dive in every exchange drilldown (28 markets) |
| 7 | **All AI reads live data** | Prompts include real RSI, change%, price, signal from mktData[] |
| 8 | **Zero paid APIs** | MiniMax M2.7 100% free · same _groqCall() infrastructure from v3.26 |

---

## Phase MK — Markets Tab AI

| # | Test | Expected | Result |
|---|------|----------|--------|
| 1 | `id="ai-mkt-pulse-panel"` in Markets HTML | Panel container above sub-tabs | PASS |
| 2 | `🤖 AI Market Pulse` button present | `onclick="_mmMarketPulse()"` | PASS |
| 3 | `🔄 Sector Rotation` button present | `onclick="_mmSectorRotation()"` | PASS |
| 4 | Setup key hint link in Markets header | `onclick="_showAISetup()"` | PASS |
| 5 | `ai-asset-${a.sym}` panel in makeCard drilldown | Per-asset AI panel | PASS |
| 6 | `🤖 AI Asset Analysis` button in makeCard | `onclick="_mmAssetAI('${a.sym}')"` | PASS |
| 7 | `_mmMarketPulse()` defined | Async function | PASS |
| 8 | `_mmSectorRotation()` defined | Async function | PASS |
| 9 | `_mmAssetAI(sym)` defined | Async function | PASS |

---

## Phase MP — AI Market Pulse Logic

| # | Test | Expected | Result |
|---|------|----------|--------|
| 10 | Collects data from all 5 categories | ADEFS['metals/crypto/fx/oil/indices'] loop | PASS |
| 11 | Snapshot includes name, price, change%, RSI, signal | 5 fields per asset | PASS |
| 12 | Guard: empty snapshots shows graceful message | No crash on cold load | PASS |
| 13 | Prompt requests 3 paragraphs + REGIME label | Cross-asset · Standout · Outlook | PASS |
| 14 | max_tokens = 550 | Sufficient for 200-word brief | PASS |
| 15 | Result shows signal count in attribution | `N signals` in panel header | PASS |
| 16 | Refresh link re-runs analysis | `onclick="_mmMarketPulse()"` | PASS |
| 17 | NO_KEY guard active | `_aiNoKey(panel)` called | PASS |

---

## Phase SR — AI Sector Rotation Logic

| # | Test | Expected | Result |
|---|------|----------|--------|
| 18 | Computes avgRSI per category | Reduces ADEFS[cat] RSI values | PASS |
| 19 | Computes avgChg per category | Reduces ADEFS[cat] change values | PASS |
| 20 | Computes bullPct per category | % of assets with positive change | PASS |
| 21 | Prompt requests OVERWEIGHT/UNDERWEIGHT/NEUTRAL lines | 3-line allocation output | PASS |
| 22 | Ends with ROTATION SIGNAL label | [DEFENSIVE SHIFT / RISK ROTATION / STAY POSITIONED] | PASS |
| 23 | Uses same `ai-mkt-pulse-panel` as Market Pulse | Shared panel, different content | PASS |
| 24 | max_tokens = 380 | Sufficient for rotation brief | PASS |

---

## Phase AA — AI Asset Analysis Logic

| # | Test | Expected | Result |
|---|------|----------|--------|
| 25 | Finds asset definition across all 5 categories | ADEFS loop with `.find()` | PASS |
| 26 | Reads live price, change, RSI, signal from mktData | Real data in prompt | PASS |
| 27 | Computes 20D volatility from price history | `Math.sqrt(variance)/price` | PASS |
| 28 | Prompt: Technical + Macro + Trade Setup paragraphs | 3-paragraph structure | PASS |
| 29 | Prompt ends with SIGNAL + 30D TARGET labels | Structured output | PASS |
| 30 | `window._aiLastSym=sym` set for Regenerate | Safe onclick reference | PASS |
| 31 | Buttons disabled during call, re-enabled in finally | `btns.forEach(b=>b.disabled=true/false)` | PASS |
| 32 | max_tokens = 420 | Sufficient for 160-word brief | PASS |

---

## Phase SK — World Stocks Tab AI

| # | Test | Expected | Result |
|---|------|----------|--------|
| 33 | `id="ai-stocks-panel"` in Stocks HTML | Panel below title, above region tabs | PASS |
| 34 | `🤖 AI Global Equity Outlook` button present | `onclick="_mmStockOutlook()"` | PASS |
| 35 | `🌱 EM Opportunity Scanner` button present | `onclick="_mmEmergingScanner()"` | PASS |
| 36 | Setup key hint in Stocks header | `onclick="_showAISetup()"` | PASS |
| 37 | `ai-exch-${e.sym}` panel in makeExchCard drilldown | Per-exchange AI panel | PASS |
| 38 | `🤖 AI Exchange Analysis` button in makeExchCard | `onclick="_mmExchangeAI('${e.sym}')"` | PASS |
| 39 | `_mmStockOutlook()` defined | Async function | PASS |
| 40 | `_mmEmergingScanner()` defined | Async function | PASS |
| 41 | `_mmExchangeAI(sym)` defined | Async function | PASS |

---

## Phase SO — AI Global Equity Outlook Logic

| # | Test | Expected | Result |
|---|------|----------|--------|
| 42 | Maps all 28 EXCHANGES with live data | change%, RSI, signal, MC | PASS |
| 43 | Computes bullCount (positive change) and breadth% | `EXCHANGES.filter(e=>change>0).length` | PASS |
| 44 | Breadth% included in prompt | `bullCount+'/28 (N% breadth)'` | PASS |
| 45 | Prompt: GLOBAL REGIME + TOP 3 OPPORTUNITIES + KEY RISKS | 3-paragraph structure | PASS |
| 46 | Ends with GLOBAL EQUITY BIAS label | [BULLISH / BEARISH / NEUTRAL] | PASS |
| 47 | Breadth shown in result panel header | `28 exchanges · N/28 bullish` | PASS |
| 48 | max_tokens = 560 | Sufficient for 200-word regime brief | PASS |

---

## Phase EM — AI Emerging Market Scanner Logic

| # | Test | Expected | Result |
|---|------|----------|--------|
| 49 | Filters EXCHANGES for reg='mea' OR reg='asia' | EM subset only | PASS |
| 50 | Includes 2030 targets in EM data | `2030:e.yr2030` | PASS |
| 51 | Also flags global weakening markets (change < -1%) | Cross-market weak signal context | PASS |
| 52 | Prompt: TOP 3 PICKS + RED FLAGS + EM MACRO THEME | 3-section structure | PASS |
| 53 | Ends with EM POSTURE + single top pick | [ACCUMULATE / HOLD / REDUCE] | PASS |
| 54 | EM exchange count in result panel header | `N EM exchanges` | PASS |
| 55 | Uses same `ai-stocks-panel` as Equity Outlook | Shared panel, different content | PASS |
| 56 | max_tokens = 460 | Sufficient for 170-word EM brief | PASS |

---

## Phase EA — AI Exchange Analysis Logic

| # | Test | Expected | Result |
|---|------|----------|--------|
| 57 | Finds exchange in EXCHANGES[] by sym | `.find(x=>x.sym===sym)` | PASS |
| 58 | Reads live price, change, RSI, signal | Real mktData in prompt | PASS |
| 59 | Includes MC, 2030/2035/2040 targets in prompt | Long-run context | PASS |
| 60 | Prompt: Technical + Country/Macro + Investment Case | 3-paragraph structure | PASS |
| 61 | Ends with OUTLOOK + 12M Bias + Key risk | Structured output | PASS |
| 62 | `window._aiLastExch=sym` set for Regenerate | Safe onclick reference | PASS |
| 63 | Buttons disabled during call, re-enabled in finally | Error-safe UI state | PASS |
| 64 | max_tokens = 440 | Sufficient for 170-word analysis | PASS |

---

## Phase REG — Regression Tests

| # | Test | Expected | Result |
|---|------|----------|--------|
| 65 | All v3.26 MiniMax AI features intact | Country/News/Deforestation/Forecast AI all present | PASS |
| 66 | `_groqCall()` function intact | Markets+Stocks AI reuses same infrastructure | PASS |
| 67 | `wip_minimax_key` localStorage intact | v3.26 key name unchanged | PASS |
| 68 | All v3.25 AI CSS intact | `.ai-panel`, `.ai-btn`, `.ai-panel-hdr`, `.ai-result` | PASS |
| 69 | makeCard() renders correctly | drilldown still opens, AI panel added | PASS |
| 70 | makeExchCard() renders correctly | drilldown still opens, AI panel added | PASS |
| 71 | `wip_rp_subtab` localStorage intact | 2 occurrences | PASS |
| 72 | Forecast tab (v3.19) intact | fcChart, switchFcAsset, Monte Carlo | PASS |
| 73 | `node --check` passed | ✅ SYNTAX CLEAN (JS: 461KB) | PASS |
| 74 | File ends `</html>` | No truncation | PASS |
| 75 | File size ~640KB | +15.5KB from AI layer | PASS |
| 76 | Version title = v3.27 | `<title>World Intelligence Platform v3.27</title>` | PASS |
| 77 | Version badge = v3.27 | `<span class="badge">v3.27</span>` | PASS |
| 78 | `version.py` = 3.27.0 | `APP_VERSION = "3.27.0"` | PASS |
| 79 | Zero paid APIs | MiniMax M2.7 free tier only | PASS |

---

## Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| Markets Tab AI (HTML) | 9 | 9 | 0 |
| AI Market Pulse Logic | 8 | 8 | 0 |
| AI Sector Rotation Logic | 7 | 7 | 0 |
| AI Asset Analysis Logic | 8 | 8 | 0 |
| World Stocks Tab AI (HTML) | 9 | 9 | 0 |
| AI Global Equity Outlook | 7 | 7 | 0 |
| AI EM Scanner Logic | 8 | 8 | 0 |
| AI Exchange Analysis Logic | 8 | 8 | 0 |
| Regression | 15 | 15 | 0 |
| **TOTAL** | **79** | **79** | **0** |

**All 79 tests pass. v3.27 adds 6 AI intelligence features across the Markets and World Stocks tabs — all powered by MiniMax M2.7 (100% free). AI Market Pulse analyses cross-asset signals from all 5 market categories. Sector Rotation Model provides category-level allocation signals. AI Asset Analysis gives per-asset technical + macro deep dives in every drilldown. AI Global Equity Outlook scans all 28 exchanges for regime analysis including breadth metrics. EM Opportunity Scanner screens emerging markets for top picks and red flags. AI Exchange Analysis provides per-exchange country + technical + long-run investment assessments. All 6 features read live RSI, price, change%, and signal data from the dashboard's own mktData[] object, so the AI analyses are grounded in real numbers. Zero paid APIs.**

---

## AI Feature Map

| Feature | Trigger | Panel | Scope |
|---------|---------|-------|-------|
| AI Market Pulse | `🤖 AI Market Pulse` button | `ai-mkt-pulse-panel` | All 5 categories, 25+ assets |
| Sector Rotation | `🔄 Sector Rotation` button | `ai-mkt-pulse-panel` | 5 categories (avg RSI/change) |
| AI Asset Analysis | `🤖 AI Asset Analysis` in drilldown | `ai-asset-{sym}` | Single asset |
| AI Global Equity Outlook | `🤖 AI Global Equity Outlook` button | `ai-stocks-panel` | All 28 exchanges |
| EM Opportunity Scanner | `🌱 EM Opportunity Scanner` button | `ai-stocks-panel` | MEA + Asia exchanges |
| AI Exchange Analysis | `🤖 AI Exchange Analysis` in drilldown | `ai-exch-{sym}` | Single exchange |

---

## Setup

The same MiniMax key from v3.26 unlocks all 6 new AI features. Click **🤖 AI** in the header to enter your key from **platform.minimaxi.com** (free, no credit card).

*— Muhammad Umer Lari, World Intelligence Platform v3.27*
