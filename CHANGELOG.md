# Changelog — World Intelligence Platform
**Author: Muhammad Umer Lari**
**Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved.**

---

## [v3.4.0] — 2025

### Added
- **Environment Tab** (v3.3) — full suite: CO₂, global temperature, AQI map, sea level, renewables, deforestation, emissions donut, Net Zero pledges, country climate score
- **KPI fix** (v3.3.1) — environment KPIs no longer hidden under tab bar; scroll lag resolved
- **AQI Modal** (v3.4) — 50-city Live Air Quality map with clickable city cards; 4-tab detail modal (Overview, Pollutants, Trends, Health & Risk); past/present/future data; Escape key close
- **Launcher** — PyInstaller single `.exe`; silent FastAPI backend start; system tray icon (pystray); Windows single-instance mutex
- **Auto-updater** — GitHub Releases API check on startup (8 s delay); SHA-256 hash verification before applying update; silent background check
- **Inno Setup installer** — pre-install GitHub version check via Pascal script; proper Windows installer with desktop shortcut, Start Menu entry, optional startup entry, uninstaller
- **GitHub Actions workflow** — auto-builds `WorldIntelligence.exe` on version tag push; publishes GitHub Release with SHA-256 embedded in release notes
- **Author branding** — "Muhammad Umer Lari" hard-coded in: `version.py`, `launcher.py`, `updater.py`, `version_info.txt` (Windows file properties), `installer.iss` (installer wizard), `release.yml` (release notes), `LICENSE.txt`

### Fixed
- Environment tab DOM placement bug (page rendered outside `#pages` container)
- Nested scroll trap in environment page CSS
- `aqiColor` duplicate function definition
- PowerShell commit message parse error with parentheses

---

## [v3.2.0] — 2025

### Added
- Markets tab real-time price integration
- Vercel / Render deployment support (FastAPI backend on port 8111)

---

## [v3.1.0] — 2025

### Added
- Initial multi-tab dashboard: Markets, Economy, Crypto, AI Signals, Geopolitical, Tech GDP
