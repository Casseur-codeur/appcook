# AppCook — Brief de refonte v2

## Vision

Application mobile de gestion de recettes, liste de courses et administration, conçue spécifiquement pour les personnes atteintes de TDAH. Accessible depuis l'écran d'accueil de la tablette/téléphone (PWA), belle, rapide, sans friction.

L'app est divisée en **3 sections**, toutes pensées pour le TDAH :
- **Recettes** — trouver et cuisiner une recette sans paralysie de décision
- **Courses** — générer et cocher une liste sans effort
- **Admin** — gérer les recettes et le catalogue en dehors du flux quotidien

---

## Contexte

L'app existante tourne sur un NAS Synology dans Docker via Streamlit. Elle fonctionne mais Streamlit n'est pas adapté au mobile. L'objectif est une refonte complète du frontend tout en conservant la logique backend (Python + SQLite).

L'app Streamlit reste active pendant le développement de la nouvelle version.

---

## Stack technique

| Couche | Techno | Raison |
|---|---|---|
| Backend API | FastAPI (Python) | Réutilise db.py existant, async, rapide |
| Frontend | React + Vite | Mobile-first, PWA, expérience native |
| Style | Tailwind CSS | Utility-first, dark mode natif |
| DB | SQLite (inchangée) | Pas de migration de moteur nécessaire |
| Infra | Docker sur NAS Synology | Infra existante conservée |
| Accès distant | Tailscale | Déjà en place |

### Architecture Docker

```
docker-compose.yml
├── service: api        (FastAPI, port 8000)
└── service: frontend   (Nginx servant le build React, port 80)
```

L'app est accessible sur `http://[IP-NAS]:80` depuis le réseau local ou via Tailscale.

---

## Workflow de développement

```
PC Windows (dev)
├── Backend  → uvicorn main:app --reload     (port 8000)
└── Frontend → npm run dev                   (port 5173)
      ↓ test en local sur localhost
      ↓ test tablette via IP locale du PC

NAS Synology (prod)
└── git pull + docker-compose up --build
      ↓ version stable, accessible via Tailscale
      ↓ installer en PWA sur la tablette → mode offline
```

**Prérequis PC** : Python (installé), VS Code (installé), Node.js (à installer)

---

## Schéma DB — changements par rapport à l'existant

### Tables conservées (inchangées)
```
ingredient_catalog   -- catalogue global des ingrédients
recipe_ingredients   -- liaison recette ↔ ingrédients (qty, unit)
step_ingredients     -- liaison étape ↔ ingrédients
ingredient_alias     -- synonymes d'ingrédients
unit_alias           -- synonymes d'unités
```

### Table `recipes` — modifications
| Colonne | Action | Note |
|---|---|---|
| id, code, name, base_servings, notes | ✅ Conserver | Inchangés |
| category | ✅ Conserver + **activer dans l'UI** | Filtre dans la grille |
| cookeo_modes | ❌ Supprimer | Spécifique Cookeo, inutile |
| is_batch | ➕ Ajouter | BOOLEAN — recette batch cooking (se conserve) |
| origin | ➕ Ajouter | TEXT — cuisine du monde (ex: japonais, mexicain, italien...) |

### Table `steps` — modifications
| Colonne | Action |
|---|---|
| id, recipe_id, step_no, title, instruction, time_min | ✅ Conserver |
| cookeo_mode | ❌ Supprimer |

### Nouvelle table `cooking_history`
```sql
CREATE TABLE cooking_history (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id  INTEGER NOT NULL REFERENCES recipes(id),
  cooked_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```
Alimentée automatiquement à la fin du Focus Mode. Aucune action manuelle requise.

### Unités canoniques (inchangées)
```
Poids  : g, kg
Volume : ml, cl, l
Pièces : pièce, gousse, tranche, cube, pincée, cs, cc
```

---

## Navigation

Barre d'onglets en bas (bottom nav) — standard mobile :

```
[🍳 Recettes]  [🛒 Courses]  [⚙️ Admin]
```

---

## Écrans

### 1. Home (écran d'accueil)
- 2 gros boutons : **🍳 Cuisiner une recette** / **🛒 Faire les courses**
- Accès direct à l'Admin via bottom nav
- Aucune décision parasite à l'ouverture

### 2. Recettes — Filtres + Grille

**Filtres rapides (en haut, chips cliquables) :**
- Temps disponible : `< 20 min` / `~30 min` / `J'ai le temps`
- Batch cooking : toggle `🥡 Batch`
- Catégorie : chips par type de plat
- Origine : chips par cuisine du monde

**Grille :**
- Cartes visuelles : nom, temps total estimé, nb portions, badges (batch, origine)
- Tap sur une carte → vue détail

### 3. Recette — Vue détail
- Nom + métadonnées (temps total, portions)
- Scaling du nombre de personnes
- Liste des ingrédients complète
- Liste des étapes avec badges numérotés
- Temps total affiché de façon concrète : *"~25 min — tu as le temps avant 20h30"*
- Bouton **"🎯 Cuisiner"** très visible → lance le Focus Mode

### 4. Focus Mode (priorité max)
- Plein écran, bottom nav cachée
- Barre de progression en haut (Étape X/N)
- Une seule étape affichée à la fois, texte grand
- Aperçu discret de l'étape suivante en bas (réduit l'anxiété)
- Timer countdown par étape (démarrable/pausable) si `time_min` renseigné
- Ingrédients de l'étape dans un encadré
- Boutons **Précédente / Suivante** grands et facilement tappables
- **"✅ Terminé !"** à la dernière étape → enregistrement automatique dans `cooking_history`

### 5. Courses — Sélection
- Grille de cartes pour choisir les recettes à inclure
- Input nb de personnes par recette (scaling)
- Toggle ingrédients optionnels (inclure / exclure)
- Bouton **"Générer la liste"**

### 6. Courses — Liste
- Barre de progression en haut (X/Y cochés)
- Gros checkboxes tactiles
- Bouton **Copier** (compatible Google Keep / .txt)
- Message de complétion quand tout est coché

### 7. Admin — Recettes
- Flow guidé step-by-step pour créer/modifier une recette
- Étape 1 : infos de base (nom, portions, catégorie, origine, is_batch)
- Étape 2 : ingrédients (searchbox avec création à la volée)
- Étape 3 : étapes de préparation (avec durée optionnelle)
- Validation finale + aperçu
- Actions destructrices (supprimer) clairement séparées et confirmées

### 8. Admin — Catalogue ingrédients
- Voir et modifier les ingrédients existants (unité par défaut, show_qty, alias)
- Fusionner des doublons

### 9. Admin — Import / Export
- Import de recettes au format JSON (`appcook.recipe.v1`)
- Export de toutes les recettes ou d'une sélection

---

## Suggestion intelligente

La suggestion apparaît en tête de grille (carte mise en avant) après application des filtres.

**Logique de suggestion :**
1. Filtrer par temps disponible (sélectionné)
2. Exclure les recettes cuisinées dans les 7 derniers jours (via `cooking_history`)
3. Mettre en avant les recettes batch si l'utilisateur n'a pas cuisiné batch récemment
4. Parmi les résultats : sélectionner aléatoirement une recette à mettre en avant

---

## Principes UX TDAH

### Ce qui est critique
- **Un seul focus à la fois** — jamais plusieurs tâches visibles simultanément
- **Timer par étape** — contre le time blindness
- **Ancrage temporel concret** — "tu as le temps avant 20h30", pas juste "25 min"
- **Feedback immédiat** — chaque action confirmée visuellement
- **Progress visible** — barres de progression, compteurs, états de complétion
- **Réduction de friction** — pas de décisions inutiles, defaults sensés, actions en 1 tap
- **Anticipation** — aperçu de l'étape suivante pour éviter l'anxiété de l'inconnu

### Ce qui aide
- Dark mode (moins de fatigue visuelle)
- Texte grand et lisible en Focus Mode
- Ordre des étapes clair (badge numéroté)
- Ingrédients de l'étape visibles sans scroller
- Checkboxes satisfaisants à cocher
- Badge "batch" visible dès la grille (argument motivationnel : "je cuisine une fois, je mange 4 jours")

### Ce qu'il faut éviter
- Formulaires longs avec beaucoup de champs (réservés à l'Admin)
- Navigation ambiguë (toujours savoir où on est)
- Actions irréversibles sans confirmation
- Surcharge d'information sur un même écran
- Temps de réponse lent

---

## Design

- **Mode** : Dark uniquement (pas de toggle)
- **Couleur accent** : `#FF6B35` (orange)
- **Palette :**

```css
--bg-primary:    #0F1117;
--bg-secondary:  #1A1D27;
--bg-tertiary:   #2A2D3A;
--accent:        #FF6B35;
--accent-dark:   #E84F1B;
--text-primary:  #E8EAF0;
--text-muted:    #8B8FA8;
--success:       #4CAF50;
--warning:       #FFC107;
```

---

## PWA — Installation écran d'accueil

```json
{
  "name": "AppCook",
  "short_name": "AppCook",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0F1117",
  "theme_color": "#FF6B35"
}
```

Mode offline : les recettes consultées sont mises en cache par le service worker. L'app reste utilisable en Focus Mode sans connexion au NAS.

---

## Recettes d'exemple

Voir le dossier `recettes_exemple/` :
- `poulet_cajun_riz.json` — batch cooking, épices cajun
- `steak_hache_pates.json` — ultra rapide, < 20 min
- `riz_saute_oeuf_bacon.json` — fried rice express

---

## Fichiers de référence

- `db_reference/db.py` — logique DB existante à porter en FastAPI
- `SCHEMA_DB.md` — schéma complet + script de migration SQL
- `ARCHITECTURE.md` — architecture technique détaillée
