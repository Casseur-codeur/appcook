@echo off
title AppCook — Lancement
echo.
echo  ========================================
echo   AppCook — Lancement backend + frontend
echo  ========================================
echo.

REM ── Backend (FastAPI + uvicorn) ──────────────────────────────────────────────
echo  [1/2] Demarrage du backend (port 8000)...
start "AppCook Backend" cmd /k "cd /d "%~dp0backend" && echo Backend AppCook && echo. && python -m uvicorn main:app --reload --port 8000"

REM Petite pause pour laisser uvicorn demarrer avant le frontend
timeout /t 2 /nobreak >nul

REM ── Frontend (Vite) ──────────────────────────────────────────────────────────
echo  [2/2] Demarrage du frontend (port 5173)...
start "AppCook Frontend" cmd /k "cd /d "%~dp0frontend" && echo Frontend AppCook && echo. && npm run dev"

echo.
echo  Les deux serveurs sont en cours de demarrage.
echo  Ouvre http://localhost:5173 dans ton navigateur.
echo.
timeout /t 3 /nobreak >nul

REM Ouvre le navigateur automatiquement
start http://localhost:5173
