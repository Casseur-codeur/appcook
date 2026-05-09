@echo off
title AppCook — Push prod
echo.
echo  ========================================
echo   AppCook — Merge dev + Deploy prod
echo  ========================================
echo.

cd /d "%~dp0"

REM ── Merge dev dans main ───────────────────────────────────────────────────────
echo  [1/3] Merge dev dans main...
echo.
git checkout main
if %ERRORLEVEL% neq 0 ( echo ERREUR : checkout main echoue. & pause & exit /b 1 )

git merge dev
if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERREUR : merge echoue. Resous les conflits puis relance.
    git checkout dev
    pause
    exit /b 1
)

REM ── Push NAS (deploy automatique) ────────────────────────────────────────────
echo.
echo  [2/3] Push NAS (deploy en prod)...
echo        (entre ton mot de passe SSH si demande)
echo.
git push nas main

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERREUR : push NAS echoue.
    git checkout dev
    pause
    exit /b 1
)

REM ── Push GitHub (backup) ─────────────────────────────────────────────────────
echo.
echo  [3/3] Push GitHub (backup)...
echo.
git push github main

REM ── Retour sur dev ───────────────────────────────────────────────────────────
git checkout dev

echo.
echo  ========================================
echo   Deploy lance + GitHub a jour !
echo   Tu es de retour sur la branche dev.
echo  ========================================
echo.
pause
