@echo off
:: ════════════════════════════════════════════════════════════════
:: World Intelligence Platform — Windows Autostart Setup
:: Registers the watchdog as a Task Scheduler job so it starts
:: automatically on every Windows boot (no login required).
::
:: Run this ONCE as Administrator, then it's permanent.
:: To remove: schtasks /Delete /TN "WorldIntelligence" /F
:: ════════════════════════════════════════════════════════════════

echo.
echo  Setting up Windows autostart for World Intelligence Platform...
echo.

set TASK_NAME=WorldIntelligencePlatform
set PYTHON_EXE=python
set SCRIPT=C:\Users\Sidrah\Claude\UMER\Project\ai-churn-analytics-platform\backend\watchdog_agent.py
set WORKDIR=C:\Users\Sidrah\Claude\UMER\Project\ai-churn-analytics-platform\backend

:: Delete existing task if it exists
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

:: Create scheduled task — runs at system startup, restarts every 1 min if it crashes
schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "\"%PYTHON_EXE%\" \"%SCRIPT%\"" ^
  /SC ONSTART ^
  /DELAY 0001:00 ^
  /RU SYSTEM ^
  /RL HIGHEST ^
  /F

if %ERRORLEVEL% EQU 0 (
  echo.
  echo  ✓ Autostart registered successfully!
  echo.
  echo  Task name : %TASK_NAME%
  echo  Runs at   : every Windows startup
  echo  Script    : %SCRIPT%
  echo.
  echo  To remove autostart:
  echo    schtasks /Delete /TN "%TASK_NAME%" /F
  echo.
  echo  To check status:
  echo    schtasks /Query /TN "%TASK_NAME%"
  echo.
  echo  To start NOW without rebooting:
  schtasks /Run /TN "%TASK_NAME%"
  echo  Started!
) else (
  echo.
  echo  ✗ Failed to register. Try running this as Administrator.
  echo    Right-click setup_autostart.bat → Run as administrator
)

pause
