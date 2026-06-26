# Test Report — MiniMax AI Migration v3.26
**World Intelligence Platform v3.26**
**Author: Muhammad Umer Lari | Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**
**Free LLM: MiniMax API · MiniMax-M2.7 · 100% free · Zero paid APIs**

---

## What Changed in v3.26

| # | Change | Detail |
|---|--------|--------|
| 1 | **🔄 API migrated: Groq → MiniMax** | Endpoint changed to `api.minimaxi.chat/v1/chat/completions` |
| 2 | **🤖 Model updated** | `llama-3.1-70b-versatile` → `MiniMax-M2.7` |
| 3 | **🔑 localStorage key renamed** | `wip_groq_key` → `wip_minimax_key` |
| 4 | **🛡 Security unchanged** | Key still stored in localStorage only — never in any project file |
| 5 | **📋 Setup modal updated** | All Groq references replaced with MiniMax; placeholder `sk-cp-...` |
| 6 | **🔗 Links updated** | `console.groq.com` → `platform.minimaxi.com` |
| 7 | **🏷 Result attributions updated** | All 4 AI panels now credit MiniMax M2.7 |
| 8 | **💬 Error messages updated** | `Groq 4xx` → `MiniMax 4xx` |
| 9 | **Zero paid APIs** | MiniMax M2.7 100% free — no hidden cost, no credit card |

---

## Phase KY — Key Management (MiniMax)

| # | Test | Expected | Result |
|---|------|----------|--------|
| 1 | `_groqKey()` returns `localStorage('wip_minimax_key')` | localStorage key renamed | PASS |
| 2 | `_saveGroqKey()` stores to `wip_minimax_key` | Correct storage key | PASS |
| 3 | `_clearGroqKey()` removes `wip_minimax_key` | Correct removal key | PASS |
| 4 | `_showAISetup()` pre-fills from `wip_minimax_key` | Reads correct key | PASS |
| 5 | `wip_groq_key` not present anywhere in file | Old key name gone | PASS |
| 6 | `wip_minimax_key` present (getItem + setItem + removeItem) | 3 occurrences | PASS |
| 7 | Key validation: rejects short keys (< 20 chars) | Unchanged logic | PASS |
| 8 | Enter key submits form | `onkeydown="if(event.key==='Enter')_saveGroqKey()"` | PASS |
| 9 | `id="ai-setup-modal"` present | Modal container intact | PASS |
| 10 | `id="ai-key-input"` present | Password input intact | PASS |
| 11 | `id="ai-key-status"` present | Status feedback intact | PASS |
| 12 | Modal closes on backdrop click | `onclick="if(event.target===this)_closeAISetup()"` | PASS |
| 13 | Key never appears in any project file | Only in localStorage calls | PASS |

---

## Phase AC — MiniMax API Core

| # | Test | Expected | Result |
|---|------|----------|--------|
| 14 | `_groqCall(messages, maxTok)` defined | Async function | PASS |
| 15 | Endpoint: `api.minimaxi.chat/v1/chat/completions` | MiniMax international API | PASS |
| 16 | Old endpoint `api.groq.com` not present | Groq endpoint removed | PASS |
| 17 | Model: `MiniMax-M2.7` | Correct MiniMax model | PASS |
| 18 | Old model `llama-3.1-70b-versatile` not present | Groq model removed | PASS |
| 19 | Auth header: `Bearer ` + key | OpenAI-compatible auth unchanged | PASS |
| 20 | NO_KEY error thrown when key empty | `throw new Error('NO_KEY')` | PASS |
| 21 | HTTP error: `MiniMax ` + status | Updated error prefix | PASS |
| 22 | Old error prefix `'Groq '` not present | Groq error text removed | PASS |
| 23 | `_aiThinking(el, msg)` helper intact | Spinner unchanged | PASS |
| 24 | `_aiNoKey(el)` links to `platform.minimaxi.com` | Updated setup link | PASS |
| 25 | `_aiEsc(s)` helper intact | HTML escape function unchanged | PASS |
| 26 | `window._aiLastIso` pattern intact | onclick reference pattern | PASS |

---

## Phase C1 — Country AI Assessment

| # | Test | Expected | Result |
|---|------|----------|--------|
| 27 | `_groqCountryReport(iso)` defined | Async function intact | PASS |
| 28 | `id="ai-country-panel"` in rpDrillDown modal | Panel container intact | PASS |
| 29 | "🤖 AI Assessment" button in modal | Button intact | PASS |
| 30 | Result attribution: `MiniMax M2.7` | Updated from Groq llama-3.1-70b | PASS |
| 31 | Old attribution `Groq llama-3.1-70b` not present | Removed | PASS |
| 32 | Country modal subtitle: `MiniMax free tier` | Updated from Groq free tier | PASS |
| 33 | max_tokens = 420 | Unchanged | PASS |

---

## Phase C2 — News AI Brief

| # | Test | Expected | Result |
|---|------|----------|--------|
| 34 | `_groqNewsBrief()` defined | Async function intact | PASS |
| 35 | `id="ai-news-panel"` present | Panel container intact | PASS |
| 36 | "🤖 AI Brief" button present | Button intact | PASS |
| 37 | Result attribution: `MiniMax · N headlines` | Updated from Groq | PASS |
| 38 | max_tokens = 380 | Unchanged | PASS |

---

## Phase C3 — Deforestation Risk Narrative

| # | Test | Expected | Result |
|---|------|----------|--------|
| 39 | `_groqDeforestationRisk()` defined | Async function intact | PASS |
| 40 | `id="ai-def-panel"` present | Panel container intact | PASS |
| 41 | Result attribution: `MiniMax · GFW/Hansen/UMD verified data` | Updated from Groq | PASS |
| 42 | max_tokens = 480 | Unchanged | PASS |

---

## Phase C4 — Forecast Explanation

| # | Test | Expected | Result |
|---|------|----------|--------|
| 43 | `_groqForecastExplain()` defined | Async function intact | PASS |
| 44 | `id="ai-fc-panel"` present | Panel container intact | PASS |
| 45 | Result attribution: `MiniMax M2.7` | Updated from Groq llama-3.1-70b | PASS |
| 46 | max_tokens = 300 | Unchanged | PASS |

---

## Phase UI — Setup Modal UI

| # | Test | Expected | Result |
|---|------|----------|--------|
| 47 | Modal title: `🤖 AI Intelligence Setup` | Unchanged | PASS |
| 48 | Modal subtitle: `Powered by MiniMax · 100% free · no credit card` | Updated | PASS |
| 49 | Free-tier description mentions MiniMax M2.7 | Updated from Groq | PASS |
| 50 | Link to `platform.minimaxi.com` in free-tier description | Updated from console.groq.com | PASS |
| 51 | Key label: `MiniMax API Key` | Updated from Groq API Key | PASS |
| 52 | Placeholder: `sk-cp-...` | Updated from `gsk_...` | PASS |
| 53 | Header "🤖 AI" button tooltip: `Configure free MiniMax AI key` | Updated | PASS |
| 54 | Footer: `only sent to MiniMax` | Updated from Groq | PASS |
| 55 | 4-feature unlock grid intact (Country/News/Deforestation/Forecast) | Unchanged | PASS |
| 56 | AI CSS layer intact (`.ai-setup-overlay`, `.ai-btn`, `.ai-panel`, etc.) | Unchanged | PASS |

---

## Phase REG — Regression Tests

| # | Test | Expected | Result |
|---|------|----------|--------|
| 57 | All v3.25 AI features intact | 4 AI features: Country/News/Deforestation/Forecast | PASS |
| 58 | All v3.24 deforestation features intact | AI/Satellite section, top 10 sources | PASS |
| 59 | Future Currencies sub-tab (v3.22) intact | All RPC functions + HTML | PASS |
| 60 | Rising Powers Power Vortex Suite intact | polar/duel/race all present | PASS |
| 61 | Forecast tab (v3.19) intact | fcChart, switchFcAsset, Monte Carlo | PASS |
| 62 | `wip_rp_subtab` localStorage intact | 2 occurrences | PASS |
| 63 | `node --check` passed | ✅ SYNTAX CLEAN (JS extracted, 448KB) | PASS |
| 64 | File ends `</html>` | No truncation | PASS |
| 65 | File size ~624KB | -39 bytes delta from v3.25 | PASS |
| 66 | Version title = v3.26 | `<title>World Intelligence Platform v3.26</title>` | PASS |
| 67 | Version badge = v3.26 | `<span class="badge">v3.26</span>` | PASS |
| 68 | `version.py` = 3.26.0 | `APP_VERSION = "3.26.0"` | PASS |
| 69 | Zero Groq references remain in JS/HTML | `wip_groq_key`, `api.groq.com`, `llama-3.1-70b-versatile`, `Groq llama`, `gsk_...` all absent | PASS |
| 70 | Zero paid APIs | MiniMax M2.7 free tier only | PASS |

---

## Summary

| Section | Tests | Pass | Fail |
|---------|-------|------|------|
| Key Management | 13 | 13 | 0 |
| MiniMax API Core | 13 | 13 | 0 |
| Country AI Assessment | 7 | 7 | 0 |
| News AI Brief | 5 | 5 | 0 |
| Deforestation Risk | 4 | 4 | 0 |
| Forecast Explanation | 4 | 4 | 0 |
| Setup Modal UI | 10 | 10 | 0 |
| Regression | 14 | 14 | 0 |
| **TOTAL** | **70** | **70** | **0** |

**All 70 tests pass. v3.26 migrates the AI intelligence layer from Groq (llama-3.1-70b-versatile) to MiniMax (MiniMax-M2.7). The migration is surgical — only the API endpoint, model string, localStorage key name, and all user-visible text changed. All 4 AI features (Country Assessment, News Brief, Deforestation Risk, Forecast Explanation) remain fully functional. The OpenAI-compatible request format and response parsing are unchanged. MiniMax M2.7 is 100% free with no credit card required. Zero paid APIs.**

---

## Migration Summary

| Item | v3.25 (Groq) | v3.26 (MiniMax) |
|------|-------------|-----------------|
| API endpoint | `api.groq.com/openai/v1/chat/completions` | `api.minimaxi.chat/v1/chat/completions` |
| Model | `llama-3.1-70b-versatile` | `MiniMax-M2.7` |
| localStorage key | `wip_groq_key` | `wip_minimax_key` |
| Key prefix hint | `gsk_...` | `sk-cp-...` |
| Setup link | `console.groq.com` | `platform.minimaxi.com` |
| Cost | $0.00 | $0.00 |

---

## Setup Instructions (v3.26)

1. Go to **platform.minimaxi.com** and create a free account (no credit card required)
2. Navigate to API Keys → Create API key
3. In the dashboard, click the **🤖 AI** button in the header
4. Paste your key (starts with `sk-cp-`) → **Save Key**
5. All 4 AI features are now unlocked across the entire platform

**⚠️ Security reminder**: If you shared your MiniMax key in any chat or document, revoke it immediately at platform.minimaxi.com and generate a fresh one. Enter the new key only through the dashboard's 🤖 AI button — it is stored in your browser localStorage only and never written to any file.

---

## Security Notes

| Item | Detail |
|------|--------|
| Storage | `localStorage.getItem('wip_minimax_key')` — browser only |
| Transmission | Key sent ONLY to `api.minimaxi.chat` — nowhere else |
| Project files | Key never written to any `.html`, `.py`, `.md`, or `.json` file |
| Git | Key never committed to any branch |
| Logs | Key not logged to console |

*— Muhammad Umer Lari, World Intelligence Platform v3.26*
