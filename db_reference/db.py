# app/db.py
import os
import sqlite3
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# 1) Config / Connexion
# =============================================================================

# Par défaut, on garde recettes.db à côté de l'endroit où tu lances streamlit.
# Tu peux le déplacer plus tard (ex: data/recettes.db) via variable d'env.
DEFAULT_DB = (Path(__file__).resolve().parent.parent / "data" / "recettes.db")
DB_FILE = os.environ.get("APPCOOK_DB_FILE", str(DEFAULT_DB))
DB_FILE = str(Path(DB_FILE).expanduser().resolve())


def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# =============================================================================
# 2) Migrations / ensure_schema
# =============================================================================



# ---------- helpers schema ----------

def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    if not table_exists(conn, table):
        return False
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    # PRAGMA table_info: (cid, name, type, notnull, dflt_value, pk)
    return any(r[1] == column for r in rows)


# ---------- base schema (tables) ----------

def create_tables_if_needed(conn: sqlite3.Connection) -> None:
    """
    Crée toutes les tables de base si elles n'existent pas.
    IMPORTANT: aucun ALTER ici. Seulement CREATE TABLE IF NOT EXISTS.
    """
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS recipes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT NOT NULL UNIQUE,
          name TEXT NOT NULL,
          category TEXT,
          base_servings REAL NOT NULL,
          cookeo_modes TEXT,
          notes TEXT
        );

        CREATE TABLE IF NOT EXISTS ingredient_catalog (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL UNIQUE
          -- colonnes ajoutées via ALTER si besoin (show_qty_in_list, etc.)
        );

        CREATE TABLE IF NOT EXISTS recipe_ingredients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          recipe_id INTEGER NOT NULL,
          ingredient_id INTEGER NOT NULL,
          qty REAL,
          unit TEXT,
          optional INTEGER NOT NULL DEFAULT 0,
          notes TEXT,
          FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
          FOREIGN KEY (ingredient_id) REFERENCES ingredient_catalog(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS steps (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          recipe_id INTEGER NOT NULL,
          step_no INTEGER NOT NULL,
          title TEXT,
          instruction TEXT NOT NULL,
          cookeo_mode TEXT,
          time_min REAL,
          FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
          UNIQUE(recipe_id, step_no)
        );

        CREATE TABLE IF NOT EXISTS step_ingredients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          step_id INTEGER NOT NULL,
          recipe_ingredient_id INTEGER NOT NULL,
          FOREIGN KEY (step_id) REFERENCES steps(id) ON DELETE CASCADE,
          FOREIGN KEY (recipe_ingredient_id) REFERENCES recipe_ingredients(id) ON DELETE CASCADE,
          UNIQUE(step_id, recipe_ingredient_id)
        );
        """
    )


# ---------- migrations / alters ----------

def ensure_show_qty_column(conn: sqlite3.Connection) -> None:
    """
    Ajoute ingredient_catalog.show_qty_in_list si absent.
    Safe même si la table n'existe pas (mais normalement elle existe car créée avant).
    """
    if not table_exists(conn, "ingredient_catalog"):
        return
    if not column_exists(conn, "ingredient_catalog", "show_qty_in_list"):
        conn.execute(
            """
            ALTER TABLE ingredient_catalog
            ADD COLUMN show_qty_in_list INTEGER NOT NULL DEFAULT 1
            """
        ) 


def ensure_norm_name_column(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "ingredient_catalog"):
        return
    if not column_exists(conn, "ingredient_catalog", "norm_name"):
        conn.execute(
            """
            ALTER TABLE ingredient_catalog
            ADD COLUMN norm_name TEXT
            """
        )


def ensure_default_unit_column(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "ingredient_catalog"):
        return
    if not column_exists(conn, "ingredient_catalog", "default_unit"):
        conn.execute(
            """
            ALTER TABLE ingredient_catalog
            ADD COLUMN default_unit TEXT
            """
        )


def create_aux_tables_if_needed(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS ingredient_alias (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ingredient_id INTEGER NOT NULL,
          alias_name TEXT NOT NULL,
          alias_norm_name TEXT NOT NULL,
          FOREIGN KEY (ingredient_id) REFERENCES ingredient_catalog(id) ON DELETE CASCADE,
          UNIQUE(alias_norm_name)
        );

        CREATE TABLE IF NOT EXISTS unit_alias (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          alias TEXT NOT NULL,
          alias_norm TEXT NOT NULL UNIQUE,
          unit TEXT NOT NULL
        );
        """
    )


def ensure_schema(conn: sqlite3.Connection) -> None:
    """
    Point d'entrée unique : schéma + migrations.
    Idempotent et safe sur DB vide.
    """
    # Toujours activer FK sur la connexion courante
    conn.execute("PRAGMA foreign_keys = ON;")

    # 1) Base tables
    create_tables_if_needed(conn)

    # 2) Migrations / colonnes manquantes
    ensure_show_qty_column(conn)
    ensure_norm_name_column(conn)
    ensure_default_unit_column(conn)
    create_aux_tables_if_needed(conn)
    backfill_ingredient_norm_names(conn)
    refresh_ingredient_alias_norm_names(conn)
    seed_unit_aliases(conn)

    # 3) Commit global
    conn.commit()

# =============================================================================
# 3) Recipes
# =============================================================================

def load_recipes(conn):
    """Retourne un dict {code: {...}}"""
    cur = conn.execute(
        """
        SELECT code, name, category, base_servings, cookeo_modes, notes
        FROM recipes
        ORDER BY code
        """
    )
    recipes = {}
    for code, name, category, base_servings, cookeo_modes, notes in cur.fetchall():
        recipes[code] = {
            "code": code,
            "name": name,
            "category": category or "",
            "base_servings": float(base_servings),
            "cookeo_modes": cookeo_modes or "",
            "notes": notes or "",
        }
    return recipes


def get_recipe_id_by_code(conn, code: str):
    row = conn.execute("SELECT id FROM recipes WHERE code = ?", (code,)).fetchone()
    return row[0] if row else None


def get_recipe_row_by_code(conn, code: str):
    return conn.execute(
        """
        SELECT code, name, category, base_servings, cookeo_modes, COALESCE(notes,'')
        FROM recipes
        WHERE code=?
        """,
        (code,),
    ).fetchone()


def make_unique_code(conn, base_code: str) -> str:
    code = base_code
    i = 2
    while conn.execute(
        "SELECT 1 FROM recipes WHERE code=? LIMIT 1",
        (code,),
    ).fetchone():
        code = f"{base_code}_{i}"
        i += 1
    return code


def insert_recipe(conn, code: str, name: str, category: str, base_servings: float, cookeo_modes: str, notes: str):
    conn.execute(
        """
        INSERT INTO recipes (code, name, category, base_servings, cookeo_modes, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (code, name, category, float(base_servings), cookeo_modes, notes),
    )
    conn.commit()


def update_recipe_by_code(conn, code: str, name: str, category: str, base_servings: float, cookeo_modes: str, notes: str):
    conn.execute(
        """
        UPDATE recipes
        SET name=?, category=?, base_servings=?, cookeo_modes=?, notes=?
        WHERE code=?
        """,
        (name, category, float(base_servings), cookeo_modes, notes, code),
    )
    conn.commit()


def delete_recipe_by_code(conn, code: str):
    """Supprime recette + associations + steps (transaction)."""
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
# 4) Ingredients catalog
# =============================================================================

def search_ingredients_searchbox(searchterm: str, conn, limit: int = 20):
    """
    Retourne une liste d'options pour la searchbox.
    - Suggestions: ingrédients dont le nom contient searchterm
    - Option "➕ Créer : <searchterm>" si aucun match exact n'existe
    """
    term = (searchterm or "").strip()
    if not term:
        return []

    rows = conn.execute(
        """
        SELECT name
        FROM ingredient_catalog
        WHERE LOWER(name) LIKE LOWER(?)
        ORDER BY name
        LIMIT ?
        """,
        (f"%{term}%", limit),
    ).fetchall()

    opts = [r[0] for r in rows]
    exact = any(o.lower() == term.lower() for o in opts)

    if not exact:
        return [f"➕ Créer : {term}"] + opts
    return opts


def search_ingredients(conn, query: str, limit: int = 20):
    q = (query or "").strip().lower()
    if not q:
        return conn.execute(
            "SELECT id, name FROM ingredient_catalog ORDER BY name LIMIT ?",
            (limit,),
        ).fetchall()

    like = f"%{q}%"
    return conn.execute(
        """
        SELECT id, name
        FROM ingredient_catalog
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


def get_ingredient_id_by_name(conn, name: str):
    return resolve_ingredient_id_by_name(conn, name)


def get_or_create_ingredient_id(conn, name: str):
    name = name.strip()
    if not name:
        return None

    existing_id = resolve_ingredient_id_by_name(conn, name)
    if existing_id:
        return existing_id

    norm = normalize_ingredient_name(name)
    cur = conn.execute(
        "INSERT INTO ingredient_catalog (name, norm_name) VALUES (?, ?)",
        (name, norm),
    )
    conn.commit()
    return cur.lastrowid


def ingredient_is_used(conn, ingredient_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM recipe_ingredients WHERE ingredient_id=? LIMIT 1",
        (ingredient_id,),
    ).fetchone()
    return row is not None


def list_catalog_show_qty(conn):
    return conn.execute(
        "SELECT id, name, COALESCE(show_qty_in_list, 1) FROM ingredient_catalog ORDER BY name"
    ).fetchall()


def set_catalog_show_qty(conn, ingredient_id: int, show_qty: int):
    conn.execute(
        "UPDATE ingredient_catalog SET show_qty_in_list=? WHERE id=?",
        (1 if int(show_qty) else 0, int(ingredient_id)),
    )
    conn.commit()


def list_catalog_default_units(conn):
    return conn.execute(
        "SELECT id, name, COALESCE(default_unit, '') FROM ingredient_catalog ORDER BY name"
    ).fetchall()


def set_catalog_default_unit(conn, ingredient_id: int, default_unit: str):
    conn.execute(
        "UPDATE ingredient_catalog SET default_unit=? WHERE id=?",
        ((default_unit or "").strip(), int(ingredient_id)),
    )
    conn.commit()


def list_duplicate_ingredient_groups(conn):
    rows = conn.execute(
        """
        SELECT id, name, norm_name
        FROM ingredient_catalog
        WHERE norm_name IS NOT NULL AND norm_name != ''
        ORDER BY norm_name, name
        """
    ).fetchall()

    groups = defaultdict(list)
    for ing_id, name, norm_name in rows:
        groups[norm_name].append({"id": int(ing_id), "name": name})

    return [
        {"norm_name": norm_name, "items": items}
        for norm_name, items in groups.items()
        if len(items) > 1
    ]


def list_orphan_ingredients(conn):
    """
    Ingrédients sans recette associée.
    Retourne: (id, name, default_unit)
    """
    return conn.execute(
        """
        SELECT ic.id, ic.name, COALESCE(ic.default_unit, '')
        FROM ingredient_catalog ic
        LEFT JOIN recipe_ingredients ri ON ri.ingredient_id = ic.id
        WHERE ri.id IS NULL
        ORDER BY ic.name
        """
    ).fetchall()


def delete_orphan_ingredients(conn) -> int:
    rows = list_orphan_ingredients(conn)
    if not rows:
        return 0

    ids = [int(r[0]) for r in rows]
    placeholders = ",".join(["?"] * len(ids))

    try:
        conn.execute("BEGIN")
        conn.execute(
            f"DELETE FROM ingredient_catalog WHERE id IN ({placeholders})",
            ids,
        )
        conn.commit()
        return len(ids)
    except Exception:
        conn.rollback()
        raise


def merge_ingredients(conn, canonical_id: int, duplicate_ids: List[int]) -> int:
    dupes = [int(i) for i in duplicate_ids if int(i) != int(canonical_id)]
    if not dupes:
        return 0

    placeholders = ",".join(["?"] * len(dupes))
    params = [int(canonical_id)] + dupes

    try:
        conn.execute("BEGIN")
        conn.execute(
            f"UPDATE ingredient_alias SET ingredient_id=? WHERE ingredient_id IN ({placeholders})",
            params,
        )
        conn.execute(
            f"UPDATE recipe_ingredients SET ingredient_id=? WHERE ingredient_id IN ({placeholders})",
            params,
        )
        conn.execute(
            f"DELETE FROM ingredient_catalog WHERE id IN ({placeholders})",
            dupes,
        )
        conn.commit()
        return len(dupes)
    except Exception:
        conn.rollback()
        raise


def get_show_qty_map(conn):
    return dict(
        conn.execute(
            "SELECT name, COALESCE(show_qty_in_list, 1) FROM ingredient_catalog"
        ).fetchall()
    )


# =============================================================================
# 5) Recipe ingredients
# =============================================================================

def load_recipe_ingredients(conn):
    """
    Retourne une liste de dicts au format proche de l'ancien CSV:
    [
      {recipe_code, ingredient, qty, unit, optional, notes}
    ]
    """
    cur = conn.execute(
        """
        SELECT r.code, ic.name, ri.qty, ri.unit, ri.optional, COALESCE(ri.notes, '')
        FROM recipe_ingredients ri
        JOIN recipes r ON r.id = ri.recipe_id
        JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
        ORDER BY r.code, ic.name
        """
    )
    items = []
    for code, ing_name, qty, unit, optional, notes in cur.fetchall():
        items.append(
            {
                "recipe_code": code,
                "ingredient": ing_name,
                "qty": float(qty),
                "unit": unit,
                "optional": int(optional),
                "notes": notes or "",
            }
        )
    return items


def ingredient_in_recipe(conn, recipe_id: int, ingredient_id: int) -> bool:
    row = conn.execute(
        "SELECT 1 FROM recipe_ingredients WHERE recipe_id=? AND ingredient_id=? LIMIT 1",
        (recipe_id, ingredient_id),
    ).fetchone()
    return row is not None


def list_recipe_ingredients(conn, recipe_id: int):
    """
    Retourne: (ri_id, ingredient_id, ingredient_name, qty, unit, optional, notes)
    """
    return conn.execute(
        """
        SELECT ri.id as ri_id, ic.id as ingredient_id, ic.name as ingredient_name,
               ri.qty, ri.unit, ri.optional, COALESCE(ri.notes,'') as notes
        FROM recipe_ingredients ri
        JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
        WHERE ri.recipe_id = ?
        ORDER BY ic.name
        """,
        (recipe_id,),
    ).fetchall()


def delete_recipe_ingredient(conn, ri_id: int):
    conn.execute("DELETE FROM recipe_ingredients WHERE id=?", (ri_id,))
    conn.commit()


def update_recipe_ingredient(conn, ri_id: int, qty: float, unit: str, optional: int, notes: str):
    conn.execute(
        "UPDATE recipe_ingredients SET qty=?, unit=?, optional=?, notes=? WHERE id=?",
        (float(qty), unit, int(optional), notes, int(ri_id)),
    )
    conn.commit()


def add_recipe_ingredient(conn, recipe_id: int, ingredient_id: int, qty: float, unit: str, optional: int, notes: str):
    conn.execute(
        """
        INSERT INTO recipe_ingredients (recipe_id, ingredient_id, qty, unit, optional, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (int(recipe_id), int(ingredient_id), float(qty), unit, int(optional), notes),
    )
    conn.commit()


def list_recipe_ingredient_rows(conn, recipe_id: int):
    """
    Ingrédients (recipe_ingredients) d'une recette, pour alimenter la sélection par étape.
    Retourne: (ri_id, name, qty, unit)
    """
    return conn.execute(
        """
        SELECT ri.id, ic.name, ri.qty, ri.unit
        FROM recipe_ingredients ri
        JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
        WHERE ri.recipe_id = ?
        ORDER BY ic.name
        """,
        (int(recipe_id),),
    ).fetchall()


# =============================================================================
# 6) Steps
# =============================================================================

def load_steps(conn):
    """Retourne dict {recipe_code: [steps...]} pour l'affichage côté Recipes."""
    cur = conn.execute(
        """
        SELECT r.code, s.id, s.step_no, COALESCE(s.title,''), s.instruction,
               COALESCE(s.cookeo_mode,''), s.time_min
        FROM steps s
        JOIN recipes r ON r.id = s.recipe_id
        ORDER BY r.code, s.step_no
        """
    )
    steps_by_recipe = defaultdict(list)
    for code, sid, step_no, title, instruction, cookeo_mode, time_min in cur.fetchall():
        steps_by_recipe[code].append(
            {
                "id": int(sid),
                "step_no": int(step_no),
                "title": title.strip(),
                "instruction": instruction.strip(),
                "cookeo_mode": cookeo_mode.strip(),
                "time_min": time_min,  # peut être None
            }
        )
    return steps_by_recipe


def list_steps_by_recipe(conn, recipe_id: int):
    return conn.execute(
        """
        SELECT id, step_no, COALESCE(title,''), instruction,
               COALESCE(cookeo_mode,''), time_min
        FROM steps
        WHERE recipe_id = ?
        ORDER BY step_no
        """,
        (recipe_id,),
    ).fetchall()


def update_step(conn, step_id: int, step_no: int, title: str, instruction: str, cookeo_mode: str, time_min):
    conn.execute(
        """
        UPDATE steps
        SET step_no=?, title=?, instruction=?, cookeo_mode=?, time_min=?
        WHERE id=?
        """,
        (int(step_no), title, instruction, cookeo_mode, time_min, int(step_id)),
    )
    conn.commit()


def delete_step(conn, step_id: int):
    conn.execute("DELETE FROM steps WHERE id=?", (int(step_id),))
    conn.commit()


def insert_step(conn, recipe_id: int, step_no: int, title: str, instruction: str, cookeo_mode: str, time_min):
    conn.execute(
        """
        INSERT INTO steps (recipe_id, step_no, title, instruction, cookeo_mode, time_min)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (int(recipe_id), int(step_no), title, instruction, cookeo_mode, time_min),
    )
    conn.commit()


# =============================================================================
# 7) Step ingredients (step_ingredients)
# =============================================================================

def get_step_ingredient_ids(conn, step_id: int):
    rows = conn.execute(
        "SELECT recipe_ingredient_id FROM step_ingredients WHERE step_id=?",
        (int(step_id),),
    ).fetchall()
    return [r[0] for r in rows]


def save_step_ingredients(conn, step_id: int, recipe_ingredient_ids: list[int]):
    conn.execute("DELETE FROM step_ingredients WHERE step_id=?", (int(step_id),))
    conn.executemany(
        "INSERT OR IGNORE INTO step_ingredients (step_id, recipe_ingredient_id) VALUES (?, ?)",
        [(int(step_id), int(ri_id)) for ri_id in recipe_ingredient_ids],
    )
    conn.commit()


def list_step_ingredients_for_display(conn, step_id: int):
    """
    Ingrédients associés à une étape (pour affichage dans la page Recettes).
    Retourne: (name, qty, unit, show_qty_in_list, optional)
    """
    return conn.execute(
        """
        SELECT ic.name, ri.qty, ri.unit, ic.show_qty_in_list, ri.optional
        FROM step_ingredients si
        JOIN recipe_ingredients ri ON ri.id = si.recipe_ingredient_id
        JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
        WHERE si.step_id = ?
        ORDER BY ic.name
        """,
        (int(step_id),),
    ).fetchall()

SCHEMA_V1 = "appcook.recipe.v1"

# =============================================================================
# Ingredient normalization & aliases
# =============================================================================

PLURAL_EXCEPTIONS = {"riz", "maïs", "ananas", "pois"}

UNIT_CANONICAL = {"g", "kg", "ml", "l", "cl", "pièce", "gousse", "tranche", "cube", "pincée", "cs", "cc"}

UNIT_ALIAS_SEED = [
    ("g", "g"),
    ("gr", "g"),
    ("grs", "g"),
    ("kg", "kg"),
    ("kgs", "kg"),
    ("ml", "ml"),
    ("l", "l"),
    ("litre", "l"),
    ("litres", "l"),
    ("cl", "cl"),
    ("pc", "pièce"),
    ("piece", "pièce"),
    ("pieces", "pièce"),
    ("pièce", "pièce"),
    ("pièces", "pièce"),
    ("pcs", "pièce"),
    ("pincee", "pincée"),
    ("pincees", "pincée"),
    ("pincée", "pincée"),
    ("pincées", "pincée"),
    ("tranches", "tranche"),
    ("cs", "cs"),
    ("cc", "cc"),
    ("c a s", "cs"),
    ("c a c", "cc"),
    ("c. a s", "cs"),
    ("c. a c", "cc"),
    ("c. a. s", "cs"),
    ("c. a. c", "cc"),
    ("c a soupe", "cs"),
    ("c a cafe", "cc"),
    ("c. a soupe", "cs"),
    ("c. a cafe", "cc"),
    ("c. à soupe", "cs"),
    ("c. à cafe", "cc"),
    ("c. à café", "cc"),
    ("cas", "tbsp"),
    ("càs", "tbsp"),
    ("cs", "tbsp"),
    ("tbsp", "tbsp"),
]


def _strip_accents(text: str) -> str:
    text = text.replace("œ", "oe").replace("æ", "ae")
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_ingredient_name(name: str) -> str:
    s = _strip_accents((name or "").strip().lower())
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.split(r"\s+/(?:\s+|$)|\s+ou\s+", s, maxsplit=1)[0]
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s in {"creme fraiche", "creme"}:
        s = "creme"
    if s in {"farine de ble", "farine"}:
        s = "farine"
    if s in {"sucre blanc", "sucre"}:
        s = "sucre"

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
    s = s.replace(".", "")
    s = re.sub(r"\s+", "", s)
    return s


CANONICAL_UNIT_BY_NORM = {normalize_unit_alias(u): u for u in UNIT_CANONICAL}


def resolve_ingredient_id_by_name(conn, name: str):
    norm = normalize_ingredient_name(name)
    if not norm:
        return None

    row = conn.execute(
        "SELECT ingredient_id FROM ingredient_alias WHERE alias_norm_name = ? LIMIT 1",
        (norm,),
    ).fetchone()
    if row:
        return row[0]

    row = conn.execute(
        "SELECT id FROM ingredient_catalog WHERE norm_name = ? LIMIT 1",
        (norm,),
    ).fetchone()
    return row[0] if row else None


SQL_UNIT_ALIAS_ALL = """
    SELECT alias_norm, unit
    FROM unit_alias
"""


def get_unit_alias_map(conn) -> Dict[str, str]:
    rows = conn.execute(SQL_UNIT_ALIAS_ALL).fetchall()
    return {alias_norm: unit for alias_norm, unit in rows}


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


UNIT_FACTORS = {
    "g": ("weight", 1.0),
    "kg": ("weight", 1000.0),
    "ml": ("volume", 1.0),
    "cl": ("volume", 10.0),
    "l": ("volume", 1000.0),
    "pièce": ("piece", 1.0),
    "gousse": ("piece", 1.0),
    "tranche": ("piece", 1.0),
    "cube": ("piece", 1.0),
    "pincée": ("piece", 1.0),
    "cs": ("piece", 1.0),
    "cc": ("piece", 1.0),
}


def convert_qty(qty: float, from_unit: str, to_unit: str) -> Optional[float]:
    if from_unit == to_unit:
        return qty
    from_group, from_factor = UNIT_FACTORS.get(from_unit, (None, None))
    to_group, to_factor = UNIT_FACTORS.get(to_unit, (None, None))
    if from_group is None or to_group is None or from_group != to_group:
        return None
    return qty * (from_factor / to_factor)


SQL_SHOPPING_INGREDIENTS = """
    SELECT r.code,
           r.base_servings,
           ic.id,
           ic.name,
           ic.norm_name,
           ic.default_unit,
           COALESCE(ic.show_qty_in_list, 1),
           ri.qty,
           ri.unit,
           ri.optional
    FROM recipe_ingredients ri
    JOIN recipes r ON r.id = ri.recipe_id
    JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
    WHERE r.code IN ({placeholders})
    ORDER BY r.code, ic.name
"""


def list_shopping_ingredients(conn, recipe_codes: List[str]):
    if not recipe_codes:
        return []
    placeholders = ",".join(["?"] * len(recipe_codes))
    sql = SQL_SHOPPING_INGREDIENTS.format(placeholders=placeholders)
    return conn.execute(sql, recipe_codes).fetchall()


def aggregate_shopping_list(conn, recipe_codes: List[str], persons: float, include_optional: bool):
    rows = list_shopping_ingredients(conn, recipe_codes)
    alias_map = get_unit_alias_map(conn)

    items_by_key: Dict[str, Dict[str, Any]] = {}
    issues: List[Dict[str, Any]] = []

    for (
        code,
        base_servings,
        ingredient_id,
        name,
        norm_name,
        default_unit,
        show_qty,
        qty,
        unit,
        optional,
    ) in rows:
        if int(optional or 0) == 1 and not include_optional:
            continue

        base = float(base_servings or 1)
        factor = float(persons) / base if base else 1.0
        scaled_qty = (float(qty) if qty is not None else 0.0) * factor

        default_unit = (default_unit or "").strip()
        if not default_unit:
            issues.append(
                {
                    "recipe_code": code,
                    "ingredient_name": name,
                    "unit": unit or "",
                    "default_unit": "",
                    "qty": scaled_qty,
                    "reason": "default_unit_missing",
                    "message": "Unité par défaut manquante",
                }
            )
            continue

        default_resolved = resolve_unit(conn, default_unit, alias_map)
        if not default_resolved or default_resolved not in UNIT_CANONICAL:
            issues.append(
                {
                    "recipe_code": code,
                    "ingredient_name": name,
                    "unit": unit or "",
                    "default_unit": default_unit,
                    "qty": scaled_qty,
                    "reason": "default_unit_invalid",
                    "message": "Unité par défaut invalide",
                }
            )
            continue

        unit_resolved = resolve_unit(conn, unit or "", alias_map)
        if unit_resolved == "":
            issues.append(
                {
                    "recipe_code": code,
                    "ingredient_name": name,
                    "unit": "",
                    "default_unit": default_resolved,
                    "qty": scaled_qty,
                    "reason": "unit_missing",
                    "message": "Unité manquante dans la recette",
                }
            )
            continue
        if unit_resolved is None:
            issues.append(
                {
                    "recipe_code": code,
                    "ingredient_name": name,
                    "unit": unit or "",
                    "default_unit": default_resolved,
                    "qty": scaled_qty,
                    "reason": "unit_unknown",
                    "message": "Unité inconnue",
                }
            )
            continue
        if unit_resolved not in UNIT_CANONICAL:
            issues.append(
                {
                    "recipe_code": code,
                    "ingredient_name": name,
                    "unit": unit or "",
                    "default_unit": default_resolved,
                    "qty": scaled_qty,
                    "reason": "unit_non_convertible",
                    "message": "Unité non convertible",
                }
            )
            continue

        converted_qty = convert_qty(scaled_qty, unit_resolved, default_resolved)
        if converted_qty is None:
            issues.append(
                {
                    "recipe_code": code,
                    "ingredient_name": name,
                    "unit": unit or "",
                    "default_unit": default_resolved,
                    "qty": scaled_qty,
                    "reason": "unit_incompatible",
                    "message": "Unité incompatible avec l'unité par défaut",
                }
            )
            continue

        key = norm_name or f"id:{int(ingredient_id)}"
        item = items_by_key.get(key)
        if not item:
            items_by_key[key] = {
                "name": name,
                "unit": default_resolved,
                "qty": converted_qty,
                "show_qty": int(show_qty or 1),
            }
        else:
            item["qty"] += converted_qty

    items = list(items_by_key.values())
    items.sort(key=lambda x: x["name"].lower())
    return items, issues


SQL_RECIPE_INGREDIENTS_AUDIT = """
    SELECT ri.id,
           r.code,
           r.name,
           ic.id,
           ic.name,
           ic.default_unit,
           ri.unit
    FROM recipe_ingredients ri
    JOIN recipes r ON r.id = ri.recipe_id
    JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
    ORDER BY r.code, ic.name
"""


def list_unit_issues(conn):
    rows = conn.execute(SQL_RECIPE_INGREDIENTS_AUDIT).fetchall()
    alias_map = get_unit_alias_map(conn)
    issues: List[Dict[str, Any]] = []

    for ri_id, rcode, rname, ing_id, ing_name, default_unit, unit in rows:
        default_unit = (default_unit or "").strip()
        unit = (unit or "").strip()

        if not default_unit:
            issues.append(
                {
                    "ri_id": int(ri_id),
                    "recipe_code": rcode,
                    "recipe_name": rname,
                    "ingredient_id": int(ing_id),
                    "ingredient_name": ing_name,
                    "unit": unit,
                    "default_unit": "",
                    "reason": "default_unit_missing",
                    "message": "Unite par defaut manquante",
                }
            )
            continue

        default_resolved = resolve_unit(conn, default_unit, alias_map)
        if not default_resolved or default_resolved not in UNIT_CANONICAL:
            issues.append(
                {
                    "ri_id": int(ri_id),
                    "recipe_code": rcode,
                    "recipe_name": rname,
                    "ingredient_id": int(ing_id),
                    "ingredient_name": ing_name,
                    "unit": unit,
                    "default_unit": default_unit,
                    "reason": "default_unit_invalid",
                    "message": "Unite par defaut invalide",
                }
            )
            continue

        if unit == "":
            issues.append(
                {
                    "ri_id": int(ri_id),
                    "recipe_code": rcode,
                    "recipe_name": rname,
                    "ingredient_id": int(ing_id),
                    "ingredient_name": ing_name,
                    "unit": "",
                    "default_unit": default_resolved,
                    "reason": "unit_missing",
                    "message": "Unite manquante dans la recette",
                }
            )
            continue

        unit_resolved = resolve_unit(conn, unit, alias_map)
        if unit_resolved is None:
            issues.append(
                {
                    "ri_id": int(ri_id),
                    "recipe_code": rcode,
                    "recipe_name": rname,
                    "ingredient_id": int(ing_id),
                    "ingredient_name": ing_name,
                    "unit": unit,
                    "default_unit": default_resolved,
                    "reason": "unit_unknown",
                    "message": "Unite inconnue",
                }
            )
            continue

        if unit_resolved not in UNIT_CANONICAL:
            issues.append(
                {
                    "ri_id": int(ri_id),
                    "recipe_code": rcode,
                    "recipe_name": rname,
                    "ingredient_id": int(ing_id),
                    "ingredient_name": ing_name,
                    "unit": unit,
                    "default_unit": default_resolved,
                    "reason": "unit_non_canonical",
                    "message": "Unite non canonique",
                }
            )
            continue

        if convert_qty(1.0, unit_resolved, default_resolved) is None:
            issues.append(
                {
                    "ri_id": int(ri_id),
                    "recipe_code": rcode,
                    "recipe_name": rname,
                    "ingredient_id": int(ing_id),
                    "ingredient_name": ing_name,
                    "unit": unit,
                    "default_unit": default_resolved,
                    "reason": "unit_incompatible",
                    "message": "Unite incompatible avec l'unite par defaut",
                }
            )

    return issues


def update_recipe_ingredient_unit(conn, ri_id: int, unit: str):
    conn.execute(
        "UPDATE recipe_ingredients SET unit=? WHERE id=?",
        ((unit or "").strip(), int(ri_id)),
    )
    conn.commit()


def backfill_ingredient_norm_names(conn) -> None:
    if not column_exists(conn, "ingredient_catalog", "norm_name"):
        return
    rows = conn.execute(
        "SELECT id, name FROM ingredient_catalog"
    ).fetchall()
    if not rows:
        return
    updates = [(normalize_ingredient_name(name), int(ing_id)) for ing_id, name in rows]
    conn.executemany(
        "UPDATE ingredient_catalog SET norm_name = ? WHERE id = ?",
        updates,
    )


def refresh_ingredient_alias_norm_names(conn) -> None:
    if not table_exists(conn, "ingredient_alias"):
        return
    rows = conn.execute(
        "SELECT id, alias_name FROM ingredient_alias"
    ).fetchall()
    if not rows:
        return
    updates = [(normalize_ingredient_name(name), int(alias_id)) for alias_id, name in rows]
    conn.executemany(
        "UPDATE ingredient_alias SET alias_norm_name = ? WHERE id = ?",
        updates,
    )


def seed_unit_aliases(conn) -> None:
    if not table_exists(conn, "unit_alias"):
        return
    rows = [
        (alias, normalize_unit_alias(alias), unit)
        for alias, unit in UNIT_ALIAS_SEED
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO unit_alias (alias, alias_norm, unit) VALUES (?, ?, ?)",
        rows,
    )

    conn.execute(
        """
        UPDATE ingredient_catalog
        SET default_unit = 'pièce'
        WHERE LOWER(default_unit) IN ('pc', 'pcs')
        """
    )


# =============================================================================
# Export SQL (v1.0)
# =============================================================================

SQL_EXPORT_RECIPE_META = """
    SELECT name, base_servings, notes
    FROM recipes
    WHERE id = ?
"""

SQL_EXPORT_RECIPE_INGREDIENTS = """
    SELECT ic.name, ri.qty, ri.unit, COALESCE(ic.show_qty_in_list, 1)
    FROM recipe_ingredients ri
    JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
    WHERE ri.recipe_id = ?
    ORDER BY ic.name
"""

SQL_EXPORT_STEPS = """
    SELECT id, step_no, title, instruction, time_min
    FROM steps
    WHERE recipe_id = ?
    ORDER BY step_no
"""

SQL_EXPORT_STEP_INGREDIENTS = """
    SELECT si.step_id, ic.name, ri.qty, ri.unit
    FROM step_ingredients si
    JOIN recipe_ingredients ri ON ri.id = si.recipe_ingredient_id
    JOIN ingredient_catalog ic ON ic.id = ri.ingredient_id
    WHERE ri.recipe_id = ?
    ORDER BY ic.name
"""


def get_recipe_meta_for_export(conn, recipe_id: int):
    return conn.execute(SQL_EXPORT_RECIPE_META, (int(recipe_id),)).fetchone()


def list_recipe_ingredients_for_export(conn, recipe_id: int):
    return conn.execute(SQL_EXPORT_RECIPE_INGREDIENTS, (int(recipe_id),)).fetchall()


def list_steps_for_export(conn, recipe_id: int):
    return conn.execute(SQL_EXPORT_STEPS, (int(recipe_id),)).fetchall()


def list_step_ingredients_for_export(conn, recipe_id: int):
    return conn.execute(SQL_EXPORT_STEP_INGREDIENTS, (int(recipe_id),)).fetchall()

# -------------------------
# Validation JSON (v1.0)
# -------------------------

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

    title = recipe.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("recipe.title est obligatoire (string non vide).")

    # ingredients globaux
    ingredients = recipe.get("ingredients")
    if not isinstance(ingredients, list):
        errors.append("recipe.ingredients doit être une liste.")
    else:
        for i, ing in enumerate(ingredients):
            if not isinstance(ing, dict):
                errors.append(f"ingredients[{i}] doit être un objet.")
                continue
            name = ing.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"ingredients[{i}].name est obligatoire (string non vide).")
            if "show_qty_in_list" in ing and not isinstance(ing["show_qty_in_list"], bool):
                errors.append(f"ingredients[{i}].show_qty_in_list doit être un bool.")

    # steps
    steps = recipe.get("steps")
    if not isinstance(steps, list) or len(steps) == 0:
        errors.append("recipe.steps doit être une liste non vide.")
    else:
        for si, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"steps[{si}] doit être un objet.")
                continue

            text = step.get("text")
            if not isinstance(text, str) or not text.strip():
                errors.append(f"steps[{si}].text est obligatoire (string non vide).")

            if "time_sec" in step and step["time_sec"] is not None:
                if not isinstance(step["time_sec"], int) or step["time_sec"] < 0:
                    errors.append(f"steps[{si}].time_sec doit être un entier >= 0 ou null.")

            step_ings = step.get("ingredients", [])
            if step_ings is not None and not isinstance(step_ings, list):
                errors.append(f"steps[{si}].ingredients doit être une liste si présent.")
            elif isinstance(step_ings, list):
                for ji, jing in enumerate(step_ings):
                    if not isinstance(jing, dict):
                        errors.append(f"steps[{si}].ingredients[{ji}] doit être un objet.")
                        continue
                    name = jing.get("name")
                    if not isinstance(name, str) or not name.strip():
                        errors.append(f"steps[{si}].ingredients[{ji}].name est obligatoire.")

    # cohérence : ingrédients d’étape doivent exister en global (par name, insensible à la casse)
    if isinstance(ingredients, list) and isinstance(steps, list):
        global_names = {(ing.get("name") or "").strip().lower() for ing in ingredients if isinstance(ing, dict)}
        global_names.discard("")
        for si, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            step_ings = step.get("ingredients", []) or []
            if not isinstance(step_ings, list):
                continue
            for ji, jing in enumerate(step_ings):
                if not isinstance(jing, dict):
                    continue
                nm = (jing.get("name") or "").strip().lower()
                if nm and nm not in global_names:
                    errors.append(
                        f"Ingrédient d'étape '{jing.get('name')}' (steps[{si}].ingredients[{ji}]) "
                        f"absent des ingrédients globaux."
                    )

    return (len(errors) == 0), errors


# -------------------------
# Import JSON (v1.0)
# -------------------------

def import_recipe_from_json(
    data: Dict[str, Any],
    *,
    on_code_conflict: str = "rename",   # "rename" | "error"
) -> int:
    """
    Importe 1 recette au format JSON v1.0 dans la DB.
    Transactionnel : tout ou rien.

    Mapping vers DB:
    - recipe.title -> recipes.name
    - recipe.servings -> recipes.base_servings (float)
    - recipe.source/tags -> recipes.notes (concat simple)
    - steps[].text -> steps.instruction
    - steps[].time_sec -> steps.time_min (sec / 60)
    - step_ingredients : lien vers recipe_ingredients (via nom -> recipe_ingredient_id)
    """
    ok, errors = validate_recipe_json(data)
    if not ok:
        raise ValueError("JSON invalide:\n- " + "\n- ".join(errors))

    r = data["recipe"]
    title: str = r["title"].strip()

    # base_servings: si absent, on met 1.0 (simple et sûr)
    base_servings = r.get("servings")
    try:
        base_servings_f = float(base_servings) if base_servings is not None else 1.0
    except Exception:
        base_servings_f = 1.0

    # Notes: on reste simple, sans créer de colonnes
    source = r.get("source")
    tags = r.get("tags")
    notes = r.get("notes")

    notes_lines: List[str] = []
    if isinstance(source, str) and source.strip():
        notes_lines.append(f"Source: {source.strip()}")
    if isinstance(tags, list) and tags:
        safe_tags = [str(t).strip() for t in tags if str(t).strip()]
        if safe_tags:
            notes_lines.append("Tags: " + ", ".join(safe_tags))
    if isinstance(notes, str) and notes.strip():
        notes_lines.append(notes.strip())

    final_notes = "\n".join(notes_lines) if notes_lines else None

    # code : dérivé du titre (slug) et résolu en cas de conflit
    desired_code = _slugify_code(title)
    conn = get_conn()
    try:
        conn.execute("BEGIN")

        final_code = _resolve_recipe_code(conn, desired_code, mode=on_code_conflict)

        recipe_id = conn.execute(
            """
            INSERT INTO recipes (code, name, category, base_servings, cookeo_modes, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                final_code,
                title,
                None,            # category (non fourni par JSON v1.0)
                base_servings_f,
                None,            # cookeo_modes (non fourni par JSON v1.0)
                final_notes,
            ),
        ).lastrowid

        # 1) Créer tous les ingrédients globaux (recipe_ingredients)
        #    et construire un mapping name(lower) -> recipe_ingredient_id
        name_to_ri_id: Dict[str, int] = {}
        for ing in r.get("ingredients", []):
            name = ing["name"].strip()
            qty = ing.get("qty")
            unit = ing.get("unit")
            if unit is None:
                unit = ""

            show = ing.get("show_qty_in_list", None)
            ingredient_id = _get_or_create_ingredient_catalog(conn, name, show_qty_in_list=show)

            ri_id = conn.execute(
                """
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, qty, unit, optional, notes)
                VALUES (?, ?, ?, ?, 0, NULL)
                """,
                (recipe_id, ingredient_id, qty, unit),
            ).lastrowid


            name_to_ri_id[name.lower()] = ri_id

        # 2) Créer steps + liens step_ingredients vers recipe_ingredients
        for idx, step in enumerate(r.get("steps", []), start=1):
            step_title = step.get("title")
            instruction = step["text"].strip()

            time_min = None
            if step.get("time_sec") is not None:
                # REAL en DB, conversion sec -> min
                time_min = float(step["time_sec"]) / 60.0

            cookeo_mode = step.get("cookeo_mode")  # (pas dans JSON v1.0, mais ignore si absent)

            step_id = conn.execute(
                """
                INSERT INTO steps (recipe_id, step_no, title, instruction, cookeo_mode, time_min)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (recipe_id, idx, step_title, instruction, cookeo_mode, time_min),
            ).lastrowid

            for jing in (step.get("ingredients", []) or []):
                jname = jing["name"].strip().lower()
                ri_id = name_to_ri_id.get(jname)
                if not ri_id:
                    # ne devrait pas arriver grâce à validate_recipe_json
                    raise ValueError(f"Ingrédient d'étape introuvable dans les globaux: {jing.get('name')}")

                conn.execute(
                    """
                    INSERT OR IGNORE INTO step_ingredients (step_id, recipe_ingredient_id)
                    VALUES (?, ?)
                    """,
                    (step_id, ri_id),
                )

        conn.commit()
        return recipe_id

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -------------------------
# Export JSON (v1.0)
# -------------------------

def export_recipe_to_json(conn, recipe_id: int) -> Dict[str, Any]:
    """
    Exporte une recette existante au format JSON v1.0.
    """
    row = get_recipe_meta_for_export(conn, recipe_id)
    if not row:
        raise ValueError(f"Recette introuvable (id={recipe_id}).")

    title, base_servings, notes = row

    ing_rows = list_recipe_ingredients_for_export(conn, recipe_id)
    ingredients: List[Dict[str, Any]] = []
    for name, qty, unit, show_qty in ing_rows:
        ingredients.append(
            {
                "name": name,
                "qty": qty,
                "unit": unit or "",
                "show_qty_in_list": bool(show_qty),
            }
        )

    step_rows = list_steps_for_export(conn, recipe_id)
    step_ing_rows = list_step_ingredients_for_export(conn, recipe_id)

    step_ingredients_map: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for step_id, name, qty, unit in step_ing_rows:
        step_ingredients_map[int(step_id)].append(
            {"name": name, "qty": qty, "unit": unit or ""}
        )

    steps: List[Dict[str, Any]] = []
    for sid, step_no, title, instruction, time_min in step_rows:
        step: Dict[str, Any] = {"text": instruction}
        if title:
            step["title"] = title
        if time_min is not None:
            step["time_sec"] = int(round(float(time_min) * 60))

        step_ings = step_ingredients_map.get(int(sid), [])
        if step_ings:
            step["ingredients"] = step_ings

        steps.append(step)

    recipe: Dict[str, Any] = {
        "title": title,
        "servings": base_servings,
        "ingredients": ingredients,
        "steps": steps,
    }
    if notes:
        recipe["notes"] = notes

    return {
        "schema_version": SCHEMA_V1,
        "recipe": recipe,
    }


def export_recipe_to_json_by_code(conn, code: str) -> Dict[str, Any]:
    recipe_id = get_recipe_id_by_code(conn, code)
    if recipe_id is None:
        raise ValueError(f"Recette introuvable (code={code}).")
    return export_recipe_to_json(conn, recipe_id)


# -------------------------
# Helpers
# -------------------------

def _slugify_code(title: str) -> str:
    """
    Transforme un titre en code stable.
    - minuscule
    - espaces -> _
    - caractères non alphanum -> _
    - compactage
    """
    s = title.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "recette"


def _resolve_recipe_code(conn: sqlite3.Connection, desired_code: str, mode: str) -> str:
    row = conn.execute("SELECT 1 FROM recipes WHERE code = ? LIMIT 1", (desired_code,)).fetchone()
    if not row:
        return desired_code

    if mode == "error":
        raise ValueError(f"Une recette avec le code '{desired_code}' existe déjà.")

    # rename: suffixe _import, _import2, ...
    base = f"{desired_code}_import"
    candidate = base
    n = 2
    while conn.execute("SELECT 1 FROM recipes WHERE code = ? LIMIT 1", (candidate,)).fetchone():
        candidate = f"{base}{n}"
        n += 1
    return candidate


def _get_or_create_ingredient_catalog(
    conn: sqlite3.Connection,
    name: str,
    show_qty_in_list: Optional[bool],
) -> int:
    row = conn.execute(
        "SELECT id FROM ingredient_catalog WHERE name = ?",
        (name,),
    ).fetchone()

    if row:
        ing_id = row["id"] if isinstance(row, sqlite3.Row) else row[0]
        # show_qty_in_list est géré via ALTER et une colonne potentiellement ajoutée
        if show_qty_in_list is not None and column_exists(conn, "ingredient_catalog", "show_qty_in_list"):
            conn.execute(
                "UPDATE ingredient_catalog SET show_qty_in_list = ? WHERE id = ?",
                (1 if show_qty_in_list else 0, ing_id),
            )
        return ing_id

    # Création
    if column_exists(conn, "ingredient_catalog", "show_qty_in_list"):
        conn.execute(
            "INSERT INTO ingredient_catalog (name, show_qty_in_list) VALUES (?, ?)",
            (name, 1 if show_qty_in_list else 0),
        )
    else:
        conn.execute(
            "INSERT INTO ingredient_catalog (name) VALUES (?)",
            (name,),
        )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
