# TEST REPORT — v3.32 — Recession Intelligence Fix

**Version:** 3.32.0  
**Date:** 2026-06-30  
**Fix Type:** Hotfix — Recession Intelligence blank content  

---

## Bug Fixed

**Symptom:** Clicking "📉 Recession Intelligence" sub-tab inside Crisis Map showed a completely blank/empty content area even though the tab was active.

**Root Cause:** `initRecession()` builds all recession panels (Historical Atlas, Warning Lights, Coming Storm) but never calls `showRecTab()` to activate the first panel. All `.rec-panel` divs defaulted to `display:none` with no function activating them.

**Chrome Debug Confirmed:**
- `crisis-sub-recession` div: present, `display:block`, 44KB of HTML ✓
- `_recInited = true` after click ✓
- All `.rec-panel` elements: `display:none` ← root cause
- After manually calling `showRecTab('historical', ...)`: content appeared at 780px height ✓

---

## Fix Applied

Added at end of `initRecession()`:
```javascript
setTimeout(function(){ showRecTab('historical', document.querySelector('.rec-stab')); }, 100);
```

This activates the "🏛️ Historical Atlas" panel by default 100ms after recession data is built.

---

## Tests

| Feature | Status |
|---------|--------|
| Recession Intelligence sub-tab click | ✅ Fixed |
| Historical Atlas panel visible on open | ✅ Fixed |
| Sub-tab buttons (Historical / Warning Lights / Coming Storm) | ✅ Working |
| Crisis Map sub-tab still works | ✅ Unchanged |
| JS syntax check (node --check) | ✅ No errors |
| `showCrisisSub` function present | ✅ Yes |
| `initRecessionMap()` call correct | ✅ Yes |

---

## Changes

- `dashboard/world-intelligence.html` — added `showRecTab` call in `initRecession()`
- `launcher/version.py` — bumped to 3.32.0
