# AppCook v2

Application mobile-first de gestion de recettes et listes de courses.  
Stack : React + Vite (frontend) · FastAPI + SQLite (backend) · Docker · nginx

---

## Déploiement Docker

### Prérequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé

### 1. Cloner le repo

```bash
git clone https://github.com/julienlambs/appcook.git
cd appcook
```

### 2. Déployer l'app

```bash
docker compose pull
docker compose up -d
```

Par défaut, l'app est disponible sur :

- **http://localhost:8082** si aucun certificat TLS n'est monté
- **https://localhost:8443** si des certificats sont présents dans `deploy/certs/`

En mode HTTPS, nginx redirige automatiquement HTTP vers HTTPS.

### Activer et forcer HTTPS

Le container frontend sait maintenant servir :

- HTTP simple en mode `APPCOOK_HTTPS_MODE=off`
- HTTP simple automatiquement si aucun certificat n'est trouvé en mode `APPCOOK_HTTPS_MODE=auto`
- HTTPS + redirection HTTP -> HTTPS en mode `APPCOOK_HTTPS_MODE=redirect`

Par défaut, Compose monte le dossier local suivant dans le container :

```bash
./deploy/certs
```

Le plus simple est d'y placer :

```bash
deploy/certs/fullchain.pem
deploy/certs/privkey.pem
```

Puis de lancer :

```bash
export APPCOOK_HTTPS_MODE=redirect
docker compose up -d
```

Si tu veux utiliser les ports standards en production :

```bash
export APPCOOK_HTTP_PORT=80
export APPCOOK_HTTPS_PORT=443
export APPCOOK_HTTPS_REDIRECT_PORT=443
export APPCOOK_HTTPS_MODE=redirect
docker compose up -d
```

Tu peux aussi monter un autre répertoire de certificats :

```bash
export APPCOOK_TLS_CERT_DIR=/volume1/docker/appcook/certs
export APPCOOK_HTTPS_MODE=redirect
docker compose up -d
```

### Configuration sécurité recommandée

L'espace admin est protégé par un secret :

- si `APPCOOK_ADMIN_TOKEN` est défini, AppCook utilise cette valeur
- sinon, AppCook génère automatiquement un secret fort au premier démarrage et le stocke à côté de la base SQLite dans `admin_token.txt`

Avec le `docker-compose.yml` actuel, le fichier généré côté hôte sera en pratique :

```bash
/volume1/docker/appcook/data/admin_token.txt
```

Si tu lances seulement le backend en local sans Docker, ce sera par défaut :

```bash
backend/data/admin_token.txt
```

Optionnellement, tu peux toujours forcer ton propre secret :

```bash
export APPCOOK_ADMIN_TOKEN="choisis-un-secret-long-et-aleatoire"
export APPCOOK_ALLOWED_ORIGINS="http://localhost:5173"
docker compose pull
docker compose up -d
```

- `APPCOOK_ADMIN_TOKEN` remplace le secret auto-généré si tu veux un secret imposé par l'infra.
- `APPCOOK_ALLOWED_ORIGINS` limite les appels cross-origin. En production derrière nginx sur le même domaine, tu peux souvent le laisser vide.
- `APPCOOK_HTTPS_MODE=redirect` force HTTPS si `fullchain.pem` et `privkey.pem` sont disponibles.

### 3. Peupler la base de données

Au premier lancement la base est vide. Pour l'initialiser avec des données de test :

```bash
docker exec appcook_api python seed.py
```

---

## Développement local

### Prérequis
- Python 3.11+
- Node.js 20+

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

L'app est disponible sur **http://localhost:5173**

Au premier démarrage local, si `APPCOOK_ADMIN_TOKEN` n'est pas défini, le backend génère un token persistant dans :

```bash
backend/data/admin_token.txt
```

---

## Publication des images

Le workflow GitHub Actions publie automatiquement deux images Docker sur GHCR à chaque push sur `main` :

- `ghcr.io/<owner>/appcook-api:latest`
- `ghcr.io/<owner>/appcook-frontend:latest`

Le `docker-compose.yml` du repo est prévu pour la production et utilise directement ces images préconstruites. Le flux côté serveur reste donc :

```bash
docker compose pull
docker compose up -d
```

Le répertoire de données reste monté sur :

```bash
/volume1/docker/appcook/data
```

Si `APPCOOK_ADMIN_TOKEN` n'est pas fourni en prod, AppCook générera aussi un token persistant dans :

```bash
/volume1/docker/appcook/data/admin_token.txt
```

### Variables utiles en prod

- `IMAGE_TAG` : permet d'épingler une version précise, par exemple un tag Git ou un SHA publié par GitHub Actions
- `IMAGE_NAMESPACE` : permet de changer le namespace GHCR si besoin
- `APPCOOK_ADMIN_TOKEN` : override optionnel du token auto-généré
- `APPCOOK_ALLOWED_ORIGINS` : origines frontend autorisées si tu sers l'API derrière un autre domaine
- `APPCOOK_HTTPS_MODE` : `auto`, `off` ou `redirect`
- `APPCOOK_HTTP_PORT` : port HTTP publié par Docker, `8082` par défaut
- `APPCOOK_HTTPS_PORT` : port HTTPS publié par Docker, `8443` par défaut
- `APPCOOK_HTTPS_REDIRECT_PORT` : port cible utilisé dans la redirection HTTP -> HTTPS
- `APPCOOK_TLS_CERT_DIR` : dossier monté dans le container contenant les certificats
- `APPCOOK_TLS_CERT_PATH` : chemin du certificat dans le container, `fullchain.pem` par défaut
- `APPCOOK_TLS_KEY_PATH` : chemin de la clé privée dans le container, `privkey.pem` par défaut
- `APPCOOK_TLS_SERVER_NAME` : `server_name` nginx si tu veux le restreindre à un domaine précis

Si le package GHCR est privé, il faut aussi faire un `docker login ghcr.io` sur le serveur avant le premier `pull`.

### Déploiement automatique via GitHub Actions

Le workflow [deploy.yml](/Users/jblafon/Documents/GitHub/appcook/.github/workflows/deploy.yml) se déclenche :

- automatiquement après un publish réussi sur `main`
- manuellement via `workflow_dispatch` pour redéployer un tag précis

Secrets GitHub Actions à configurer :

- `DEPLOY_HOST` : hostname ou IP du Synology
- `DEPLOY_USER` : utilisateur SSH
- `DEPLOY_SSH_KEY` : clé privée SSH utilisée par GitHub Actions
- `DEPLOY_PATH` : chemin du repo sur le serveur, par exemple `/volume1/docker/appcook`
- `APPCOOK_ADMIN_TOKEN` : optionnel, pour imposer un token au lieu du token auto-généré
- `APPCOOK_ALLOWED_ORIGINS` : optionnel
- `APPCOOK_HTTPS_MODE` : optionnel, mais recommandé à `redirect` en production
- `APPCOOK_HTTP_PORT` / `APPCOOK_HTTPS_PORT` / `APPCOOK_HTTPS_REDIRECT_PORT` : optionnels
- `APPCOOK_TLS_CERT_DIR` : optionnel si tu utilises `./deploy/certs`, sinon à renseigner
- `APPCOOK_TLS_CERT_PATH` / `APPCOOK_TLS_KEY_PATH` / `APPCOOK_TLS_SERVER_NAME` : optionnels
- `GHCR_USERNAME` : optionnel si les images GHCR sont publiques
- `GHCR_PULL_TOKEN` : optionnel si les images GHCR sont publiques
- `DEPLOY_PORT` : optionnel, sinon port `22`

Le workflow écrit un fichier `.env` sur le serveur avec les variables runtime, fait un login GHCR si nécessaire, puis exécute :

```bash
docker compose pull
docker compose up -d
```

Pour une PWA installable sur mobile hors localhost, HTTPS est nécessaire. La configuration ci-dessus permet donc d'avoir à la fois :

- redirection automatique vers HTTPS
- en-tête HSTS
- API servie derrière le même domaine en HTTPS

---

## Structure du projet

```
appcook/
├── backend/          # API FastAPI + base SQLite
│   ├── main.py       # Routes API
│   ├── db.py         # Accès base de données
│   ├── seed.py       # Données initiales
│   └── requirements.txt
├── frontend/         # Interface React
│   ├── src/
│   │   ├── pages/    # Pages de l'app
│   │   ├── components/
│   │   └── api/      # Appels API
│   └── public/       # Manifest PWA, icônes
├── docker-compose.yml       # Compose production (pull GHCR)
└── recettes_exemple/ # Recettes JSON importables
```

---

## Fonctionnalités

- 📋 Gestion de recettes (création, édition, suppression)
- 🛒 Génération automatique de listes de courses
- 📦 Bundles d'articles récurrents
- 🎯 Mode focus pour cuisiner étape par étape
- 📱 PWA installable sur Android / iOS
- 📤 Import / export de recettes en JSON
