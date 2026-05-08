@echo off
title AppCook — Push prod
echo.
echo  ========================================
echo   AppCook — Push vers NAS + GitHub
echo  ========================================
echo.

cd /d "%~dp0"

REM ── Push NAS (deploy automatique) ────────────────────────────────────────────
echo  [1/2] Push NAS (deploy en prod)...
echo        (entre ton mot de passe SSH si demande)
echo.
git push nas main

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERREUR : push NAS echoue.
    pause
    exit /b 1
)

REM ── Push GitHub (backup) ─────────────────────────────────────────────────────
echo.
echo  [2/2] Push GitHub (backup)...
echo.
git push github main

echo.
echo  ========================================
echo   Deploy lance + GitHub a jour !
echo  ========================================
echo.
pause
