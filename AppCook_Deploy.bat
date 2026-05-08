@echo off
title AppCook — Deploy NAS
echo.
echo  ========================================
echo   AppCook — Deploiement sur le NAS
echo  ========================================
echo.

REM ── Config ───────────────────────────────────────────────────────────────────
set NAS_USER=Aradions
set NAS_HOST=100.111.51.14
set NAS_SSH_PORT=3009
set NAS_PATH=/volume1/docker/appcook

echo  NAS  : %NAS_USER%@%NAS_HOST%:%NAS_SSH_PORT%
echo  Path : %NAS_PATH%
echo  Port app : 8082
echo.

REM ── 1. Envoi des fichiers (tar via SSH, exclut node_modules et data) ─────────
echo  [1/3] Envoi des fichiers vers le NAS...
echo        (entre ton mot de passe SSH si demande)
echo.

tar -czf - ^
  --exclude=node_modules ^
  --exclude=__pycache__ ^
  --exclude=*.pyc ^
  --exclude=.git ^
  --exclude=data ^
  -C "%~dp0." . | ssh -p %NAS_SSH_PORT% %NAS_USER%@%NAS_HOST% "mkdir -p %NAS_PATH% && cd %NAS_PATH% && tar -xzf -"

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERREUR : transfert de fichiers echoue.
    echo  Verifie que le NAS est accessible et que SSH fonctionne.
    pause
    exit /b 1
)

echo.
echo  Fichiers envoyes avec succes.

REM ── 2. Build Docker + lancement ──────────────────────────────────────────────
echo.
echo  [2/3] Build et lancement des containers Docker...
echo        (entre ton mot de passe Synology quand demande)
echo        (ca peut prendre 1-2 minutes, ne pas fermer la fenetre)
echo.

ssh -t -p %NAS_SSH_PORT% %NAS_USER%@%NAS_HOST% "cd %NAS_PATH% && sudo /usr/local/bin/docker-compose up -d --build"

if %ERRORLEVEL% neq 0 (
    echo.
    echo  ERREUR : docker-compose a echoue.
    echo  Connecte-toi en SSH et verifie avec : docker-compose logs
    pause
    exit /b 1
)

REM ── 3. Verification ──────────────────────────────────────────────────────────
echo.
echo  [3/3] Verification des containers...
echo.
ssh -t -p %NAS_SSH_PORT% %NAS_USER%@%NAS_HOST% "sudo /usr/local/bin/docker ps --filter name=appcook --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo.
echo  ========================================
echo   Deploiement termine !
echo   App dispo : http://%NAS_HOST%:8082
echo  ========================================
echo.
pause
