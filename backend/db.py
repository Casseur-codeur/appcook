"""
AppCook — couche base de données (refonte v2)
Adapté de db_reference/db.py :
  - Suppression des champs cookeo_modes / cookeo_mode
  - Ajout de recipes.is_batch (BOOLEAN)
  - Ajout de recipes.origin (TEXT)
  - Ajout de la table cooking_history
  - Nouvelles fonctions : log_cook, get_recent_cooked_codes, suggest_recipe
"""
import os
import sqlite3
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# 1) Config / Connexion
# =============================================================================

DEFAULT_DB = (Path(__file__).resolve().parent / "data" / "recettes.db")
DB_FILE = os.environ.get("APPCOOK_DB_FILE", str(DEFAULT_DB))
DB_FILE = str(Path(DB_FILE).expanduser().resolve())


def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# =============================================================================
# 2) Migrations / ensure_schema
# =============================================================================

def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


_ALLOWED_TABLES = {
    "recipes", "steps", "step_ingredients", "recipe_ingredients",
    "ingredient_catalog", "ingredient_alias", "unit_alias",
    "cooking_history", "shopping_list", "shopping_list_items",
    "shopping_bundles", "shopping_bundle_items", "user_settings",
}

def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    if table not in _ALLOWED_TABLES:
        return False
    if not table_exists(conn, table):
        return False
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def create_tables_if_needed(conn: sqlite3.Connection) -> None:
    """Schéma v2 : sans champs Cookeo, avec is_batch et origin."""
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS recipes (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          code          TEXT    NOT NULL UNIQUE,
          name          TEXT    NOT NULL,
          category      TEXT,
          origin        TEXT,
          base_servings REAL    NOT NULL,
          is_batch      INTEGER NOT NULL DEFAULT 0,
          notes         TEXT
        );

        CREATE TABLE IF NOT EXISTS ingredient_catalog (
          id   INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS recipe_ingredients (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          recipe_id     INTEGER NOT NULL,
          ingredient_id INTEGER NOT NULL,
          qty           REAL,
          unit          TEXT,
          optional      INTEGER NOT NULL DEFAULT 0,
          notes         TEXT,
          FOREIGN KEY (recipe_id)     REFERENCES recipes(id)            ON DELETE CASCADE,
          FOREIGN KEY (ingredient_id) REFERENCES ingredient_catalog(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS steps (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          recipe_id   INTEGER NOT NULL,
          step_no     INTEGER NOT NULL,
          title       TEXT,
          instruction TEXT    NOT NULL,
          time_min    REAL,
          FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
          UNIQUE(recipe_id, step_no)
        );

        CREATE TABLE IF NOT EXISTS step_ingredients (
          id                   INTEGER PRIMARY KEY AUTOINCREMENT,
          step_id              INTEGER NOT NULL,
          recipe_ingredient_id INTEGER NOT NULL,
          FOREIGN KEY (step_id)              REFERENCES steps(id)             ON DELETE CASCADE,
          FOREIGN KEY (recipe_ingredient_id) REFERENCES recipe_ingredients(id) ON DELETE CASCADE,
          UNIQUE(step_id, recipe_ingredient_id)
        );

        CREATE TABLE IF NOT EXISTS cooking_history (
          id        INTEGER PRIMARY KEY AUTOINCREMENT,
          recipe_id INTEGER NOT NULL,
          cooked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        );
        """
    )


def ensure_catalog_columns(conn: sqlite3.Connection) -> None:
    """Migrations progressives sur ingredient_catalog."""
    for col, definition in [
        ("show_qty_in_list", "INTEGER NOT NULL DEFAULT 1"),
        ("norm_name",        "TEXT"),
        ("default_unit",     "TEXT"),
        ("category",         "TEXT"),
    ]:
        if not column_exists(conn, "ingredient_catalog", col):
            conn.execute(f"ALTER TABLE ingredient_catalog ADD COLUMN {col} {definition}")


def ensure_recipe_columns(conn: sqlite3.Connection) -> None:
    """Migrations : ajout de is_batch et origin sur une DB existante."""
    for col, definition in [
        ("is_batch", "INTEGER NOT NULL DEFAULT 0"),
        ("origin",   "TEXT"),
    ]:
        if not column_exists(conn, "recipes", col):
            conn.execute(f"ALTER TABLE recipes ADD COLUMN {col} {definition}")


def create_aux_tables_if_needed(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingredient_alias (
          id              INTEGER PRIMARY KEY AUTOINCREMENT,
          ingredient_id   INTEGER NOT NULL,
          alias_name      TEXT    NOT NULL,
          alias_norm_name TEXT    NOT NULL,
          FOREIGN KEY (ingredient_id) REFERENCES ingredient_catalog(id) ON DELETE CASCADE,
          UNIQUE(alias_norm_name)
        );

        CREATE TABLE IF NOT EXISTS unit_alias (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          alias      TEXT NOT NULL,
          alias_norm TEXT NOT NULL UNIQUE,
          unit       TEXT NOT NULL
        );
        """
    )


def create_shopping_tables(conn: sqlite3.Connection) -> None:
    """Tables v2 : bundles, liste de courses persistante, settings, stats."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS shopping_bundles (
          id       INTEGER PRIMARY KEY AUTOINCREMENT,
          name     TEXT    NOT NULL,
          icon     TEXT    DEFAULT '🛒',
          position INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS shopping_bundle_items (
          id        INTEGER PRIMARY KEY AUTOINCREMENT,
          bundle_id INTEGER NOT NULL,
          name      TEXT    NOT NULL,
          qty       REAL,
          unit      TEXT,
          category  TEXT    DEFAULT 'Divers',
          position  INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY (bundle_id) REFERENCES shopping_bundles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS shopping_list (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at TEXT    NOT NULL DEFAULT (datetime('now')),
          status     TEXT    NOT NULL DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS shopping_list_items (
          id        INTEGER PRIMARY KEY AUTOINCREMENT,
          list_id   INTEGER NOT NULL,
          name      TEXT    NOT NULL,
          qty       REAL,
          unit      TEXT,
          category  TEXT    DEFAULT 'Divers',
          checked   INTEGER NOT NULL DEFAULT 0,
          source    TEXT    DEFAULT 'recipe',
          position  INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY (list_id) REFERENCES shopping_list(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_settings (
          key   TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        """
    )


def ensure_catalog_category(conn: sqlite3.Connection) -> None:
    """Migration : ajout de la colonne category sur ingredient_catalog."""
    if not column_exists(conn, "ingredient_catalog", "category"):
        conn.execute("ALTER TABLE ingredient_catalog ADD COLUMN category TEXT")


def ensure_shopping_missing_column(conn: sqlite3.Connection) -> None:
    """Migration : ajout de la colonne missing sur shopping_list_items."""
    if not column_exists(conn, "shopping_list_items", "missing"):
        conn.execute(
            "ALTER TABLE shopping_list_items ADD COLUMN missing INTEGER NOT NULL DEFAULT 0"
        )


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Point d'entrée unique — idempotent, safe sur DB vide ou existante."""
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode=WAL;")   # meilleure concurrence lecture/écriture
    create_tables_if_needed(conn)
    ensure_catalog_columns(conn)
    ensure_catalog_category(conn)
    ensure_recipe_columns(conn)
    create_aux_tables_if_needed(conn)
    create_shopping_tables(conn)
    ensure_shopping_missing_column(conn)
    backfill_ingredient_norm_names(conn)
    refresh_ingredient_alias_norm_names(conn)
    seed_unit_aliases(conn)
    conn.commit()


# =============================================================================
# 3) Recipes
# =============================================================================

def load_recipes(conn):
    cur = conn.execute(
        """
        SELECT code, name, category, origin, base_servings, is_batch, notes
        FROM recipes
        ORDER BY name
        """
    )
    recipes = {}
    for code, name, category, origin, base_servings, is_batch, notes in cur.fetchall():
        recipes[code] = {
            "code":         code,
            "name":         name,
            "category":     category or "",
            "origin":       origin or "",
            "base_servings": float(base_servings),
            "is_batch":     bool(is_batch),
            "notes":        notes or "",
        }
    return recipes


def load_recipes_filtered(conn, time_max: Optional[int] = None, is_batch: Optional[bool] = None,
                          category: Optional[str] = None, origin: Optional[str] = None):
    """
    Retourne les recettes avec leur temps total calculé depuis les steps.
    time_max : durée maximale en minutes (somme des time_min des étapes)
    """
    conditions = []
    params = []

    if is_batch is not None:
        conditions.append("r.is_batch = ?")
        params.append(1 if is_batch else 0)
    if category:
        conditions.append("LOWER(r.category) = LOWER(?)")
        params.append(category)
    if origin:
        conditions.append("LOWER(r.origin) = LOWER(?)")
        params.append(origin)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = conn.execute(
        f"""
        SELECT r.code, r.name, r.category, r.origin, r.base_servings, r.is_batch,
               COALESCE(SUM(s.time_min), 0) as total_time
        FROM recipes r
        LEFT JOIN steps s ON s.recipe_id = r.id
        {where}
        GROUP BY r.id
        ORDER BY r.name
        """,
        params,
    ).fetchall()

    result = []
    for code, name, category, origin, base_servings, is_batch, total_time in rows:
        if time_max is not None and total_time and total_time > time_max:
            continue
        result.append({
            "code":         code,
            "name":         name,
            "category":     category or "",
            "origin":       origin or "",
            "base_servings": float(base_servings),
            "is_batch":     bool(is_batch),
            "total_time":   float(total_time) if total_time else None,
        })
    return result


def get_recipe_id_by_code(conn, code: str):
    row = conn.execute("SELECT id FROM recipes WHERE code = ?", (code,)).fetchone()
    return row[0] if row else None


def get_recipe_detail(conn, code: str) -> Optional[Dict]:
    """Retourne la recette complète avec steps + ingrédients."""
    row = conn.execute(
        "SELECT id, code, name, category, origin, base_servings, is_batch, notes FROM recipes WHERE code = ?",
        (code,),
    ).fetchone()
    if not row:
        return None

    recipe_id, code, name, category, origin, base_servings, is_batch, notes = row

    steps = conn.execute(
        "SELECT id, step_no, title, instruction, time_min FROM steps WHERE recipe_id = ? ORDER BY step_no",
        (recipe_id,),
    ).fetchall()

    steps_data = []
    for step_id, step_no, title, instruction, time_min in steps:
        step_ings = conn.execute(
            """
            SELECT ic.name, ri.qty, ri.unit
            FROM step_ingredients si
            JOIN recipe_ingredients ri ON ri.id = si.recipe_ingredient_id
            JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
            WHERE si.step_id = ?
            ORDER BY ic.name
            """,
            (step_id,),
        ).fetchall()
        steps_data.append({
            "id":          step_id,
            "step_no":     step_no,
            "title":       title or "",
            "instruction": instruction,
            "time_min":    time_min,
            "ingredients": [{"name": n, "qty": q, "unit": u} for n, q, u in step_ings],
        })

    all_ingredients = conn.execute(
        """
        SELECT ic.name, ri.qty, ri.unit, ri.optional, ri.notes
        FROM recipe_ingredients ri
        JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
        WHERE ri.recipe_id = ?
        ORDER BY ic.name
        """,
        (recipe_id,),
    ).fetchall()

    total_time = conn.execute(
        "SELECT COALESCE(SUM(time_min), 0) FROM steps WHERE recipe_id = ?", (recipe_id,)
    ).fetchone()[0]

    return {
        "code":         code,
        "name":         name,
        "category":     category or "",
        "origin":       origin or "",
        "base_servings": float(base_servings),
        "is_batch":     bool(is_batch),
        "notes":        notes or "",
        "total_time":   float(total_time) if total_time else None,
        "ingredients":  [
            {"name": n, "qty": q, "unit": u, "optional": bool(opt), "notes": note or ""}
            for n, q, u, opt, note in all_ingredients
        ],
        "steps": steps_data,
    }


def make_unique_code(conn, base_code: str) -> str:
    code = base_code
    i = 2
    while conn.execute("SELECT 1 FROM recipes WHERE code=? LIMIT 1", (code,)).fetchone():
        code = f"{base_code}_{i}"
        i += 1
    return code


def insert_recipe(conn, code: str, name: str, category: str, origin: str,
                  base_servings: float, is_batch: bool, notes: str):
    conn.execute(
        """
        INSERT INTO recipes (code, name, category, origin, base_servings, is_batch, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (code, name, category, origin, float(base_servings), 1 if is_batch else 0, notes),
    )
    conn.commit()


def update_recipe_by_code(conn, code: str, name: str, category: str, origin: str,
                          base_servings: float, is_batch: bool, notes: str):
    conn.execute(
        """
        UPDATE recipes
        SET name=?, category=?, origin=?, base_servings=?, is_batch=?, notes=?
        WHERE code=?
        """,
        (name, category, origin, float(base_servings), 1 if is_batch else 0, notes, code),
    )
    conn.commit()


def delete_recipe_by_code(conn, code: str):
    rid = get_recipe_id_by_code(conn, code)
    if rid is None:
        return
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (rid,))
        conn.execute("DELETE FROM steps WHERE recipe_id = ?", (rid,))
        conn.execute("DELETE FROM recipes WHERE id = ?", (rid,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# =============================================================================
# 4) Cooking history
# =============================================================================

def log_cook(conn, recipe_code: str) -> None:
    """Enregistre une session de cuisine. Appelé automatiquement à la fin du Focus Mode."""
    recipe_id = get_recipe_id_by_code(conn, recipe_code)
    if recipe_id is None:
        raise ValueError(f"Recette introuvable : {recipe_code}")
    conn.execute(
        "INSERT INTO cooking_history (recipe_id) VALUES (?)", (recipe_id,)
    )
    conn.commit()


def get_recent_cooked_codes(conn, days: int = 7) -> List[str]:
    """Retourne les codes des recettes cuisinées dans les X derniers jours."""
    since = (datetime.now() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        """
        SELECT DISTINCT r.code
        FROM cooking_history ch
        JOIN recipes r ON r.id = ch.recipe_id
        WHERE ch.cooked_at >= ?
        """,
        (since,),
    ).fetchall()
    return [r[0] for r in rows]


def get_cooking_history(conn, limit: int = 20) -> List[Dict]:
    rows = conn.execute(
        """
        SELECT r.code, r.name, ch.cooked_at
        FROM cooking_history ch
        JOIN recipes r ON r.id = ch.recipe_id
        ORDER BY ch.cooked_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [{"code": code, "name": name, "cooked_at": cooked_at} for code, name, cooked_at in rows]


# =============================================================================
# 5) Suggestion intelligente
# =============================================================================

def suggest_recipe(conn, time_max: Optional[int] = None) -> Optional[Dict]:
    """
    Suggère une recette :
    1. Filtre par time_max si fourni
    2. Exclut les recettes cuisinées dans les 7 derniers jours
    3. Priorise les recettes batch si aucune batch récente
    4. Retourne une recette aléatoire parmi les candidats
    """
    recent_codes = get_recent_cooked_codes(conn, days=7)
    recent_batch_codes = get_recent_cooked_codes(conn, days=14)

    # Filtrer les candidats
    candidates = load_recipes_filtered(conn, time_max=time_max)
    candidates = [r for r in candidates if r["code"] not in recent_codes]

    if not candidates:
        # Si tout a été cuisiné récemment, on ignore l'historique
        candidates = load_recipes_filtered(conn, time_max=time_max)

    if not candidates:
        return None

    # Prioriser batch si pas de batch récent
    recent_batch = [c for c in candidates if c["code"] in recent_batch_codes]
    batch_candidates = [c for c in candidates if c["is_batch"]]

    if batch_candidates and not recent_batch:
        import random
        return random.choice(batch_candidates)

    import random
    return random.choice(candidates)


# =============================================================================
# 6) Ingredients catalog
# =============================================================================

def search_ingredients(conn, query: str, limit: int = 20):
    q = (query or "").strip().lower()
    if not q:
        return conn.execute(
            "SELECT id, name FROM ingredient_catalog ORDER BY name LIMIT ?", (limit,)
        ).fetchall()
    like = f"%{q}%"
    return conn.execute(
        """
        SELECT id, name FROM ingredient_catalog
        WHERE LOWER(name) LIKE ?
        ORDER BY
          CASE WHEN LOWER(name) = ? THEN 0
               WHEN LOWER(name) LIKE ? THEN 1
               ELSE 2 END,
          name
        LIMIT ?
        """,
        (like, q, f"{q}%", limit),
    ).fetchall()


def get_or_create_ingredient_id(conn, name: str):
    name = name.strip()
    if not name:
        return None
    existing_id = resolve_ingredient_id_by_name(conn, name)
    if existing_id:
        return existing_id
    norm = normalize_ingredient_name(name)
    cur = conn.execute(
        "INSERT INTO ingredient_catalog (name, norm_name) VALUES (?, ?)", (name, norm)
    )
    conn.commit()
    return cur.lastrowid


def list_catalog(conn):
    return conn.execute(
        """
        SELECT id, name, COALESCE(default_unit,''), COALESCE(show_qty_in_list,1),
               COALESCE(norm_name,''), COALESCE(category,'')
        FROM ingredient_catalog ORDER BY name
        """
    ).fetchall()


def set_catalog_show_qty(conn, ingredient_id: int, show_qty: int):
    conn.execute(
        "UPDATE ingredient_catalog SET show_qty_in_list=? WHERE id=?",
        (1 if int(show_qty) else 0, int(ingredient_id)),
    )
    conn.commit()


def set_catalog_default_unit(conn, ingredient_id: int, default_unit: str):
    conn.execute(
        "UPDATE ingredient_catalog SET default_unit=? WHERE id=?",
        ((default_unit or "").strip(), int(ingredient_id)),
    )
    conn.commit()


def set_catalog_category(conn, ingredient_id: int, category: str):
    conn.execute(
        "UPDATE ingredient_catalog SET category=? WHERE id=?",
        ((category or "").strip(), int(ingredient_id)),
    )
    conn.commit()


def merge_ingredients(conn, canonical_id: int, duplicate_ids: List[int]) -> int:
    dupes = [int(i) for i in duplicate_ids if int(i) != int(canonical_id)]
    if not dupes:
        return 0
    placeholders = ",".join(["?"] * len(dupes))
    params = [int(canonical_id)] + dupes
    try:
        conn.execute("BEGIN")
        conn.execute(f"UPDATE ingredient_alias SET ingredient_id=? WHERE ingredient_id IN ({placeholders})", params)
        conn.execute(f"UPDATE recipe_ingredients SET ingredient_id=? WHERE ingredient_id IN ({placeholders})", params)
        conn.execute(f"DELETE FROM ingredient_catalog WHERE id IN ({placeholders})", dupes)
        conn.commit()
        return len(dupes)
    except Exception:
        conn.rollback()
        raise


def get_show_qty_map(conn):
    return dict(
        conn.execute("SELECT name, COALESCE(show_qty_in_list,1) FROM ingredient_catalog").fetchall()
    )


# =============================================================================
# 7) Recipe ingredients
# =============================================================================

def list_recipe_ingredients(conn, recipe_id: int):
    return conn.execute(
        """
        SELECT ri.id, ic.id, ic.name, ri.qty, ri.unit, ri.optional, COALESCE(ri.notes,'')
        FROM recipe_ingredients ri
        JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
        WHERE ri.recipe_id = ?
        ORDER BY ic.name
        """,
        (recipe_id,),
    ).fetchall()


def add_recipe_ingredient(conn, recipe_id: int, ingredient_id: int, qty: float,
                          unit: str, optional: int, notes: str):
    conn.execute(
        """
        INSERT INTO recipe_ingredients (recipe_id, ingredient_id, qty, unit, optional, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (int(recipe_id), int(ingredient_id), float(qty), unit, int(optional), notes),
    )
    conn.commit()


def update_recipe_ingredient(conn, ri_id: int, qty: float, unit: str, optional: int, notes: str):
    conn.execute(
        "UPDATE recipe_ingredients SET qty=?, unit=?, optional=?, notes=? WHERE id=?",
        (float(qty), unit, int(optional), notes, int(ri_id)),
    )
    conn.commit()


def delete_recipe_ingredient(conn, ri_id: int):
    conn.execute("DELETE FROM recipe_ingredients WHERE id=?", (ri_id,))
    conn.commit()


# =============================================================================
# 8) Steps
# =============================================================================

def list_steps_by_recipe(conn, recipe_id: int):
    return conn.execute(
        "SELECT id, step_no, COALESCE(title,''), instruction, time_min FROM steps WHERE recipe_id=? ORDER BY step_no",
        (recipe_id,),
    ).fetchall()


def insert_step(conn, recipe_id: int, step_no: int, title: str, instruction: str, time_min):
    conn.execute(
        "INSERT INTO steps (recipe_id, step_no, title, instruction, time_min) VALUES (?, ?, ?, ?, ?)",
        (int(recipe_id), int(step_no), title, instruction, time_min),
    )
    conn.commit()


def update_step(conn, step_id: int, step_no: int, title: str, instruction: str, time_min):
    conn.execute(
        "UPDATE steps SET step_no=?, title=?, instruction=?, time_min=? WHERE id=?",
        (int(step_no), title, instruction, time_min, int(step_id)),
    )
    conn.commit()


def delete_step(conn, step_id: int):
    conn.execute("DELETE FROM steps WHERE id=?", (int(step_id),))
    conn.commit()


# =============================================================================
# 9) Step ingredients
# =============================================================================

def get_step_ingredient_ids(conn, step_id: int):
    rows = conn.execute(
        "SELECT recipe_ingredient_id FROM step_ingredients WHERE step_id=?", (int(step_id),)
    ).fetchall()
    return [r[0] for r in rows]


def save_step_ingredients(conn, step_id: int, recipe_ingredient_ids: List[int]):
    conn.execute("DELETE FROM step_ingredients WHERE step_id=?", (int(step_id),))
    conn.executemany(
        "INSERT OR IGNORE INTO step_ingredients (step_id, recipe_ingredient_id) VALUES (?, ?)",
        [(int(step_id), int(ri_id)) for ri_id in recipe_ingredient_ids],
    )
    conn.commit()


# =============================================================================
# 10) Shopping list
# =============================================================================

def aggregate_shopping_list(conn, recipe_codes: List[str], persons_map: Dict[str, float], include_optional: bool):
    """
    persons_map : { recipe_code: persons } — portions par recette.
    """
    if not recipe_codes:
        return [], []

    placeholders = ",".join(["?"] * len(recipe_codes))
    rows = conn.execute(
        f"""
        SELECT r.code, r.base_servings, ic.id, ic.name, ic.norm_name,
               ic.default_unit, COALESCE(ic.show_qty_in_list, 1),
               ri.qty, ri.unit, ri.optional
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
        WHERE r.code IN ({placeholders})
        ORDER BY r.code, ic.name
        """,
        recipe_codes,
    ).fetchall()

    alias_map = get_unit_alias_map(conn)
    items_by_key: Dict[str, Dict] = {}
    issues: List[Dict] = []

    for (code, base_servings, ingredient_id, name, norm_name,
         default_unit, show_qty, qty, unit, optional) in rows:

        if int(optional or 0) == 1 and not include_optional:
            continue

        base = float(base_servings or 1)
        persons = float(persons_map.get(code, 1))
        factor = persons / base if base else 1.0
        scaled_qty = (float(qty) if qty is not None else 0.0) * factor

        default_unit = (default_unit or "").strip()
        recipe_unit  = (unit or "").strip()

        # Si pas d'unité par défaut dans le catalogue, on utilise l'unité de la recette
        effective_unit = default_unit or recipe_unit

        if not effective_unit:
            # Ingrédient sans unité (ex: sel, poivre "au goût") — on l'inclut sans qty
            key = norm_name or f"id:{int(ingredient_id)}"
            if key not in items_by_key:
                items_by_key[key] = {"name": name, "unit": "", "qty": None, "show_qty": 0}
            continue

        if not default_unit:
            # Pas de default_unit → on prend l'unité de la recette telle quelle, sans conversion
            key = norm_name or f"id:{int(ingredient_id)}"
            if key not in items_by_key:
                items_by_key[key] = {"name": name, "unit": recipe_unit,
                                     "qty": scaled_qty, "show_qty": int(show_qty or 1)}
            else:
                items_by_key[key]["qty"] = (items_by_key[key]["qty"] or 0) + scaled_qty
            continue

        default_resolved = resolve_unit(conn, default_unit, alias_map)
        unit_resolved = resolve_unit(conn, recipe_unit, alias_map)

        if not default_resolved or unit_resolved is None:
            issues.append({"ingredient": name, "reason": "unit_error"})
            continue

        converted_qty = convert_qty(scaled_qty, unit_resolved, default_resolved)
        if converted_qty is None:
            issues.append({"ingredient": name, "reason": "unit_incompatible"})
            continue

        key = norm_name or f"id:{int(ingredient_id)}"
        if key not in items_by_key:
            items_by_key[key] = {"name": name, "unit": default_resolved,
                                 "qty": converted_qty, "show_qty": int(show_qty or 1)}
        else:
            items_by_key[key]["qty"] += converted_qty

    items = sorted(items_by_key.values(), key=lambda x: x["name"].lower())
    return items, issues


# =============================================================================
# 11) Import / Export JSON (v1.0)
# =============================================================================

SCHEMA_V1 = "appcook.recipe.v1"


def validate_recipe_json(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["Le JSON racine doit être un objet."]
    if data.get("schema_version") != SCHEMA_V1:
        errors.append(f"schema_version doit être '{SCHEMA_V1}'.")
    recipe = data.get("recipe")
    if not isinstance(recipe, dict):
        errors.append("recipe doit être un objet.")
        return False, errors
    if not isinstance(recipe.get("title"), str) or not recipe["title"].strip():
        errors.append("recipe.title est obligatoire.")
    if not isinstance(recipe.get("ingredients"), list):
        errors.append("recipe.ingredients doit être une liste.")
    else:
        for i, ing in enumerate(recipe["ingredients"]):
            if not isinstance(ing, dict):
                errors.append(f"recipe.ingredients[{i}] doit être un objet.")
            elif not isinstance(ing.get("name"), str) or not ing["name"].strip():
                errors.append(f"recipe.ingredients[{i}].name est obligatoire.")
    if not isinstance(recipe.get("steps"), list) or len(recipe.get("steps", [])) == 0:
        errors.append("recipe.steps doit être une liste non vide.")
    else:
        for i, step in enumerate(recipe["steps"]):
            if not isinstance(step, dict):
                errors.append(f"recipe.steps[{i}] doit être un objet.")
            elif not isinstance(step.get("text"), str) or not step["text"].strip():
                errors.append(f"recipe.steps[{i}].text est obligatoire.")
    return (len(errors) == 0), errors


def import_recipe_from_json(data: Dict[str, Any], on_code_conflict: str = "rename") -> int:
    ok, errors = validate_recipe_json(data)
    if not ok:
        raise ValueError("JSON invalide:\n- " + "\n- ".join(errors))

    r = data["recipe"]
    title = r["title"].strip()
    base_servings_f = float(r.get("servings") or 1.0)
    is_batch = bool(r.get("is_batch", False))
    category = r.get("category", "")
    origin = r.get("origin", "")

    notes_lines = []
    if r.get("source"):
        notes_lines.append(f"Source: {r['source']}")
    if isinstance(r.get("tags"), list):
        notes_lines.append("Tags: " + ", ".join(str(t) for t in r["tags"] if str(t).strip()))
    if r.get("notes"):
        notes_lines.append(r["notes"])
    final_notes = "\n".join(notes_lines) or None

    desired_code = _slugify_code(title)
    conn = get_conn()
    try:
        conn.execute("BEGIN")
        final_code = _resolve_recipe_code(conn, desired_code, mode=on_code_conflict)
        recipe_id = conn.execute(
            "INSERT INTO recipes (code, name, category, origin, base_servings, is_batch, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (final_code, title, category, origin, base_servings_f, 1 if is_batch else 0, final_notes),
        ).lastrowid

        name_to_ri_id: Dict[str, int] = {}
        for ing in r.get("ingredients", []):
            name = ing["name"].strip()
            unit = ing.get("unit", "")
            ingredient_id = _get_or_create_ingredient_catalog(
                conn, name,
                show_qty_in_list=ing.get("show_qty_in_list"),
                default_unit=unit,
            )
            ri_id = conn.execute(
                "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, qty, unit, optional) VALUES (?, ?, ?, ?, 0)",
                (recipe_id, ingredient_id, ing.get("qty"), unit),
            ).lastrowid
            name_to_ri_id[name.lower()] = ri_id

        for idx, step in enumerate(r.get("steps", []), start=1):
            time_min = float(step["time_sec"]) / 60.0 if step.get("time_sec") is not None else None
            step_id = conn.execute(
                "INSERT INTO steps (recipe_id, step_no, title, instruction, time_min) VALUES (?, ?, ?, ?, ?)",
                (recipe_id, idx, step.get("title"), step["text"].strip(), time_min),
            ).lastrowid

            for jing in (step.get("ingredients", []) or []):
                ri_id = name_to_ri_id.get(jing["name"].strip().lower())
                if ri_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO step_ingredients (step_id, recipe_ingredient_id) VALUES (?, ?)",
                        (step_id, ri_id),
                    )

        conn.commit()
        return recipe_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def export_recipe_to_json(conn, recipe_id: int) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT name, base_servings, is_batch, category, origin, notes FROM recipes WHERE id=?", (recipe_id,)
    ).fetchone()
    if not row:
        raise ValueError(f"Recette introuvable (id={recipe_id})")
    name, base_servings, is_batch, category, origin, notes = row

    ing_rows = conn.execute(
        """
        SELECT ic.name, ri.qty, ri.unit, COALESCE(ic.show_qty_in_list,1)
        FROM recipe_ingredients ri JOIN ingredient_catalog ic ON ic.id=ri.ingredient_id
        WHERE ri.recipe_id=? ORDER BY ic.name
        """, (recipe_id,),
    ).fetchall()

    step_rows = conn.execute(
        "SELECT id, step_no, title, instruction, time_min FROM steps WHERE recipe_id=? ORDER BY step_no",
        (recipe_id,),
    ).fetchall()

    step_ings_map: Dict[int, List] = defaultdict(list)
    for step_id, sname, sq, su in conn.execute(
        """
        SELECT si.step_id, ic.name, ri.qty, ri.unit
        FROM step_ingredients si JOIN recipe_ingredients ri ON ri.id=si.recipe_ingredient_id
        JOIN ingredient_catalog ic ON ic.id=ri.ingredient_id WHERE ri.recipe_id=?
        """, (recipe_id,),
    ).fetchall():
        step_ings_map[int(step_id)].append({"name": sname, "qty": sq, "unit": su or ""})

    steps = []
    for sid, step_no, title, instruction, time_min in step_rows:
        s: Dict = {"text": instruction}
        if title:
            s["title"] = title
        if time_min is not None:
            s["time_sec"] = int(round(float(time_min) * 60))
        if step_ings_map.get(int(sid)):
            s["ingredients"] = step_ings_map[int(sid)]
        steps.append(s)

    recipe: Dict = {
        "title":        name,
        "servings":     base_servings,
        "is_batch":     bool(is_batch),
        "category":     category or "",
        "origin":       origin or "",
        "ingredients":  [{"name": n, "qty": q, "unit": u or "", "show_qty_in_list": bool(sq)} for n, q, u, sq in ing_rows],
        "steps":        steps,
    }
    if notes:
        recipe["notes"] = notes
    return {"schema_version": SCHEMA_V1, "recipe": recipe}


def export_recipe_to_json_by_code(conn, code: str) -> Dict[str, Any]:
    recipe_id = get_recipe_id_by_code(conn, code)
    if recipe_id is None:
        raise ValueError(f"Recette introuvable (code={code})")
    return export_recipe_to_json(conn, recipe_id)


# =============================================================================
# 12) Normalization helpers
# =============================================================================

PLURAL_EXCEPTIONS = {"riz", "maïs", "ananas", "pois"}
UNIT_CANONICAL = {"g", "kg", "ml", "l", "cl", "pièce", "gousse", "tranche", "cube", "pincée", "cs", "cc"}

UNIT_ALIAS_SEED = [
    ("g", "g"), ("gr", "g"), ("grs", "g"), ("kg", "kg"), ("kgs", "kg"),
    ("ml", "ml"), ("l", "l"), ("litre", "l"), ("litres", "l"), ("cl", "cl"),
    ("pc", "pièce"), ("piece", "pièce"), ("pieces", "pièce"), ("pièce", "pièce"),
    ("pièces", "pièce"), ("pcs", "pièce"), ("pincee", "pincée"), ("pincees", "pincée"),
    ("pincée", "pincée"), ("pincées", "pincée"), ("tranches", "tranche"),
    ("cs", "cs"), ("cc", "cc"), ("c a soupe", "cs"), ("c a cafe", "cc"),
    ("c. à soupe", "cs"), ("c. à café", "cc"),
]

UNIT_FACTORS = {
    "g": ("weight", 1.0), "kg": ("weight", 1000.0),
    "ml": ("volume", 1.0), "cl": ("volume", 10.0), "l": ("volume", 1000.0),
    "pièce": ("piece", 1.0), "gousse": ("piece", 1.0), "tranche": ("piece", 1.0),
    "cube": ("piece", 1.0), "pincée": ("piece", 1.0), "cs": ("piece", 1.0), "cc": ("piece", 1.0),
}


def _strip_accents(text: str) -> str:
    text = text.replace("œ", "oe").replace("æ", "ae")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normalize_ingredient_name(name: str) -> str:
    s = _strip_accents((name or "").strip().lower())
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.split(r"\s+/(?:\s+|$)|\s+ou\s+", s, maxsplit=1)[0]
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        tokens = []
        for tok in s.split(" "):
            if len(tok) > 3 and tok.endswith("s") and tok not in PLURAL_EXCEPTIONS:
                tok = tok[:-1]
            tokens.append(tok)
        s = " ".join(tokens)
    return s


def normalize_unit_alias(unit: str) -> str:
    s = _strip_accents((unit or "").strip().lower())
    return re.sub(r"\s+", "", s.replace(".", ""))


CANONICAL_UNIT_BY_NORM = {normalize_unit_alias(u): u for u in UNIT_CANONICAL}


def resolve_ingredient_id_by_name(conn, name: str):
    norm = normalize_ingredient_name(name)
    if not norm:
        return None
    row = conn.execute(
        "SELECT ingredient_id FROM ingredient_alias WHERE alias_norm_name=? LIMIT 1", (norm,)
    ).fetchone()
    if row:
        return row[0]
    row = conn.execute(
        "SELECT id FROM ingredient_catalog WHERE norm_name=? LIMIT 1", (norm,)
    ).fetchone()
    return row[0] if row else None


def get_unit_alias_map(conn) -> Dict[str, str]:
    return dict(conn.execute("SELECT alias_norm, unit FROM unit_alias").fetchall())


def resolve_unit(conn, unit: str, alias_map: Optional[Dict[str, str]] = None) -> Optional[str]:
    raw = (unit or "").strip()
    if raw == "":
        return ""
    norm = normalize_unit_alias(raw)
    canonical = CANONICAL_UNIT_BY_NORM.get(norm)
    if canonical:
        return canonical
    if alias_map is None:
        alias_map = get_unit_alias_map(conn)
    return alias_map.get(norm)


def convert_qty(qty: float, from_unit: str, to_unit: str) -> Optional[float]:
    if from_unit == to_unit:
        return qty
    from_group, from_factor = UNIT_FACTORS.get(from_unit, (None, None))
    to_group, to_factor = UNIT_FACTORS.get(to_unit, (None, None))
    if from_group is None or to_group is None or from_group != to_group:
        return None
    return qty * (from_factor / to_factor)


def backfill_ingredient_norm_names(conn) -> None:
    if not column_exists(conn, "ingredient_catalog", "norm_name"):
        return
    rows = conn.execute("SELECT id, name FROM ingredient_catalog").fetchall()
    if rows:
        conn.executemany(
            "UPDATE ingredient_catalog SET norm_name=? WHERE id=?",
            [(normalize_ingredient_name(name), ing_id) for ing_id, name in rows],
        )


def refresh_ingredient_alias_norm_names(conn) -> None:
    if not table_exists(conn, "ingredient_alias"):
        return
    rows = conn.execute("SELECT id, alias_name FROM ingredient_alias").fetchall()
    if rows:
        conn.executemany(
            "UPDATE ingredient_alias SET alias_norm_name=? WHERE id=?",
            [(normalize_ingredient_name(name), alias_id) for alias_id, name in rows],
        )


def seed_unit_aliases(conn) -> None:
    if not table_exists(conn, "unit_alias"):
        return
    conn.executemany(
        "INSERT OR IGNORE INTO unit_alias (alias, alias_norm, unit) VALUES (?, ?, ?)",
        [(alias, normalize_unit_alias(alias), unit) for alias, unit in UNIT_ALIAS_SEED],
    )


# =============================================================================
# Helpers internes
# =============================================================================

# =============================================================================
# 17) Full recipe save (create + replace)
# =============================================================================

def _get_or_create_ingredient_id_tx(conn, name: str) -> Optional[int]:
    """Version sans commit — à utiliser dans une transaction ouverte."""
    name = name.strip()
    if not name:
        return None
    existing_id = resolve_ingredient_id_by_name(conn, name)
    if existing_id:
        return existing_id
    norm = normalize_ingredient_name(name)
    cur = conn.execute(
        "INSERT INTO ingredient_catalog (name, norm_name) VALUES (?, ?)", (name, norm)
    )
    return cur.lastrowid


def replace_recipe_full(
    conn,
    code: str,
    name: str, category: str, origin: str,
    base_servings: float, is_batch: bool, notes: str,
    ingredients: List[Dict],
    steps: List[Dict],
) -> int:
    """
    Remplace entièrement une recette existante : métadonnées + ingrédients + étapes.
    ingredients : [{'name', 'qty', 'unit', 'optional', 'notes'}]
    steps       : [{'step_no', 'title', 'instruction', 'time_min', 'ingredient_names': [...]}]
    Opération atomique — rollback complet en cas d'erreur.
    """
    recipe_id = get_recipe_id_by_code(conn, code)
    if recipe_id is None:
        raise ValueError(f"Recette introuvable : {code}")
    try:
        # 1) Mise à jour des métadonnées
        conn.execute(
            """UPDATE recipes
               SET name=?, category=?, origin=?, base_servings=?, is_batch=?, notes=?
               WHERE code=?""",
            (name, category or "", origin or "", float(base_servings),
             1 if is_batch else 0, notes or "", code),
        )
        # 2) Suppression des étapes et ingrédients existants
        conn.execute(
            "DELETE FROM step_ingredients WHERE step_id IN "
            "(SELECT id FROM steps WHERE recipe_id=?)", (recipe_id,)
        )
        conn.execute("DELETE FROM steps WHERE recipe_id=?", (recipe_id,))
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id=?", (recipe_id,))

        # 3) Insertion des ingrédients
        name_to_ri_id: Dict[str, int] = {}
        for ing in ingredients:
            ing_name = (ing.get("name") or "").strip()
            if not ing_name:
                continue
            ingredient_id = _get_or_create_ingredient_id_tx(conn, ing_name)
            if ingredient_id is None:
                continue
            qty_val = ing.get("qty")
            if qty_val is not None:
                try:
                    qty_val = float(qty_val)
                except (TypeError, ValueError):
                    qty_val = None
            ri_id = conn.execute(
                """INSERT INTO recipe_ingredients
                   (recipe_id, ingredient_id, qty, unit, optional, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (recipe_id, ingredient_id, qty_val,
                 ing.get("unit", "") or "",
                 1 if ing.get("optional") else 0,
                 ing.get("notes", "") or ""),
            ).lastrowid
            name_to_ri_id[ing_name.lower()] = ri_id

        # 4) Insertion des étapes
        for idx, step in enumerate(steps, start=1):
            instruction = (step.get("instruction") or "").strip()
            if not instruction:
                continue
            time_min_val = step.get("time_min")
            if time_min_val is not None:
                try:
                    time_min_val = float(time_min_val)
                    if time_min_val <= 0:
                        time_min_val = None
                except (TypeError, ValueError):
                    time_min_val = None
            step_id = conn.execute(
                """INSERT INTO steps (recipe_id, step_no, title, instruction, time_min)
                   VALUES (?, ?, ?, ?, ?)""",
                (recipe_id, idx, step.get("title", "") or "",
                 instruction, time_min_val),
            ).lastrowid
            for ing_name in (step.get("ingredient_names") or []):
                ri_id = name_to_ri_id.get(ing_name.strip().lower())
                if ri_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO step_ingredients "
                        "(step_id, recipe_ingredient_id) VALUES (?, ?)",
                        (step_id, ri_id),
                    )

        conn.commit()
        return recipe_id
    except Exception:
        conn.rollback()
        raise


def _slugify_code(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_") or "recette"


def _resolve_recipe_code(conn, desired_code: str, mode: str) -> str:
    if not conn.execute("SELECT 1 FROM recipes WHERE code=? LIMIT 1", (desired_code,)).fetchone():
        return desired_code
    if mode == "error":
        raise ValueError(f"Code '{desired_code}' déjà utilisé.")
    base = f"{desired_code}_import"
    candidate, n = base, 2
    while conn.execute("SELECT 1 FROM recipes WHERE code=? LIMIT 1", (candidate,)).fetchone():
        candidate = f"{base}{n}"
        n += 1
    return candidate


# =============================================================================
# 13) Shopping bundles
# =============================================================================

def list_bundles(conn) -> List[Dict]:
    bundles = conn.execute(
        "SELECT id, name, icon, position FROM shopping_bundles ORDER BY position, id"
    ).fetchall()
    result = []
    for bid, name, icon, position in bundles:
        items = conn.execute(
            """
            SELECT id, name, qty, unit, category, position
            FROM shopping_bundle_items WHERE bundle_id=? ORDER BY position, id
            """,
            (bid,),
        ).fetchall()
        result.append({
            "id": bid,
            "name": name,
            "icon": icon or "🛒",
            "position": position,
            "items": [
                {"id": i[0], "name": i[1], "qty": i[2], "unit": i[3] or "",
                 "category": i[4] or "Divers", "position": i[5]}
                for i in items
            ],
        })
    return result


def create_bundle(conn, name: str, icon: str = "🛒", position: int = 0) -> int:
    cur = conn.execute(
        "INSERT INTO shopping_bundles (name, icon, position) VALUES (?, ?, ?)",
        (name, icon, position),
    )
    conn.commit()
    return cur.lastrowid


def update_bundle(conn, bundle_id: int, name: str, icon: str) -> None:
    conn.execute(
        "UPDATE shopping_bundles SET name=?, icon=? WHERE id=?",
        (name, icon, int(bundle_id)),
    )
    conn.commit()


def delete_bundle(conn, bundle_id: int) -> None:
    conn.execute("DELETE FROM shopping_bundles WHERE id=?", (int(bundle_id),))
    conn.commit()


def add_bundle_item(conn, bundle_id: int, name: str, qty, unit: str,
                    category: str, position: int = 0) -> int:
    cur = conn.execute(
        """
        INSERT INTO shopping_bundle_items (bundle_id, name, qty, unit, category, position)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (int(bundle_id), name, qty, unit, category, position),
    )
    conn.commit()
    return cur.lastrowid


def update_bundle_item(conn, item_id: int, name: str, qty, unit: str, category: str) -> None:
    conn.execute(
        "UPDATE shopping_bundle_items SET name=?, qty=?, unit=?, category=? WHERE id=?",
        (name, qty, unit, category, int(item_id)),
    )
    conn.commit()


def delete_bundle_item(conn, item_id: int) -> None:
    conn.execute("DELETE FROM shopping_bundle_items WHERE id=?", (int(item_id),))
    conn.commit()


# =============================================================================
# 14) Active shopping list (persistante, sync-ready)
# =============================================================================

def get_active_list(conn) -> Optional[Dict]:
    """Retourne la liste active avec items groupés par catégorie."""
    row = conn.execute(
        "SELECT id, created_at FROM shopping_list WHERE status='active' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    list_id, created_at = row
    items = conn.execute(
        """
        SELECT id, name, qty, unit, category, checked, source, COALESCE(missing, 0)
        FROM shopping_list_items
        WHERE list_id=? ORDER BY category, position, id
        """,
        (list_id,),
    ).fetchall()
    # Progression : checked OU missing compte comme "fait"
    total = len(items)
    done = sum(1 for i in items if i[5] or i[7])
    return {
        "id": list_id,
        "created_at": created_at,
        "total": total,
        "checked": done,
        "items": [
            {
                "id": i[0], "name": i[1], "qty": i[2], "unit": i[3] or "",
                "category": i[4] or "Divers", "checked": bool(i[5]),
                "source": i[6], "missing": bool(i[7]),
            }
            for i in items
        ],
    }


def generate_shopping_list(
    conn,
    recipe_codes: List[str],
    persons_map: Dict[str, float],
    bundle_id: Optional[int],
    manual_items: Optional[List[Dict]],
    include_optional: bool = False,
) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Génère une nouvelle liste de courses persistante :
    1. Agrège les ingrédients des recettes sélectionnées
    2. Ajoute les items du bundle choisi
    3. Ajoute les items manuels
    Retourne (liste_active, issues).
    """
    # Récupérer les articles manquants de la DERNIÈRE liste (active ou terminée)
    missing_items: List[Dict] = []
    prev = conn.execute(
        "SELECT id FROM shopping_list ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if prev:
        missing_rows = conn.execute(
            """
            SELECT name, qty, unit, category FROM shopping_list_items
            WHERE list_id=? AND missing=1
            """,
            (prev[0],),
        ).fetchall()
        missing_items = [
            {"name": r[0], "qty": r[1], "unit": r[2] or "", "category": r[3] or "Divers"}
            for r in missing_rows
        ]

    # Clore l'ancienne liste active si elle existe
    conn.execute("UPDATE shopping_list SET status='done' WHERE status='active'")

    # Créer la nouvelle liste
    list_id = conn.execute(
        "INSERT INTO shopping_list (status) VALUES ('active')"
    ).lastrowid

    issues: List[Dict] = []
    pos = 0

    # --- Ingrédients des recettes ---
    if recipe_codes:
        items, recipe_issues = aggregate_shopping_list(conn, recipe_codes, persons_map, include_optional)
        issues.extend(recipe_issues)
        for item in items:
            # Récupérer la catégorie depuis le catalogue
            cat_row = conn.execute(
                "SELECT category FROM ingredient_catalog WHERE name=?", (item["name"],)
            ).fetchone()
            category = (cat_row[0] if cat_row and cat_row[0] else "Épicerie")
            qty = item["qty"] if item.get("show_qty", 1) else None
            conn.execute(
                """
                INSERT INTO shopping_list_items (list_id, name, qty, unit, category, source, position)
                VALUES (?, ?, ?, ?, ?, 'recipe', ?)
                """,
                (list_id, item["name"], qty, item["unit"], category, pos),
            )
            pos += 1

    # --- Items du bundle ---
    if bundle_id:
        bundle_rows = conn.execute(
            """
            SELECT name, qty, unit, category FROM shopping_bundle_items
            WHERE bundle_id=? ORDER BY position, id
            """,
            (int(bundle_id),),
        ).fetchall()
        for name, qty, unit, category in bundle_rows:
            conn.execute(
                """
                INSERT INTO shopping_list_items (list_id, name, qty, unit, category, source, position)
                VALUES (?, ?, ?, ?, ?, 'bundle', ?)
                """,
                (list_id, name, qty, unit or "", category or "Divers", pos),
            )
            pos += 1

    # --- Items manuels ---
    for item in (manual_items or []):
        conn.execute(
            """
            INSERT INTO shopping_list_items (list_id, name, qty, unit, category, source, position)
            VALUES (?, ?, ?, ?, ?, 'manual', ?)
            """,
            (
                list_id, item["name"], item.get("qty"), item.get("unit", ""),
                item.get("category", "Divers"), pos,
            ),
        )
        pos += 1

    conn.commit()
    # missing_items est retourné au frontend pour lui laisser le choix d'inclure ou non
    return get_active_list(conn), issues, missing_items


def toggle_shopping_item(conn, item_id: int, checked: bool, missing: bool = False) -> None:
    """
    checked=True + missing=False → article trouvé ✓
    checked=True + missing=True  → article manquant ⚠ (compte pour la progression, revient à la prochaine liste)
    checked=False                → article non coché
    """
    conn.execute(
        "UPDATE shopping_list_items SET checked=?, missing=? WHERE id=?",
        (1 if (checked or missing) else 0, 1 if missing else 0, int(item_id)),
    )
    conn.commit()


def add_item_to_active_list(conn, name: str, qty, unit: str, category: str) -> int:
    row = conn.execute(
        "SELECT id FROM shopping_list WHERE status='active' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        raise ValueError("Aucune liste active")
    list_id = row[0]
    max_pos = conn.execute(
        "SELECT COALESCE(MAX(position), 0) FROM shopping_list_items WHERE list_id=?",
        (list_id,),
    ).fetchone()[0]
    cur = conn.execute(
        """
        INSERT INTO shopping_list_items (list_id, name, qty, unit, category, source, position)
        VALUES (?, ?, ?, ?, ?, 'manual', ?)
        """,
        (list_id, name, qty, unit or "", category or "Divers", int(max_pos) + 1),
    )
    conn.commit()
    return cur.lastrowid


def delete_shopping_item(conn, item_id: int) -> None:
    conn.execute("DELETE FROM shopping_list_items WHERE id=?", (int(item_id),))
    conn.commit()


def complete_shopping_list(conn) -> None:
    conn.execute("UPDATE shopping_list SET status='done' WHERE status='active'")
    conn.commit()


# =============================================================================
# 15) User settings
# =============================================================================

def get_setting(conn, key: str, default: Optional[str] = None) -> Optional[str]:
    row = conn.execute("SELECT value FROM user_settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(conn, key: str, value: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)",
        (key, str(value)),
    )
    conn.commit()


def get_all_settings(conn) -> Dict[str, str]:
    rows = conn.execute("SELECT key, value FROM user_settings").fetchall()
    return {k: v for k, v in rows}


# =============================================================================
# 16) Stats gamification
# =============================================================================

def get_stats(conn) -> Dict:
    """Retourne les statistiques de cuisine pour la vue gamification."""
    # Total sessions de cuisine
    total_cooks = conn.execute("SELECT COUNT(*) FROM cooking_history").fetchone()[0]

    # Nombre de listes de courses complétées
    total_lists = conn.execute(
        "SELECT COUNT(*) FROM shopping_list WHERE status='done'"
    ).fetchone()[0]

    # Objectif hebdo (configurable, défaut = 3)
    weekly_goal = int(get_setting(conn, "weekly_goal", "3"))

    # Sessions de cuisine cette semaine (lundi → dimanche)
    now = datetime.now()
    monday = now - timedelta(days=now.weekday())
    monday_str = monday.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    weekly_cooks = conn.execute(
        "SELECT COUNT(*) FROM cooking_history WHERE cooked_at >= ?",
        (monday_str,),
    ).fetchone()[0]

    # Recettes uniques cuisinées (diversité)
    unique_recipes = conn.execute(
        "SELECT COUNT(DISTINCT recipe_id) FROM cooking_history"
    ).fetchone()[0]

    # Historique récent (7 derniers jours pour le bandeau)
    recent = conn.execute(
        """
        SELECT r.name, ch.cooked_at
        FROM cooking_history ch
        JOIN recipes r ON r.id = ch.recipe_id
        ORDER BY ch.cooked_at DESC
        LIMIT 5
        """,
    ).fetchall()

    return {
        "total_cooks": int(total_cooks),
        "total_lists_completed": int(total_lists),
        "weekly_goal": weekly_goal,
        "weekly_cooks": int(weekly_cooks),
        "unique_recipes_cooked": int(unique_recipes),
        "recent_cooks": [{"name": name, "cooked_at": cooked_at} for name, cooked_at in recent],
    }


# =============================================================================
# Helpers internes (suite)
# =============================================================================

def _get_or_create_ingredient_catalog(conn, name: str, show_qty_in_list=None, default_unit=None) -> int:
    row = conn.execute("SELECT id, default_unit FROM ingredient_catalog WHERE name=?", (name,)).fetchone()
    if row:
        ing_id = row[0]
        existing_unit = row[1]
        # Mettre à jour show_qty si fourni
        if show_qty_in_list is not None:
            conn.execute("UPDATE ingredient_catalog SET show_qty_in_list=? WHERE id=?",
                         (1 if show_qty_in_list else 0, ing_id))
        # Mettre à jour default_unit si non encore défini
        if default_unit and not existing_unit:
            resolved = resolve_unit(conn, default_unit)
            if resolved:
                conn.execute("UPDATE ingredient_catalog SET default_unit=? WHERE id=?",
                             (resolved, ing_id))
        return ing_id

    norm = normalize_ingredient_name(name)
    resolved_unit = None
    if default_unit:
        resolved_unit = resolve_unit(conn, default_unit)

    conn.execute(
        "INSERT INTO ingredient_catalog (name, norm_name, show_qty_in_list, default_unit) VALUES (?, ?, ?, ?)",
        (name, norm, 1 if show_qty_in_list is not False else 0, resolved_unit or default_unit or None),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
