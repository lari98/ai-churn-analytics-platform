@echo off
title World Intelligence Platform — 24/7 Watchdog
color 0A

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║   World Intelligence Platform — 24/7 Mode   ║
echo  ║   Watchdog Agent + Auto-Heal + Auto-Update   ║
echo  ╚══════════════════════════════════════════════╝
echo.
echo  Starting watchdog agent...
echo  Dashboard:  open dashboard\world-intelligence.html in browser
echo  API:        http://localhost:8111/api/health
echo  API docs:   http://localhost:8111/docs
echo  Log file:   backend\agent.log
echo.
echo  Press Ctrl+C to stop everything.
echo.

cd /d C:\Users\Sidrah\Claude\UMER\Project\ai-churn-analytics-platform\backend
python watchdog_agent.py

pause
