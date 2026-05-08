@echo off
title AppCook — Reset DB + Seed
echo.
echo  ========================================
echo   AppCook — Reset base de donnees + Seed
echo  ========================================
echo.
echo  ATTENTION : cela va SUPPRIMER toutes les donnees
echo  et repeupler la DB avec les donnees de test.
echo.
set /p CONFIRM="Continuer ? (O/N) : "
if /i not "%CONFIRM%"=="O" (
    echo Annule.
    pause
    exit /b
)

echo.

REM ── Arret du backend pour liberer le fichier DB ───────────────────────────
echo  [1/4] Arret du backend...
taskkill /FI "WINDOWTITLE eq AppCook Backend" /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000 "') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM ── Suppression de la DB ──────────────────────────────────────────────────
echo  [2/4] Suppression de recettes.db...
if exist "%~dp0backend\data\recettes.db" (
    del /f "%~dp0backend\data\recettes.db"
    echo         OK - base supprimee.
) else (
    echo         Pas de DB existante, on continue.
)

REM ── Execution du seed ────────────────────────────────────────────────────
echo  [3/4] Execution de seed.py...
echo.
cd /d "%~dp0backend"
python seed.py
echo.

REM ── Relancement du backend ───────────────────────────────────────────────
echo  [4/4] Relancement du backend...
start "AppCook Backend" cmd /k "cd /d "%~dp0backend" && echo Backend AppCook && echo. && python -m uvicorn main:app --reload --port 8000"

echo.
echo  ========================================
echo   Seed terminee ! Backend relance.
echo   Le frontend tourne toujours si ouvert.
echo  ========================================
echo.
pause
