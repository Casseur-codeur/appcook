"""
Seed script — AppCook
Lance avec : python seed.py

Peuple la DB avec :
  - 3 bundles (Petit / Moyen / Grand) et leurs articles
  - 3 recettes de test avec ingrédients + étapes

Idempotent : vérifie si les données existent avant d'insérer.
"""
import os
import sqlite3
import re
import unicodedata
from pathlib import Path

_default_db = Path(__file__).resolve().parent / "data" / "recettes.db"
DB_FILE = Path(os.environ.get("APPCOOK_DB_FILE", str(_default_db)))


def get_conn():
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def normalize(name: str) -> str:
    name = name.strip().lower()
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def get_or_create_ingredient(conn, name: str, default_unit: str = None) -> int:
    norm = normalize(name)
    row = conn.execute(
        "SELECT id FROM ingredient_catalog WHERE norm_name=?", (norm,)
    ).fetchone()
    if row:
        ing_id = row[0]
        # Met à jour l'unité par défaut si elle n'est pas encore renseignée
        if default_unit:
            conn.execute(
                "UPDATE ingredient_catalog SET default_unit=? WHERE id=? AND (default_unit IS NULL OR default_unit='')",
                (default_unit, ing_id),
            )
        return ing_id
    cur = conn.execute(
        "INSERT INTO ingredient_catalog (name, norm_name, default_unit) VALUES (?, ?, ?)",
        (name, norm, default_unit),
    )
    return cur.lastrowid


def seed_bundles(conn):
    print("\n── Bundles ──")

    bundles = [
        {
            "name": "Petit",
            "icon": "🧺",
            "position": 1,
            "items": [
                ("Lait",            1,    "l",      "Frais"),
                ("Beurre",          250,  "g",      "Frais"),
                ("Œufs",            6,    "pièce",  "Frais"),
                ("Pain de mie",     1,    "pièce",  "Épicerie"),
                ("Café",            250,  "g",      "Épicerie"),
                ("Papier toilette", 6,    "pièce",  "Hygiène"),
                ("Eau gazeuse",     6,    "pièce",  "Boissons"),
            ],
        },
        {
            "name": "Moyen",
            "icon": "🛒",
            "position": 2,
            "items": [
                ("Lait",              2,    "l",      "Frais"),
                ("Beurre",            250,  "g",      "Frais"),
                ("Œufs",              12,   "pièce",  "Frais"),
                ("Fromage râpé",      200,  "g",      "Frais"),
                ("Yaourt nature",     4,    "pièce",  "Frais"),
                ("Pain de mie",       1,    "pièce",  "Épicerie"),
                ("Café",              250,  "g",      "Épicerie"),
                ("Riz complet",       1,    "kg",     "Épicerie"),
                ("Pâtes",             500,  "g",      "Épicerie"),
                ("Huile d'olive",     1,    "l",      "Épicerie"),
                ("Papier toilette",   12,   "pièce",  "Hygiène"),
                ("Liquide vaisselle", 1,    "pièce",  "Hygiène"),
                ("Eau gazeuse",       6,    "pièce",  "Boissons"),
                ("Jus d'orange",      1,    "l",      "Boissons"),
            ],
        },
        {
            "name": "Grand",
            "icon": "🏪",
            "position": 3,
            "items": [
                ("Lait",                2,    "l",      "Frais"),
                ("Beurre",              500,  "g",      "Frais"),
                ("Œufs",                12,   "pièce",  "Frais"),
                ("Fromage râpé",        400,  "g",      "Frais"),
                ("Yaourt nature",       8,    "pièce",  "Frais"),
                ("Crème fraîche",       20,   "cl",     "Frais"),
                ("Pain de mie",         2,    "pièce",  "Épicerie"),
                ("Café",                500,  "g",      "Épicerie"),
                ("Riz complet",         2,    "kg",     "Épicerie"),
                ("Pâtes",               1,    "kg",     "Épicerie"),
                ("Huile d'olive",       1,    "l",      "Épicerie"),
                ("Épices cajun",        1,    "pièce",  "Épicerie"),
                ("Sauce soja",          1,    "pièce",  "Épicerie"),
                ("Miel",                1,    "pièce",  "Épicerie"),
                ("Papier toilette",     24,   "pièce",  "Hygiène"),
                ("Liquide vaisselle",   2,    "pièce",  "Hygiène"),
                ("Lessive",             1,    "pièce",  "Hygiène"),
                ("Déodorant",           1,    "pièce",  "Hygiène"),
                ("Gel douche",          1,    "pièce",  "Hygiène"),
                ("Eau gazeuse",         12,   "pièce",  "Boissons"),
                ("Jus d'orange",        2,    "l",      "Boissons"),
                ("Poulet surgelé",      1,    "kg",     "Surgelés"),
                ("Frites surgelées",    1,    "kg",     "Surgelés"),
            ],
        },
    ]

    for b in bundles:
        existing = conn.execute(
            "SELECT id FROM shopping_bundles WHERE name=?", (b["name"],)
        ).fetchone()
        if existing:
            print(f"  Bundle '{b['name']}' déjà présent → skip")
            continue

        cur = conn.execute(
            "INSERT INTO shopping_bundles (name, icon, position) VALUES (?, ?, ?)",
            (b["name"], b["icon"], b["position"]),
        )
        bundle_id = cur.lastrowid
        print(f"  ✓ Bundle '{b['name']}' créé (id={bundle_id})")

        for pos, (name, qty, unit, category) in enumerate(b["items"], 1):
            conn.execute(
                """INSERT INTO shopping_bundle_items (bundle_id, name, qty, unit, category, position)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (bundle_id, name, qty, unit, category, pos),
            )
        print(f"    → {len(b['items'])} articles insérés")

    conn.commit()


def seed_recipes(conn):
    print("\n── Recettes ──")

    recipes = [
        {
            "code":          "poulet-cajun-riz",
            "name":          "Poulet cajun au riz complet",
            "category":      "Plat",
            "origin":        "Américain",
            "base_servings": 4,
            "is_batch":      1,
            "notes":         "Se conserve 4 jours au frigo. Parfait pour le batch cooking du dimanche.",
            "ingredients": [
                ("Blanc de poulet",  800,  "g",      False, None),
                ("Riz complet",      400,  "g",      False, None),
                ("Épices cajun",     2,    "cs",     False, None),
                ("Huile d'olive",    2,    "cs",     False, None),
                ("Ail",              2,    "gousse", False, None),
                ("Sel",              None, None,     False, None),
                ("Poivre",           None, None,     False, None),
            ],
            "steps": [
                (1, "Cuisson du riz",    "Rincer le riz complet. Le cuire dans 800 ml d'eau salée pendant 35-40 min à feu doux.", 40, ["Riz complet"]),
                (2, "Préparation poulet","Couper les blancs de poulet en morceaux. Mélanger avec les épices cajun, le sel et le poivre.",  5, ["Blanc de poulet", "Épices cajun", "Sel", "Poivre"]),
                (3, "Cuisson poulet",    "Faire chauffer l'huile dans une poêle à feu vif. Faire revenir l'ail écrasé 1 min puis ajouter le poulet. Cuire 8-10 min en remuant jusqu'à coloration.", 12, ["Huile d'olive", "Ail", "Blanc de poulet"]),
                (4, "Dressage",          "Servir le poulet sur le riz. Peut être réparti en boîtes pour la semaine.",                       2, []),
            ],
        },
        {
            "code":          "pates-poulet-creme",
            "name":          "Pâtes poulet à la crème",
            "category":      "Plat",
            "origin":        None,
            "base_servings": 2,
            "is_batch":      0,
            "notes":         "Prêt en 20 min.",
            "ingredients": [
                ("Pâtes",            200,  "g",  False, None),
                ("Blanc de poulet",  300,  "g",  False, None),
                ("Crème fraîche",    20,   "cl", False, None),
                ("Fromage râpé",     50,   "g",  True,  "Optionnel pour gratiner"),
                ("Ail",              1,    "gousse", False, None),
                ("Huile d'olive",    1,    "cs", False, None),
                ("Sel",              None, None, False, None),
                ("Poivre",           None, None, False, None),
            ],
            "steps": [
                (1, "Cuisson pâtes",   "Faire bouillir une grande casserole d'eau salée. Cuire les pâtes al dente selon le paquet.", 10, ["Pâtes"]),
                (2, "Cuisson poulet",  "Couper le poulet en lamelles. Faire revenir dans l'huile avec l'ail écrasé, saler et poivrer. 6-8 min à feu moyen.", 8, ["Blanc de poulet", "Ail", "Huile d'olive", "Sel", "Poivre"]),
                (3, "Sauce",           "Baisser le feu, ajouter la crème fraîche. Laisser réduire 2-3 min en mélangeant.", 3, ["Crème fraîche"]),
                (4, "Assemblage",      "Égoutter les pâtes, les mélanger à la sauce. Servir avec le fromage râpé si souhaité.", 2, ["Fromage râpé"]),
            ],
        },
        {
            "code":          "riz-boeuf-hache",
            "name":          "Riz complet au bœuf haché",
            "category":      "Plat",
            "origin":        None,
            "base_servings": 4,
            "is_batch":      1,
            "notes":         "Batch cooking. Se conserve 4 jours au frigo.",
            "ingredients": [
                ("Riz complet",      400,  "g",  False, None),
                ("Bœuf haché",       600,  "g",  False, None),
                ("Ail",              3,    "gousse", False, None),
                ("Sauce soja",       3,    "cs", False, None),
                ("Huile d'olive",    1,    "cs", False, None),
                ("Sel",              None, None, False, None),
                ("Poivre",           None, None, False, None),
            ],
            "steps": [
                (1, "Riz",         "Rincer le riz et le cuire dans 800 ml d'eau salée, 35-40 min à feu doux.", 40, ["Riz complet"]),
                (2, "Bœuf",        "Faire chauffer l'huile à feu vif. Faire revenir l'ail écrasé puis ajouter le bœuf haché. Émietter et cuire jusqu'à ce qu'il soit bien doré (8-10 min).", 10, ["Bœuf haché", "Ail", "Huile d'olive"]),
                (3, "Assaisonnement", "Ajouter la sauce soja, saler légèrement (la sauce soja est déjà salée), poivrer. Mélanger 1 min à feu vif.", 2, ["Sauce soja", "Sel", "Poivre"]),
                (4, "Service",     "Mélanger le bœuf au riz ou servir séparément. Répartir en boîtes pour la semaine.", 2, []),
            ],
        },
    ]

    for r in recipes:
        existing = conn.execute(
            "SELECT id FROM recipes WHERE code=?", (r["code"],)
        ).fetchone()
        if existing:
            print(f"  Recette '{r['name']}' déjà présente → skip")
            continue

        cur = conn.execute(
            """INSERT INTO recipes (code, name, category, origin, base_servings, is_batch, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (r["code"], r["name"], r["category"], r["origin"],
             r["base_servings"], r["is_batch"], r["notes"]),
        )
        recipe_id = cur.lastrowid
        print(f"  ✓ Recette '{r['name']}' créée (id={recipe_id})")

        # Ingrédients → catalogue + recipe_ingredients
        ing_map = {}  # name → recipe_ingredient id
        for name, qty, unit, optional, notes in r["ingredients"]:
            ing_id = get_or_create_ingredient(conn, name, default_unit=unit)
            cur2 = conn.execute(
                """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, qty, unit, optional, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (recipe_id, ing_id, qty, unit, 1 if optional else 0, notes),
            )
            ing_map[name] = cur2.lastrowid

        # Étapes + liaisons ingrédients
        for step_no, title, instruction, time_min, linked_names in r["steps"]:
            cur3 = conn.execute(
                """INSERT INTO steps (recipe_id, step_no, title, instruction, time_min)
                   VALUES (?, ?, ?, ?, ?)""",
                (recipe_id, step_no, title, instruction, time_min),
            )
            step_id = cur3.lastrowid
            for ing_name in linked_names:
                ri_id = ing_map.get(ing_name)
                if ri_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO step_ingredients (step_id, recipe_ingredient_id) VALUES (?, ?)",
                        (step_id, ri_id),
                    )

        print(f"    → {len(r['ingredients'])} ingrédients, {len(r['steps'])} étapes")

    conn.commit()


def set_always_home(conn):
    """Marque sel, poivre, huile comme 'toujours chez soi'."""
    always_home = ["sel", "poivre", "huile d'olive", "huile"]
    for name in always_home:
        conn.execute(
            "UPDATE ingredient_catalog SET show_qty_in_list=0 WHERE norm_name=?",
            (normalize(name),),
        )
    conn.commit()
    print(f"\n── Articles 'toujours chez soi' marqués : {', '.join(always_home)}")


def seed_categories(conn):
    """Affecte une catégorie/rayon à chaque ingrédient du catalogue."""
    print("\n── Catégories ingrédients ──")
    mappings = [
        ("Boucherie",        ["blanc de poulet", "boeuf hache", "poulet surgele"]),
        ("Frais",            ["creme fraiche", "fromage rape", "yaourt nature", "oeuf", "beurre", "lait"]),
        ("Épicerie",         ["riz complet", "pates", "huile d'olive", "sauce soja", "miel",
                               "epices cajun", "cafe", "pain de mie", "sel", "poivre", "ail"]),
        ("Surgelés",         ["frites surgelees", "poulet surgele"]),
        ("Boissons",         ["eau gazeuse", "jus d'orange"]),
        ("Hygiène",          ["papier toilette", "liquide vaisselle", "lessive", "deodorant", "gel douche"]),
    ]
    updated = 0
    for category, names in mappings:
        for name in names:
            cur = conn.execute(
                "UPDATE ingredient_catalog SET category=? WHERE norm_name=?",
                (category, normalize(name)),
            )
            updated += cur.rowcount
    conn.commit()
    print(f"  ✓ {updated} ingrédients mis à jour")


if __name__ == "__main__":
    print(f"DB : {DB_FILE}")
    conn = get_conn()

    # Init schéma complet (idempotent)
    print("── Initialisation du schéma ──")
    import db as appdb
    appdb.ensure_schema(conn)
    conn.commit()
    print("  ✓ Schéma OK")

    seed_bundles(conn)
    seed_recipes(conn)
    set_always_home(conn)
    seed_categories(conn)
    conn.close()
    print("\n✅ Seed terminé.\n")
