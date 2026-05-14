# Demarrage rapide

Cette page permet de lancer AppCook rapidement en local ou via Docker.

## Prerequis

- Docker Desktop pour un lancement conteneurise
- Python 3.11+ pour le backend en local
- Node.js 20+ pour le frontend en local

## Option 1 - Docker

Depuis la racine du projet :

```bash
docker compose up -d
```

Par defaut :

- `http://localhost:8082` si HTTPS est desactive ou non configure
- `https://localhost:8443` si des certificats TLS sont presents

Pour peupler la base avec des donnees d'exemple :

```bash
docker exec appcook_api python seed.py
```

## Option 2 - Developpement local

### Backend

```bash
cd backend
pip install -r requirements.txt
mkdir -p data
python seed.py
export APPCOOK_ALLOWED_ORIGINS="http://localhost:5173"
python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Application disponible sur `http://localhost:5173`.

## Premier acces admin

Si `APPCOOK_ADMIN_TOKEN` n'est pas defini, le backend genere automatiquement un token persistant :

- en local : `backend/data/admin_token.txt`
- en production Docker : dans le volume de donnees monte avec la base SQLite

## Pages et docs utiles ensuite

- [Deploiement](Deployment.md)
- [Architecture](Architecture.md)
- [Admin et securite](Admin-and-Security.md)
- [README principal](../README.md)
