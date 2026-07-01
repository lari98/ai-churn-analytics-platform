# 🌐 World Intelligence Platform v3.37

### Real-Time · AI-Augmented · Multi-Source Global Intelligence System
### 12 Modules · 22 LLM Features · Serverless SPA · Zero Paid APIs · 27 Verified Sources

**Author: Muhammad Umer Lari © 2024–2025 · All Rights Reserved**

> **Tech Stack:** `Vanilla JS` `HTML5` `CSS3` `Chart.js` `Leaflet.js` `MiniMax M2.7 LLM` `REST API Orchestration` `RSS Data Pipelines` `Event-Driven Polling` `Multi-Source Data Fusion` `OSINT Aggregation` `Geospatial Risk Modelling` `Predictive Macro Analytics` `Cross-Asset Intelligence` `Zero-Backend Architecture`

[![Dashboard](https://img.shields.io/badge/Dashboard-v3.37-a78bfa)](./dashboard/world-intelligence.html)
[![AI Features](https://img.shields.io/badge/AI_Features-22-f59e0b)](./dashboard/tests/)
[![MiniMax](https://img.shields.io/badge/LLM-MiniMax_M2.7-10b981)](https://platform.minimaxi.com)
[![Free APIs](https://img.shields.io/badge/Paid_APIs-Zero-22c55e)]()
[![Tests](https://img.shields.io/badge/Tests-308_passed-22c55e)](./dashboard/tests/)
[![AQI Cities](https://img.shields.io/badge/AQI_Cities-500+-38bdf8)]()
[![Exchanges](https://img.shields.io/badge/World_Exchanges-28-818cf8)]()
[![Rising Powers](https://img.shields.io/badge/Rising_Powers-15_Nations-f97316)]()
[![G10 Countries](https://img.shields.io/badge/G10_Countries-10-60a5fa)]()
[![Data Sources](https://img.shields.io/badge/Data_Sources-27_Verified-22c55e)]()
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-green)](./GDPR.md)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)

---

![World Intelligence Platform Banner](./screenshots/banner.png)

---

## 🖼 Platform Screenshots

> **Real screenshots from the live running dashboard · v3.37 · Muhammad Umer Lari**

| 🗺 World Map — Countries & Geopolitical Layers | 📈 Markets — Live Crypto, Forex & Commodities |
|:---:|:---:|
| ![World Map](./screenshots/world-map.png) | ![Markets](./screenshots/markets.png) |

| 🚀 Rising Powers — 15 Nations + 9 AI Features | 🌐 World Stocks — 28 Exchanges + AI Outlook |
|:---:|:---:|
| ![Rising Powers](./screenshots/rising-powers.png) | ![World Stocks](./screenshots/stocks.png) |

| 🌿 Environment — AQI 500+ Cities + Deforestation | 📊 Forecast — Monte Carlo + AI Explanation |
|:---:|:---:|
| ![Environment](./screenshots/environment.png) | ![Forecast](./screenshots/forecast.png) |

| 🏦 Central Banks — 35 Banks + ECB Live | ⚔️ Crisis Map + 📉 Recession Intelligence |
|:---:|:---:|
| ![Central Banks](./screenshots/centralbanks.png) | ![Crisis & Recession](./screenshots/crisis.png) |

| 📰 News — 8 Regional Feeds + Auto-Refresh | 🌡 Climate Intelligence — Historical + AI |
|:---:|:---:|
| ![News](./screenshots/news.png) | ![Climate](./screenshots/climate-intelligence.png) |

---

## 📋 Table of Contents

- [Overview](#-overview)
- [What's New v3.37](#-whats-new--v337)
- [All 12 Tabs](#-all-12-tabs)
- [22 AI Features](#-22-ai-features--minimax-m27)
- [Project Architecture](#️-project-architecture)
- [Database Architecture](#-database-architecture)
- [Install on Windows · macOS · Linux](#-installation)
- [Testing](#-testing)
- [Data Sources](#-data-sources--verification)
- [Project Sprints](#-project-sprints)
- [Version History](#-version-history)
- [Professional Use Cases](#-professional-use-cases)
- [Security & GDPR](#️-security--gdpr)

---

## 🎯 Overview

**World Intelligence Platform** is a **serverless, AI-augmented, real-time global intelligence system** built by **Muhammad Umer Lari**. It delivers multi-source data fusion across macroeconomics, geopolitical risk, recession intelligence, forex markets, ESG data, and predictive analytics — powered by LLM inference on demand — in a single zero-dependency deployment artifact.

Used by analysts, macro strategists, country risk advisors, ESG researchers, forex traders, and consulting teams who need structured, source-cited global intelligence without $24,000/yr data terminal subscriptions. Every figure is traceable to a primary free source (IMF · BIS · OECD · Fed · World Bank) via clickable citations embedded directly in the dashboard.

> 📄 **Professional Use Cases:** See [`PLATFORM_EXECUTIVE_BRIEF.html`](./PLATFORM_EXECUTIVE_BRIEF.html) — where this platform is deployed, how it helps firms, and which consulting firms gain strategic advantage.

| Metric | Value |
|--------|-------|
| Intelligence tabs | 12 |
| AI features (MiniMax M2.7) | 22 |
| AQI monitored cities | 500+ |
| World stock exchanges | 28 |
| Rising power nations | 15 |
| G10 countries deep-dive | 10 |
| Central banks tracked | 35 |
| Active crisis zones | 25 |
| Verified data sources | 27 |
| Paid APIs | **Zero** |
| File size | ~773 KB (single HTML) |

---

## 🆕 What's New — v3.37

### 🌐 G10 & World Impact Sub-Tab (v3.36–v3.37)
New 4th sub-tab inside Recession Intelligence covering every G10 economy:

- **10 G10 Country Cards** — USA, Japan, Germany, UK, France, Canada, Italy, Sweden, Switzerland, Eurozone. Each card shows recession status (IN RECESSION / AT RISK / MONITORING / STABLE), GDP impact %, unemployment, debt/GDP, policy response, and green recovery signals
- **Country Drill-Down Modal** — click any card for full deep-dive: policy response, pressure points, forex impact, green signals, and Chart.js time series (2008 · 2020 · 2025 forecast)
- **Developed vs. Developing Comparison** — 8 dimensions: fiscal capacity, currency shock, policy tools, banking system, trade impact, recovery speed, social impact, debt risk
- **G10 GDP Time Series Chart** — 17-quarter trajectory across 3 recession episodes
- **Forex & Safe Haven Analysis** — 10 pairs: USD/DXY +8.2%, JPY +12%, CHF +6%, Gold +22%, GBP -12%, EUR -8%, EM FX -25%, BTC -65%
- **Traders Intelligence** — 4 strategy cards: Long setups, Short setups, Forex pairs, Options (each rated STRONG / MODERATE / WATCH)
- **Live hourly news** via Google News RSS with 4 rotating queries and fallback headlines
- **28 verified source links** in footer (IMF, BIS, OECD, Fed, ECB, BOJ, World Gold Council…)

### 📚 Source Footer v3.35
27 clickable source links in 4 columns across all Recession sub-tabs — every figure traceable to IMF, World Bank, BIS, OECD, FRED, NBER.

### 📉 Recession Intelligence v3.34
6 new builder functions: sector rotation (14 sectors), recovery timeline (7 ranks), end signals (8 cards), country recovery tiers (4 tiers, 22 countries), future type cards (4 scenarios), unfold timeline (6 phases).

---

## 🗂 All 12 Tabs

### 🗺 1. World Map
- 37+ countries on Leaflet.js dark map
- Layer switcher: Risk · GDP · Inflation · Alliance · Population
- World Bank live GDP per country marker
- Future Geopolitics sub-tab (2035 projections)
- Country search, region filters, top movers panel

### 📈 2. Markets
- 5 asset categories: Metals · Crypto · Forex · Oil · Indices
- Live: CoinGecko (crypto) · Frankfurter/ECB (FX) · Yahoo Finance proxy (metals/oil/indices)
- RSI, price change%, signal badge per asset
- **AI**: 🤖 AI Market Pulse · 🔄 Sector Rotation Model · 🤖 AI Asset Analysis (per drilldown)

### 🌐 3. World Stocks
- 28 global exchanges: NYSE · LSE · TSE · BSE · SSE · HKEx · Tadawul · NSE and more
- Live price, change%, RSI, signal per exchange
- Regional tabs: Americas · Europe · Asia · MEA
- **AI**: 🤖 AI Global Equity Outlook · 🌱 EM Opportunity Scanner · 🤖 AI Exchange Analysis

### 🚀 4. Rising Powers
**15 nations**: India · China · Indonesia · Brazil · Vietnam · Mexico · Bangladesh · Ethiopia · Egypt · Nigeria · Pakistan · Turkey · Saudi Arabia · UAE · Kazakhstan

**7 sub-tabs with AI:**

| Sub-tab | Data | AI Feature |
|---------|------|-----------|
| Cards | GDP growth · Inflation · Momentum | 🔮 Global Power Oracle + 🏁 Power Race Predictor 2035 |
| Next China | 6 manufacturing candidates | 🏭 AI: Who Replaces China? |
| Migration | Flow data · Climate displacement | ✈️ AI Migration Forecast 2035–2050 |
| Passport | Henley index · Visa-free access | 🛂 AI Passport Strategy 2030 |
| Language | Speaker data · Economic weight | 🗣 AI Language Shift Forecast 2040 |
| New Nations | 8 independence movements | 🌐 AI New Nations Probability |
| Currencies | CBDC · De-dollarization | 💱 AI De-Dollarization Forecast |

### 📰 5. News
- 8 regional feeds: World · Middle East · Asia · Europe · Americas · Africa · Technology · Business
- Google News RSS + multi-source parallel fetch
- Auto-refresh every 90 seconds with live indicator
- **AI**: 📰 AI News Brief

### 📊 6. Forecast
- Monte Carlo simulation (500 paths, σ×√t volatility)
- 6 assets: Gold · BTC · Oil · EUR/USD · S&P 500 · DXY
- 90-second auto-refresh, confidence bands
- **AI**: 📊 AI Forecast Explanation

### 📡 7. Signals
- Multi-asset signal dashboard (RSI · momentum · trend)

### 🌡 8. Climate
- Historical temperature data by region
- Past / Present / Future sub-tabs

### 👶 9. Birth Rate
- Global birth rate trends with era timeline and country filter

### 🌿 10. Environment
- **500+ AQI cities** with health advisories (General · Sensitive · Children · Elderly)
- Deforestation tracker — GFW/Hansen/UMD satellite data
- Top 10 deforestation hotspots
- OpenAQ live PM2.5 overlay
- **AI**: 🌿 AI Deforestation Risk Narrative

### 🏦 11. Central Banks
- **35 central banks** worldwide
- ECB live rate (data.ecb.europa.eu, free API)
- US Treasury yield curve (FRED CSV backup)
- Taylor Rule AI Predictor · Rate Cycle Tracker · Policy Divergence Chart · Balance Sheet Tracker

### ⚔️ 12. Crisis Map + Recession Intelligence
- **25 active crisis zones** — armed · civil · protest · humanitarian
- Leaflet dark map, crisis filter bar
- ACLED · UNHCR · UCDP · ReliefWeb data (all free)

**Recession sub-tabs (4):**
- 📜 Historical Atlas — 6 recession eras 1929–2024, 30+ countries
- 🚨 Warning Lights — G20 risk table, sector rotation, live radar
- 🔮 Coming Storm — Forecast 2025–2040, 4 macro scenarios
- 🌐 G10 & World Impact — 10 country deep-dives, forex, trader playbooks *(v3.36)*

---

## 🤖 22 AI Features — MiniMax M2.7

> All features use **MiniMax M2.7** — 100% free, no credit card required.
> One key at **platform.minimaxi.com** unlocks all 22 features.

| # | Feature | Tab |
|---|---------|-----|
| 1 | 🤖 AI Country Assessment | Rising Powers → Drilldown |
| 2 | 🔮 AI Future Predictor (base/bull/bear) | Rising Powers → Drilldown |
| 3 | 🔮 Global Power Oracle (15 nations) | Rising Powers → Cards |
| 4 | 🏁 Power Race Predictor 2035 | Rising Powers → Cards |
| 5 | 🏭 AI: Who Replaces China? | Rising Powers → Next China |
| 6 | ✈️ AI Migration Forecast 2035–2050 | Rising Powers → Migration |
| 7 | 🛂 AI Passport Strategy 2030 | Rising Powers → Passport |
| 8 | 🗣 AI Language Shift Forecast 2040 | Rising Powers → Language |
| 9 | 🌐 AI New Nations Probability | Rising Powers → New Nations |
| 10 | 💱 AI De-Dollarization Forecast | Rising Powers → Currencies |
| 11 | 🤖 AI Market Pulse (cross-asset) | Markets |
| 12 | 🔄 Sector Rotation Model | Markets |
| 13 | 🤖 AI Asset Analysis | Markets → Drilldown |
| 14 | 🤖 AI Global Equity Outlook | World Stocks |
| 15 | 🌱 EM Opportunity Scanner | World Stocks |
| 16 | 🤖 AI Exchange Analysis | World Stocks → Drilldown |
| 17 | 📰 AI News Brief | News |
| 18 | 🌿 AI Deforestation Risk Narrative | Environment |
| 19 | 📊 AI Forecast Explanation | Forecast |
| 20 | 📉 AI Recession Analysis | Recession → Historical |
| 21 | 🚨 AI Current Recession Radar | Recession → Warning Lights |
| 22 | 🌐 AI G10 & World Impact Forecast | Recession → G10 World |

**AI Setup:** Click **🤖 AI** in the top-right header → paste key → Save. Every result panel shows `© Muhammad Umer Lari`.

---

## 🏗️ Project Architecture

```
ai-churn-analytics-platform/
│
├── dashboard/
│   └── world-intelligence.html        # Single-file dashboard (~773 KB · v3.37)
│                                       # Contains: all HTML + CSS + JS + data
│                                       # No build step, no npm, no webpack
│
├── launcher/
│   ├── app.py                          # FastAPI backend (optional, enhanced data)
│   ├── version.py                      # APP_VERSION = "3.37.0"
│   └── requirements.txt
│
├── screenshots/                        # Real app screenshots (PNG)
│   ├── banner.png
│   ├── world-map.png
│   ├── markets.png
│   ├── rising-powers.png
│   ├── stocks.png
│   ├── environment.png
│   ├── forecast.png
│   ├── centralbanks.png
│   ├── crisis.png
│   ├── news.png
│   └── climate-intelligence.png
│
├── dashboard/tests/                    # All version test reports
│   ├── TEST_v3.37.md
│   ├── TEST_v3.36.md
│   ├── TEST_v3.35.md
│   ├── TEST_v3.34.md
│   ├── TEST_v3.31.md
│   ├── TEST_v3.28.md
│   ├── TEST_v3.27.md
│   └── TEST_v3.26.md
│
├── README.md                           # This file
├── LINKEDIN_CARD.png                   # LinkedIn post image
├── LINKEDIN_SHOWCASE.html              # LinkedIn portfolio page
├── LINKEDIN_POST_DE.md                 # LinkedIn post (German C1)
├── GDPR.md
└── CHANGELOG.md
```

### Frontend Architecture (single HTML file)

```
world-intelligence.html
│
├── <head>            CSS variables · dark theme · responsive grid
├── <body>
│   ├── #header       Logo · version badge · AI setup button
│   ├── #nav          12 tab buttons → showPage(id)
│   └── #pages        12 page divs (display:none → block on activate)
│       ├── #page-worldmap
│       ├── #page-markets
│       ├── #page-stocks
│       ├── #page-rising-powers
│       ├── #page-news
│       ├── #page-forecast
│       ├── #page-signals
│       ├── #page-climate
│       ├── #page-birthrate
│       ├── #page-environment
│       ├── #page-centralbanks
│       └── #page-crisis          ← Recession sub-tabs live here
│           ├── rec-historical
│           ├── rec-present
│           ├── rec-future
│           └── rec-g10world      ← NEW v3.36
│
└── <script>
    ├── Global state vars       (_recInited, _recMap, etc.)
    ├── Tab routing             showPage(), showRecTab()
    ├── API fetchers            recFetchNews(), g10FetchNews()
    ├── Builder functions       recBuildSectorRotation(), g10BuildCards()…
    ├── Chart builders          g10BuildCharts(), recBuildUnfoldTimeline()…
    ├── AI engine               recAI(), sendToMiniMax()
    └── Init guards             initRecession() guarded by _recInited 