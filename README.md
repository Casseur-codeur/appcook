# AppCook v2

Application mobile-first de gestion de recettes et listes de courses.  
Stack : React + Vite (frontend) · FastAPI + SQLite (backend) · Docker · nginx

---

## Lancement rapide (Docker)

### Prérequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé

### 1. Cloner le repo

```bash
git clone https://github.com/julienlambs/appcook.git
cd appcook
```

### 2. Lancer l'app

```bash
docker-compose up --build
```

L'app est disponible sur **http://localhost:8082**

### 3. Peupler la base de données

Au premier lancement la base est vide. Pour l'initialiser avec des données de test :

```bash
docker exec appcook_api python seed.py
```

---

## Lancement en mode développement (sans Docker)

### Prérequis
- Python 3.11+
- Node.js 20+

### Backend

```bash
cd backend
pip install -r requirements.txt
mkdir -p data
python seed.py
python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

L'app est disponible sur **http://localhost:5173**

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
├── docker-compose.yml
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
