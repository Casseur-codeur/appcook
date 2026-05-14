# Deploiement

Cette page resume le mode de deploiement prevu pour AppCook.

## Mode cible

Le projet est concu pour tourner via Docker Compose avec :

- un conteneur frontend nginx
- un conteneur backend FastAPI
- une base SQLite stockee sur volume

## Images publiees

Le workflow GitHub Actions publie automatiquement des images Docker sur GHCR a chaque push sur `main` :

- `ghcr.io/<owner>/appcook-api:latest`
- `ghcr.io/<owner>/appcook-frontend:latest`

Le fichier [`docker-compose.yml`](../docker-compose.yml) est deja structure pour consommer ces images.

## HTTPS

Le frontend gere trois modes :

- `APPCOOK_HTTPS_MODE=off`
- `APPCOOK_HTTPS_MODE=auto`
- `APPCOOK_HTTPS_MODE=redirect`

Le mode `redirect` est celui a privilegier en production si les certificats sont disponibles.

Certificats attendus par defaut :

- `deploy/certs/fullchain.pem`
- `deploy/certs/privkey.pem`

## Variables d'environnement importantes

- `APPCOOK_ADMIN_TOKEN`
- `APPCOOK_ALLOWED_ORIGINS`
- `APPCOOK_HTTPS_MODE`
- `APPCOOK_HTTP_PORT`
- `APPCOOK_HTTPS_PORT`
- `APPCOOK_HTTPS_REDIRECT_PORT`
- `APPCOOK_TLS_CERT_DIR`
- `IMAGE_NAMESPACE`
- `IMAGE_TAG`

## Deploiement automatique

Le workflow [`deploy.yml`](../.github/workflows/deploy.yml) permet un redeploiement automatique apres publication des images ou via lancement manuel.

## Reference complete

Pour le detail exact des variables, secrets GitHub Actions et commandes :

- [README principal](../README.md)
