# AppCook — Schéma DB et migration

## Tables existantes (à conserver)

### `recipes`
| Colonne | Type | Conserver | Note |
|---|---|---|---|
| id | INTEGER PK | ✅ | |
| code | TEXT UNIQUE | ✅ | Slug du nom (ex: `poulet_cajun`) |
| name | TEXT | ✅ | Nom affiché |
| category | TEXT | ✅ | Garder en DB, masquer dans l'UI pour l'instant |
| base_servings | REAL | ✅ | Nombre de portions de base |
| cookeo_modes | TEXT | ❌ | **À supprimer** — spécifique Cookeo, inutile |
| notes | TEXT | ✅ | Notes libres sur la recette |

### `ingredient_catalog`
| Colonne | Type | Conserver | Note |
|---|---|---|---|
| id | INTEGER PK | ✅ | |
| name | TEXT UNIQUE | ✅ | Nom canonique |
| norm_name | TEXT | ✅ | Nom normalisé (accents, pluriels) |
| default_unit | TEXT | ✅ | Unité par défaut pour les courses |
| show_qty_in_list | INTEGER | ✅ | 0 = ingrédient "toujours chez soi" (sel, poivre…) |

### `recipe_ingredients`
| Colonne | Type | Conserver | Note |
|---|---|---|---|
| id | INTEGER PK | ✅ | |
| recipe_id | INTEGER FK | ✅ | |
| ingredient_id | INTEGER FK | ✅ | |
| qty | REAL | ✅ | Quantité pour base_servings |
| unit | TEXT | ✅ | Unité dans cette recette |
| optional | INTEGER | ✅ | 1 = ingrédient optionnel |
| notes | TEXT | ✅ | Note sur cet ingrédient dans la recette |

### `steps`
| Colonne | Type | Conserver | Note |
|---|---|---|---|
| id | INTEGER PK | ✅ | |
| recipe_id | INTEGER FK | ✅ | |
| step_no | INTEGER | ✅ | Numéro d'ordre |
| title | TEXT | ✅ | Titre court (optionnel) |
| instruction | TEXT | ✅ | Texte de l'étape |
| cookeo_mode | TEXT | ❌ | **À supprimer** — spécifique Cookeo |
| time_min | REAL | ✅ | Durée estimée (pour le timer TDAH) |

### `step_ingredients`
| Colonne | Type | Conserver | Note |
|---|---|---|---|
| id | INTEGER PK | ✅ | |
| step_id | INTEGER FK | ✅ | |
| recipe_ingredient_id | INTEGER FK | ✅ | Lie une étape à un ingrédient de la recette |

### `ingredient_alias`
| Colonne | Conserver | Note |
|---|---|---|
| id, ingredient_id, alias_name, alias_norm_name | ✅ | Permet la résolution de synonymes |

### `unit_alias`
| Colonne | Conserver | Note |
|---|---|---|
| id, alias, alias_norm, unit | ✅ | Normalisation des unités |

---

## Migration — Script SQL

À exécuter sur la DB existante avant de lancer la nouvelle app :

```sql
-- Backup d'abord !
-- cp recettes.db recettes_backup_YYYYMMDD.db

-- Supprimer cookeo_modes des recettes
-- (SQLite ne supporte pas DROP COLUMN avant 3.35, utiliser la méthode reconstruction)
CREATE TABLE recipes_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  category TEXT,
  base_servings REAL NOT NULL,
  notes TEXT
);
INSERT INTO recipes_new SELECT id, code, name, category, base_servings, notes FROM recipes;
DROP TABLE recipes;
ALTER TABLE recipes_new RENAME TO recipes;

-- Supprimer cookeo_mode des steps
CREATE TABLE steps_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipe_id INTEGER NOT NULL,
  step_no INTEGER NOT NULL,
  title TEXT,
  instruction TEXT NOT NULL,
  time_min REAL,
  FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
  UNIQUE(recipe_id, step_no)
);
INSERT INTO steps_new SELECT id, recipe_id, step_no, title, instruction, time_min FROM steps;
DROP TABLE steps;
ALTER TABLE steps_new RENAME TO steps;
```

---

## Unités canoniques

```
Poids  : g, kg
Volume : ml, cl, l
Pièces : pièce, gousse, tranche, cube, pincée, cs, cc
```

Règle : chaque ingrédient du catalogue a une `default_unit` dans cette liste. Les recettes peuvent utiliser des variantes (ex: `grs`, `kg`) qui sont résolues via `unit_alias`.

---

## Pièges connus

1. **Doublon d'ingrédients** — utiliser `norm_name` et `ingredient_alias` pour la déduplication. Ne jamais créer un ingrédient sans vérifier via `norm_name`.

2. **Agrégation liste de courses** — fonctionne uniquement si `default_unit` est renseignée ET compatible avec l'unité de la recette (même groupe : poids/volume/pièce).

3. **show_qty_in_list = 0** — ingrédients comme sel/poivre qu'on a toujours chez soi. Pas affichés dans la liste de courses mais présents dans les étapes.

4. **step_ingredients** — lien entre une étape et les `recipe_ingredients` (pas les `ingredient_catalog`). Permet d'afficher les ingrédients nécessaires à une étape précise en focus mode.

5. **Scaling** — les quantités dans la DB sont pour `base_servings`. Le facteur est `personnes_souhaitées / base_servings`.
