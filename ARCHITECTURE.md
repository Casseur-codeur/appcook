# AppCook — Architecture technique détaillée

## Vue d'ensemble

```
[Téléphone / navigateur]
        │  HTTPS
        ▼
[NAS Synology]
   ┌──────────────────────────────┐
   │  Docker Compose              │
   │                              │
   │  ┌─────────────┐             │
   │  │  Nginx      │ :80 / :443  │
   │  │  (React SPA)│             │
   │  └──────┬──────┘             │
   │         │ /api/*  proxy      │
   │  ┌──────▼──────┐             │
   │  │  FastAPI    │ :8000       │
   │  │  (Python)   │             │
   │  └──────┬──────┘             │
   │         │                    │
   │  ┌──────▼──────┐             │
   │  │  SQLite     │             │
   │  │  recettes.db│             │
   │  └─────────────┘             │
   └──────────────────────────────┘
```

---

## Structure des dossiers

```
appcook/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py              # FastAPI app + routes
│   ├── db.py                # Logique DB (repris de l'existant)
│   ├── utils.py             # Helpers
│   └── data/
│       └── recettes.db
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── public/
    │   ├── manifest.json    # PWA manifest
    │   └── icons/           # Icônes app (192x192, 512x512)
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/             # Appels FastAPI
        │   └── client.js
        ├── pages/
        │   ├── Home.jsx
        │   ├── Recipes.jsx
        │   ├── RecipeDetail.jsx
        │   ├── FocusMode.jsx
        │   ├── ShoppingSelect.jsx
        │   ├── ShoppingList.jsx
        │   └── Edit.jsx
        ├── components/
        │   ├── RecipeCard.jsx
        │   ├── StepCard.jsx
        │   ├── Timer.jsx
        │   ├── ProgressBar.jsx
        │   ├── IngredientSearch.jsx
        │   └── BottomNav.jsx
        └── styles/
            └── index.css    # Tailwind + variables dark theme
```

---

## PWA — Installation écran d'accueil

Le fichier `manifest.json` permet à Chrome/Safari de proposer "Ajouter à l'écran d'accueil".

```json
{
  "name": "AppCook",
  "short_name": "AppCook",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0F1117",
  "theme_color": "#FF6B35",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

`display: "standalone"` = l'app s'ouvre sans barre d'adresse, comme une app native.

---

## FastAPI — Endpoints principaux

```
GET    /api/recipes                  → liste toutes les recettes
GET    /api/recipes/{code}           → détail d'une recette (+ steps + ingredients)
POST   /api/recipes                  → créer une recette
PUT    /api/recipes/{code}           → modifier une recette
DELETE /api/recipes/{code}           → supprimer une recette
POST   /api/recipes/import           → importer depuis JSON

GET    /api/shopping?codes=a,b&p=2  → générer liste de courses
GET    /api/ingredients/search?q=   → recherche ingrédients (autocomplete)

GET    /api/catalog                  → catalogue ingrédients
PUT    /api/catalog/{id}             → modifier unité/show_qty d'un ingrédient
```

---

## Palette dark mode

```css
--bg-primary:    #0F1117;   /* fond principal */
--bg-secondary:  #1A1D27;   /* cartes, sidebar */
--bg-tertiary:   #2A2D3A;   /* inputs, séparateurs */
--accent:        #FF6B35;   /* orange principal */
--accent-dark:   #E84F1B;   /* orange foncé (gradient) */
--text-primary:  #E8EAF0;   /* texte principal */
--text-muted:    #8B8FA8;   /* texte secondaire */
--success:       #4CAF50;   /* vert validation */
--warning:       #FFC107;   /* jaune alerte */
```

---

## Navigation mobile

Navigation par **barre d'onglets en bas** (bottom nav) — standard mobile :

```
[🍳 Recettes]  [🛒 Courses]  [➕ Ajouter]  [⚙️ Admin]
```

---

## docker-compose.yml cible

```yaml
services:
  api:
    build: ./backend
    container_name: appcook_api
    volumes:
      - /volume1/docker/appcook/data:/data
    environment:
      - APPCOOK_DB_FILE=/data/recettes.db
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: appcook_frontend
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - api
    restart: unless-stopped
```

Nginx dans le container frontend peut servir en HTTP simple ou en HTTPS avec redirection automatique HTTP -> HTTPS selon `APPCOOK_HTTPS_MODE`. Il proxyfie `/api/*` vers le service `api:8000` en transmettant aussi les en-têtes `X-Forwarded-*`.

---

## Migration depuis Streamlit

1. Garder le container Streamlit actuel pendant le développement
2. Développer la nouvelle app sur un port différent (ex: 8080)
3. Tester en parallèle
4. Basculer le port 80 sur la nouvelle app quand prête
5. Supprimer l'ancien container Streamlit
