# ============================================================
#  World Intelligence Platform — Version & Author Metadata
#  Copyright (c) 2024-2025  Muhammad Umer Lari
#  All Rights Reserved.
#
#  Unauthorised copying, modification, or distribution of
#  this software is strictly prohibited without the express
#  written permission of Muhammad Umer Lari.
# ============================================================

APP_NAME        = "World Intelligence Platform"
APP_VERSION     = "3.17.0"
APP_AUTHOR      = "Muhammad Umer Lari"
APP_COPYRIGHT   = "Copyright © 2024-2025 Muhammad Umer Lari. All Rights Reserved."
APP_DESCRIPTION = "Real-time global intelligence: markets, environment, AQI, climate & AI signals."
APP_URL         = "https://github.com/lari98/ai-churn-analytics-platform"

# ── Update endpoint ─────────────────────────────────────────
# If you make the SOURCE repo private, keep a SEPARATE public repo
# (e.g. lari98/wip-releases) for release metadata so the auto-updater
# can reach it without auth.  Change PUBLIC_UPDATE_REPO to that repo.
# For now it points to the same repo — works while repo is public.
PUBLIC_UPDATE_REPO = "lari98/ai-churn-analytics-platform"
APP_UPDATE_URL     = f"https://api.github.com/repos/{PUBLIC_UPDATE_REPO}/releases/latest"

APP_SUPPORT     = "umerlari1998@gmail.com"
APP_PUBLISHER   = "Muhammad Umer Lari"

# Backend config
BACKEND_HOST    = "127.0.0.1"
BACKEND_PORT    = 8111
DASHBOARD_FILE  = "dashboard/world-intelligence.html"

# Version tuple for comparison
VERSION_TUPLE   = tuple(int(x) for x in APP_VERSION.split("."))

def version_str():
    return APP_VERSION

def full_banner():
    return (
        f"\n{'='*60}\n"
        f"  {APP_NAME}  v{APP_VERSION}\n"
        f"  {APP_COPYRIGHT}\n"
        f"  {APP_URL}\n"
        f"{'='*60}\n"
    )
