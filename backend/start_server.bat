@echo off
title World Intelligence Backend v2.3
echo ============================================
echo   World Intelligence Platform - Backend
echo   Starting on http://localhost:8111
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Install deps if needed
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo Starting server...
echo API Docs: http://localhost:8111/docs
echo.
python market_server.py

pause
