# Admin et securite

## Protection de l'espace admin

L'acces admin repose sur un token.

- Si `APPCOOK_ADMIN_TOKEN` est defini, cette valeur est utilisee
- Sinon, le backend genere automatiquement un token fort au premier demarrage

## Emplacement du token genere

- Local : `backend/data/admin_token.txt`
- Docker / production : fichier stocke a cote de la base dans le volume de donnees

## Recommandations

- Definir explicitement `APPCOOK_ADMIN_TOKEN` en production si l'infrastructure l'exige
- Limiter `APPCOOK_ALLOWED_ORIGINS` quand l'API est exposee cross-origin
- Preferer `APPCOOK_HTTPS_MODE=redirect` avec des certificats valides

## GHCR prive

Si les images publiees sur GHCR sont privees, un `docker login ghcr.io` doit etre effectue sur le serveur avant le premier `docker compose pull`.

## Reference complete

Pour la liste detaillee des variables et secrets de deploiement :

- [README principal](../README.md)
