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
    └── Init guards             initRecession() guarded by _recInited flag
```

---

## 🗄 Database Architecture

This project is **client-side only** — there is no traditional database. Data flows as follows:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER ARCHITECTURE                      │
├──────────────────┬──────────────────────────────────────────────┤
│  LIVE APIs       │  Source → Function → DOM element             │
│  (fetched on     │                                              │
│   page load)     │  CoinGecko → fetchCrypto() → #crypto-grid    │
│                  │  OpenAQ → fetchAQI() → #aqi-list             │
│                  │  Frankfurter → fetchFX() → #fx-grid          │
│                  │  Google News RSS → recFetchNews() → news feed │
│                  │  ECB → fetchECBRate() → #ecb-rate            │
├──────────────────┼──────────────────────────────────────────────┤
│  STATIC DATA     │  Embedded JS arrays (no external calls)      │
│  (in JS arrays)  │                                              │
│                  │  G10_COUNTRIES[10] — recession data          │
│                  │  G10_FOREX[10] — safe haven moves            │
│                  │  G10_TRADERS[4] — strategy cards             │
│                  │  REC_ERAS[] — 1929-2024 historical data      │
│                  │  SECTOR_ROT[] — 14 sector cards              │
│                  │  COUNTRIES_RISK[] — G20 risk scores          │
│                  │  RISING_POWERS[15] — nation intelligence     │
│                  │  CRISIS_ZONES[25] — geopolitical events      │
├──────────────────┼──────────────────────────────────────────────┤
│  BROWSER CACHE   │  MiniMax API key → localStorage['mmKey']     │
│  (localStorage)  │  Theme preference → localStorage['theme']    │
│                  │  Tab state → sessionStorage['activeTab']     │
├──────────────────┼──────────────────────────────────────────────┤
│  OPTIONAL        │  FastAPI backend (launcher/app.py)           │
│  BACKEND         │  Endpoints: /api/markets /api/aqi /api/fx    │
│                  │  SQLite for caching if backend enabled        │
│                  │  Default: NOT needed, dashboard works alone   │
└──────────────────┴──────────────────────────────────────────────┘
```

**Why no database?** The dashboard is designed to be zero-infrastructure. Every data point either comes from a free API on demand or is embedded as verified static data (cited to primary sources like IMF, BIS, World Bank). This means it runs anywhere — GitHub Pages, a USB stick, a laptop offline.

---

## 🚀 Installation

### ✅ Quickest (no install at all)
```bash
git clone https://github.com/lari98/ai-churn-analytics-platform.git
```
Then open `dashboard/world-intelligence.html` directly in your browser. Done.

---

### 🪟 Windows

```cmd
REM 1. Clone the repo
git clone https://github.com/lari98/ai-churn-analytics-platform.git
cd ai-churn-analytics-platform

REM 2. Open dashboard directly
start dashboard\world-intelligence.html

REM ── OR run with local server (recommended for live API data) ──
REM 3. Install Python if not present: https://python.org/downloads
python --version

REM 4. Start local server
python -m http.server 8765 --directory dashboard
REM Open: http://localhost:8765/world-intelligence.html

REM ── OR run full backend ──
pip install -r requirements.txt
python launcher\app.py
REM Opens: http://localhost:8111
```

**Unlock AI on Windows:**
1. Visit [platform.minimaxi.com](https://platform.minimaxi.com) → free account → API Keys → New Key
2. Click **🤖 AI** button (top-right of dashboard) → paste key → Save

---

### 🍎 macOS

```bash
# 1. Clone
git clone https://github.com/lari98/ai-churn-analytics-platform.git
cd ai-churn-analytics-platform

# 2. Open directly
open dashboard/world-intelligence.html

# ── OR with local server ──
# Python 3 is pre-installed on macOS 12+
python3 -m http.server 8765 --directory dashboard
# Open: http://localhost:8765/world-intelligence.html

# ── OR full backend ──
pip3 install -r requirements.txt
python3 launcher/app.py
# Opens: http://localhost:8111
```

**If Python not installed on macOS:**
```bash
# Install Homebrew first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
```

---

### 🐧 Linux (Ubuntu / Debian / Fedora)

```bash
# 1. Clone
git clone https://github.com/lari98/ai-churn-analytics-platform.git
cd ai-churn-analytics-platform

# 2. Open in browser
xdg-open dashboard/world-intelligence.html
# Or: firefox dashboard/world-intelligence.html
# Or: google-chrome dashboard/world-intelligence.html

# ── With local server ──
python3 -m http.server 8765 --directory dashboard
# Open: http://localhost:8765/world-intelligence.html

# ── Full backend (Ubuntu/Debian) ──
sudo apt update && sudo apt install python3 python3-pip -y
pip3 install -r requirements.txt
python3 launcher/app.py

# ── Full backend (Fedora/RHEL) ──
sudo dnf install python3 python3-pip -y
pip3 install -r requirements.txt
python3 launcher/app.py
```

---

### 🤖 Unlock AI (all platforms, free)

1. Go to **[platform.minimaxi.com](https://platform.minimaxi.com)** → create free account
2. Go to **API Keys** → click **Create new key** → copy key (starts `eyJ...`)
3. In the dashboard: click **🤖 AI** (top-right header)
4. Paste key → click **Save Key**
5. All 22 AI features are now active — no credit card, completely free

---

## 🧪 Testing

| Test File | Version | Tests | Result |
|-----------|---------|-------|--------|
| [TEST_v3.37.md](./TEST_v3.37.md) | v3.37 | 45 | ✅ All PASS |
| [TEST_v3.36.md](./TEST_v3.36.md) | v3.36 | 38 | ✅ All PASS |
| [TEST_v3.34.md](./TEST_v3.34.md) | v3.34 | 42 | ✅ All PASS |
| [TEST_v3.31.md](./dashboard/tests/TEST_v3.31.md) | v3.31 | 60 | ✅ All PASS |
| [TEST_v3.28.md](./dashboard/tests/TEST_v3.28.md) | v3.28 | 99 | ✅ All PASS |
| [TEST_v3.27.md](./dashboard/tests/TEST_v3.27.md) | v3.27 | 79 | ✅ All PASS |
| [TEST_v3.26.md](./dashboard/tests/TEST_v3.26.md) | v3.26 | 70 | ✅ All PASS |

**433+ tests across all versions — all passing.**

### What is tested in each version
- Version badge correct in DOM
- All JS builder functions defined
- All DOM container IDs present
- Data arrays populated (correct count)
- Sub-tab navigation works
- Drill-down modals open/close
- Chart canvases present
- News feed container exists
- AI button clickable
- File integrity (`</body></html>` present, no truncation)

---

## 📊 Data Sources & Verification

Every figure in this platform is traceable to a free, publicly accessible primary source. Source footers with clickable links appear in every major module.

| Category | Sources |
|----------|---------|
| **Recession & Macro** | IMF WEO · World Bank GDP · FRED (St. Louis Fed) · BIS Statistics · OECD Statistics · Conference Board LEI · NBER |
| **G10 Central Banks** | Federal Reserve · ECB · Bank of Japan · Bank of England · Bank of Canada · Swiss National Bank · Riksbank |
| **Forex & Markets** | BIS FX Triennial Survey · World Gold Council · FRED DXY · JPMorgan Research · Swiss Re Sigma · IMF GFSR |
| **Developing World** | IMF Regional Outlooks · World Bank Poverty Data · IIF Global Debt Monitor · UNCTAD |
| **Live Crypto** | CoinGecko API (free, no key) |
| **Live FX** | Frankfurter.app · ECB data.ecb.europa.eu (free) |
| **AQI Cities** | OpenAQ v3 API (free) |
| **Live News** | BBC RSS · Reuters RSS · Al Jazeera RSS · DW RSS · Google News RSS |
| **Crisis Zones** | ACLED · UNHCR · UCDP · ReliefWeb |
| **Climate** | NASA GISS · NOAA · IPCC reports |
| **Birth Rates** | UN World Population Prospects |
| **AI Engine** | MiniMax M2.7 (`api.minimaxi.chat`) — free with account |

---

## 🏃 Project Sprints

Full development history — from v1.0 to v3.37.

| Sprint | Version Range | Focus | Key Deliverables |
|--------|--------------|-------|-----------------|
| **Sprint 1** | v1.0 – v2.3 | Foundation | World map, basic markets tab, Rising Powers v1, Python FastAPI backend |
| **Sprint 2** | v2.4 – v2.6 | Data Depth | 37 countries, 35 exchanges, climate intelligence, birth rate tab |
| **Sprint 3** | v2.7 – v2.9 | Forecasting | Monte Carlo 500 paths, AI predictor engine, climate tipping points |
| **Sprint 4** | v3.0 – v3.1 | Birth Rate Advanced | Era timeline animation, country search, sparkline charts |
| **Sprint 5** | v3.4 – v3.9 | Environment | AQI 50 cities, OpenAQ integration, city comparison chart, rankings |
| **Sprint 6** | v3.9 – v3.13 | Bug Fixes & Performance | Tab persistence fix, white tile fix, AQI click, real market APIs, full audit |
| **Sprint 7** | v3.14 – v3.16 | Rising Powers Expansion | Next China sub-tab, Future Migration, Passport Power, New Nations, Language Future |
| **Sprint 8** | v3.16 – v3.17 | World Map Ultra | Alliance layer, population layer, geopolitical overlays, 5 new news tabs |
| **Sprint 9** | v3.17 – v3.20 | AI Layer v1 | Groq integration → MiniMax migration, 4 AI features, forecast explanation |
| **Sprint 10** | v3.20 – v3.24 | Rising Powers Intelligence | Power Vortex, GDP duel, momentum scoring, Currencies sub-tab, Deforestation |
| **Sprint 11** | v3.25 – v3.28 | AI Expansion | 22 AI features total, Markets AI, Stocks AI, Rising Powers Oracle, Power Race |
| **Sprint 12** | v3.29 – v3.31 | Recession Tab v1 | 3 sub-tabs (Historical Atlas, Current Radar, Future Forecast), country collapse panel |
| **Sprint 13** | v3.32 – v3.34 | Recession Advanced | Sector rotation (14), recovery timeline (7), end signals (8), country tiers (4), future scenarios |
| **Sprint 14** | v3.35 | Source Verification | 27 clickable source links in verified footer, live timestamp |
| **Sprint 15** | v3.36 – v3.37 | G10 & World Impact | 10 country cards, forex analysis, trader playbooks, dev vs developing, G10 source footer |

---

## 📈 Version History

| Version | Date | Highlights |
|---------|------|-----------|
| **v3.37** | Jul 2025 | G10 source footer (28 verified links) · Professional README · LinkedIn showcase |
| **v3.36** | Jul 2025 | G10 & World Impact sub-tab · 10 country cards · Forex panel · Trader playbooks · Time series charts |
| **v3.35** | Jul 2025 | 27 verified source links in footer · Live timestamp · Source credibility layer |
| **v3.34** | Jul 2025 | Sector rotation (14) · Recovery timeline (7) · End signals (8) · Country tiers (4) · Future scenarios |
| **v3.33** | Jun 2025 | DOM structural fix · CB-adv bleed fix · Sub-tab panel isolation |
| **v3.31** | Jun 2025 | Optimization −10.5 KB · Muhammad Umer Lari hardcoding in all 15 AI panels |
| **v3.30** | Jun 2025 | Recession Intelligence Tab — Historical Atlas · Current Radar · Future Forecast |
| **v3.28** | May 2025 | 9 Rising Powers AI features across all 7 sub-tabs |
| **v3.27** | May 2025 | 6 Markets + World Stocks AI features · Market Pulse · Sector Rotation |
| **v3.26** | May 2025 | Groq → MiniMax M2.7 migration · 100% free AI |
| **v3.25** | May 2025 | AI Intelligence Layer — 4 features live |
| **v3.24** | Apr 2025 | Deforestation accuracy + satellite data (GFW/Hansen/UMD) |
| **v3.23** | Apr 2025 | Deforestation sub-tab in Environment |
| **v3.22** | Apr 2025 | Future Currencies sub-tab in Rising Powers |
| **v3.20** | Apr 2025 | Rising Powers Intelligence Suite — Power Vortex · GDP duel |
| **v3.19** | Mar 2025 | Monte Carlo Forecast 500 paths · 90s auto-refresh |
| **v3.17** | Mar 2025 | 8 news tabs + sub-tab persistence fix |
| **v3.16** | Mar 2025 | 3 Rising Powers sub-tabs · World Map alliance/population layers |
| **v3.12** | Feb 2025 | World Map batched markers · Country search |
| **v3.9** | Feb 2025 | AQI Rankings + City Comparison |
| **v3.1** | Jan 2025 | Birth Rate Advanced — autoplay timeline |
| **v2.6** | Dec 2024 | Climate Intelligence + Birth Rate tabs |
| **v2.3** | Dec 2024 | Complete platform rewrite — World Intelligence branding |

---

## 💼 Professional Use Cases

### Investment Management & Trading Desks
Portfolio managers use the G10 Recession Radar and Forex panel to position ahead of central bank pivots. The STRONG/MODERATE/WATCH trader setup ratings replace hours of manual research.

### Macro Research & Strategy Teams
Analysts use the Historical Atlas and 2025–2040 Forecast scenarios to build country risk memos and sector rotation models. Every figure is source-cited and audit-ready.

### Management Consulting Firms
Consultants use Rising Powers and World Map modules to brief clients on geopolitical risk and supply chain exposure — replacing $24,000/yr Bloomberg subscriptions for qualitative briefings.

### Sovereign & Country Risk Advisory
Risk analysts use the G10 drill-down modals and Developed vs. Developing comparison to model contagion risk, debt sustainability, and currency crisis probability.

### ESG & Sustainability Research
The Environment module provides real-time AQI, deforestation rates, and climate data for ESG scoring and regulatory compliance reporting.

### Government & Policy Research
Recession Intelligence and Rising Powers modules provide structured, source-cited intelligence for policy briefings and budget stress-testing.

---

## 🛡️ Security & GDPR

- MiniMax API key stored in **browser localStorage only** — never in any file, never committed to Git
- Key transmitted only to `api.minimaxi.chat` — nowhere else
- All market data fetched client-side via free public APIs — no user PII transmitted
- **Private GitHub repository** — no public access without invitation
- Full GDPR compliance: [GDPR.md](./GDPR.md)

---

## 👤 Author

**Muhammad Umer Lari**
Business Intelligence & Global Analytics
📧 umerlari1998@gmail.com
🔗 [github.com/lari98](https://github.com/lari98)

---

*© 2024–2025 Muhammad Umer Lari · All Rights Reserved*
*World Intelligence Platform v3.37 · Free AI: MiniMax M2.7 · Zero paid APIs · Private repository*
*Unauthorised copying, modification, or distribution is strictly prohibited.*
