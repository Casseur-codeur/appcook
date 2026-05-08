@echo off
title AppCook — Relancement
echo.
echo  ========================================
echo   AppCook — Arret + Relancement
echo  ========================================
echo.

REM ── Fermeture des fenetres existantes ───────────────────────────────────────
echo  Fermeture des serveurs en cours...
taskkill /FI "WINDOWTITLE eq AppCook Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AppCook Frontend" /F >nul 2>&1

REM Tuer les processus qui ecoutent sur les ports 8000 et 5173 (securite)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 "') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173 "') do (
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

REM ── Backend ──────────────────────────────────────────────────────────────────
echo  [1/2] Relancement du backend...
start "AppCook Backend" cmd /k "cd /d "%~dp0backend" && echo Backend AppCook && echo. && python -m uvicorn main:app --reload --port 8000"

timeout /t 2 /nobreak >nul

REM ── Frontend ─────────────────────────────────────────────────────────────────
echo  [2/2] Relancement du frontend...
start "AppCook Frontend" cmd /k "cd /d "%~dp0frontend" && echo Frontend AppCook && echo. && npm run dev"

echo.
echo  Relancement termine. App disponible sur http://localhost:5173
echo.
timeout /t 3 /nobreak >nul
start http://localhost:5173
