@echo off
title WhimsyWand Tales Studio Launcher
echo ===================================================
echo      WhimsyWand Tales AI Studio Starting...
echo ===================================================
echo 1. Starting FastAPI Backend on http://localhost:8000
start "WhimsyWand Backend (FastAPI)" cmd /k "python server.py"

echo 2. Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak >nul

echo 3. Starting Next.js Studio on http://localhost:3000
start "WhimsyWand Studio (Next.js)" cmd /k "cd web && npm start -- -p 3000"

echo 4. Opening Studio in your default browser...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo ===================================================
echo   Studio is LIVE at: http://localhost:3000
echo   Enjoy creating your bedtime stories tomorrow!
echo ===================================================
pause
