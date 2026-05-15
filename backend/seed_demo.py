"""
Seed démo — AppCook
Lance avec : python seed_demo.py

Peuple la DB avec des données de démonstration :
  - Bundles courses (Petit / Moyen / Grand)
  - 15 recettes variées (entrées, plats, desserts, petit-déj)

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
        # ── Petit-déjeuner ──────────────────────────────────────────────────
        {
            "code":          "granola-maison",
            "name":          "Granola maison",
            "category":      "Petit-déjeuner",
            "origin":        None,
            "base_servings": 6,
            "is_batch":      1,
            "notes":         "Se conserve 3 semaines dans une boîte hermétique. Parfait pour préparer la semaine.",
            "ingredients": [
                ("Flocons d'avoine",  400, "g",     False, None),
                ("Miel",              4,   "cs",    False, None),
                ("Huile de coco",     3,   "cs",    False, None),
                ("Noix de cajou",     80,  "g",     True,  None),
                ("Amandes effilées",  80,  "g",     True,  None),
                ("Raisins secs",      60,  "g",     True,  None),
                ("Cannelle",          1,   "cc",    False, None),
            ],
            "steps": [
                (1, "Préchauffage", "Préchauffer le four à 160°C. Tapisser une plaque de cuisson de papier sulfurisé.", 5, []),
                (2, "Mélange",      "Dans un grand bol, mélanger les flocons d'avoine, la cannelle, les noix et les amandes. Ajouter l'huile de coco fondue et le miel. Bien mélanger jusqu'à ce que tout soit enrobé.", 5, ["Flocons d'avoine", "Miel", "Huile de coco", "Noix de cajou", "Amandes effilées", "Cannelle"]),
                (3, "Cuisson",      "Étaler uniformément sur la plaque. Enfourner 25-30 min en mélangeant à mi-cuisson jusqu'à coloration dorée.", 30, []),
                (4, "Finition",     "Laisser refroidir complètement sur la plaque (il durcit en refroidissant). Ajouter les raisins secs une fois refroidi. Conserver en boîte hermétique.", 10, ["Raisins secs"]),
            ],
        },
        {
            "code":          "pancakes-moelleux",
            "name":          "Pancakes moelleux",
            "category":      "Petit-déjeuner",
            "origin":        "Américain",
            "base_servings": 2,
            "is_batch":      0,
            "notes":         "Servir avec du sirop d'érable ou de la confiture.",
            "ingredients": [
                ("Farine",           150, "g",     False, None),
                ("Lait",             200, "ml",    False, None),
                ("Œufs",             2,   "pièce", False, None),
                ("Sucre",            2,   "cs",    False, None),
                ("Levure chimique",  1,   "cc",    False, None),
                ("Beurre",           30,  "g",     False, None),
                ("Sel",              None, None,   False, None),
                ("Sirop d'érable",   None, None,   True,  "Pour servir"),
            ],
            "steps": [
                (1, "Pâte",       "Dans un bol, mélanger la farine, le sucre, la levure et une pincée de sel. Creuser un puits, y ajouter les œufs battus et le lait. Mélanger sans trop travailler. Incorporer le beurre fondu. Laisser reposer 5 min.", 10, ["Farine", "Lait", "Œufs", "Sucre", "Levure chimique", "Beurre", "Sel"]),
                (2, "Cuisson",    "Chauffer une poêle antiadhésive à feu moyen. Verser une petite louche de pâte. Cuire jusqu'à ce que des bulles se forment en surface (2-3 min), retourner et cuire encore 1 min. Répéter.", 15, []),
                (3, "Service",    "Servir aussitôt avec du sirop d'érable ou de la confiture.", 2, ["Sirop d'érable"]),
            ],
        },
        # ── Entrées ─────────────────────────────────────────────────────────
        {
            "code":          "soupe-oignon",
            "name":          "Soupe à l'oignon gratinée",
            "category":      "Entrée",
            "origin":        "Français",
            "base_servings": 4,
            "is_batch":      1,
            "notes":         "Se congèle très bien (sans le gratin). Préparer en grande quantité.",
            "ingredients": [
                ("Oignons",           1,    "kg",    False, None),
                ("Beurre",            40,   "g",     False, None),
                ("Bouillon de bœuf",  1,    "l",     False, None),
                ("Gruyère râpé",      120,  "g",     False, None),
                ("Pain de campagne",  4,    "tranche", False, None),
                ("Farine",            1,    "cs",    False, None),
                ("Vin blanc sec",     10,   "cl",    True,  None),
                ("Sel",               None, None,    False, None),
                ("Poivre",            None, None,    False, None),
            ],
            "steps": [
                (1, "Caramélisation", "Éplucher et émincer finement les oignons. Faire fondre le beurre dans une grande casserole à feu moyen-doux. Ajouter les oignons et cuire 40-45 min en remuant régulièrement jusqu'à coloration dorée profonde.", 45, ["Oignons", "Beurre"]),
                (2, "Base soupe",     "Singer avec la farine (saupoudrer et mélanger 1 min). Déglacer au vin blanc si souhaité. Verser le bouillon, saler, poivrer. Laisser mijoter 20 min à feu doux.", 22, ["Farine", "Vin blanc sec", "Bouillon de bœuf", "Sel", "Poivre"]),
                (3, "Gratin",         "Préchauffer le grill du four. Répartir la soupe dans des bols allant au four. Poser une tranche de pain sur chaque bol, couvrir de gruyère râpé. Passer sous le grill 3-4 min jusqu'à gratinage.", 5, ["Pain de campagne", "Gruyère râpé"]),
            ],
        },
        {
            "code":          "bruschetta-tomate",
            "name":          "Bruschetta tomate basilic",
            "category":      "Entrée",
            "origin":        "Italien",
            "base_servings": 4,
            "is_batch":      0,
            "notes":         "À préparer juste avant de servir pour que le pain reste croustillant.",
            "ingredients": [
                ("Pain ciabatta",    1,    "pièce", False, None),
                ("Tomates",          4,    "pièce", False, None),
                ("Basilic frais",    1,    "pièce", False, None),
                ("Ail",              2,    "gousse", False, None),
                ("Huile d'olive",    3,    "cs",    False, None),
                ("Sel",              None, None,    False, None),
                ("Poivre",           None, None,    False, None),
            ],
            "steps": [
                (1, "Tomates",  "Couper les tomates en petits dés, égoutter l'excès de jus. Ciseler le basilic. Mélanger avec l'huile d'olive, saler, poivrer. Laisser mariner 10 min.", 12, ["Tomates", "Basilic frais", "Huile d'olive", "Sel", "Poivre"]),
                (2, "Pain",     "Couper le ciabatta en tranches épaisses. Faire griller au four (180°C, 5-7 min) ou à la poêle jusqu'à ce qu'il soit doré et croustillant.", 8, ["Pain ciabatta"]),
                (3, "Montage",  "Frotter chaque tranche de pain avec une gousse d'ail coupée. Garnir généreusement avec la préparation tomate-basilic. Servir immédiatement.", 3, ["Ail"]),
            ],
        },
        {
            "code":          "veloute-butternut",
            "name":          "Velouté de butternut",
            "category":      "Entrée",
            "origin":        "Français",
            "base_servings": 4,
            "is_batch":      1,
            "notes":         "Se congèle parfaitement. Ajouter la crème au moment de servir.",
            "ingredients": [
                ("Courge butternut",  1,    "pièce", False, None),
                ("Oignons",           1,    "pièce", False, None),
                ("Bouillon de légumes", 800, "ml",   False, None),
                ("Crème fraîche",     10,   "cl",    True,  "Pour servir"),
                ("Huile d'olive",     2,    "cs",    False, None),
                ("Noix de muscade",   None, None,    False, None),
                ("Sel",               None, None,    False, None),
                ("Poivre",            None, None,    False, None),
                ("Graines de courge", None, None,    True,  "Pour la déco"),
            ],
            "steps": [
                (1, "Légumes",   "Éplucher et couper la courge en cubes. Émincer l'oignon. Faire revenir l'oignon dans l'huile d'olive 3-4 min. Ajouter la courge et mélanger.", 8, ["Courge butternut", "Oignons", "Huile d'olive"]),
                (2, "Cuisson",   "Verser le bouillon. Porter à ébullition puis laisser mijoter 20 min à feu moyen jusqu'à ce que la courge soit tendre.", 22, ["Bouillon de légumes"]),
                (3, "Mixage",    "Mixer finement. Assaisonner avec sel, poivre et une pincée de muscade. Ajuster la consistance avec un peu d'eau si nécessaire.", 5, ["Sel", "Poivre", "Noix de muscade"]),
                (4, "Service",   "Servir bien chaud avec un filet de crème fraîche et quelques graines de courge grillées.", 2, ["Crème fraîche", "Graines de courge"]),
            ],
        },
        # ── Plats ───────────────────────────────────────────────────────────
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
                (1, "Cuisson du riz",    "Rincer le riz complet. Le cuire dans 800 ml d'eau salée pendant 35-40 min à feu doux.",                                                                                                                      40, ["Riz complet"]),
                (2, "Préparation poulet","Couper les blancs de poulet en morceaux. Mélanger avec les épices cajun, le sel et le poivre.",                                                                                                               5,  ["Blanc de poulet", "Épices cajun", "Sel", "Poivre"]),
                (3, "Cuisson poulet",    "Faire chauffer l'huile dans une poêle à feu vif. Faire revenir l'ail écrasé 1 min puis ajouter le poulet. Cuire 8-10 min en remuant jusqu'à coloration.",                                                    12, ["Huile d'olive", "Ail", "Blanc de poulet"]),
                (4, "Dressage",          "Servir le poulet sur le riz. Peut être réparti en boîtes pour la semaine.",                                                                                                                                   2,  []),
            ],
        },
        {
            "code":          "risotto-champignons",
            "name":          "Risotto aux champignons",
            "category":      "Plat",
            "origin":        "Italien",
            "base_servings": 2,
            "is_batch":      0,
            "notes":         "Le secret du risotto : ajouter le bouillon louche par louche et ne jamais arrêter de remuer.",
            "ingredients": [
                ("Riz arborio",          200, "g",     False, None),
                ("Champignons de Paris", 300, "g",     False, None),
                ("Bouillon de légumes",  700, "ml",    False, None),
                ("Parmesan",             60,  "g",     False, None),
                ("Beurre",               30,  "g",     False, None),
                ("Oignon",               1,   "pièce", False, None),
                ("Huile d'olive",        2,   "cs",    False, None),
                ("Vin blanc sec",        10,  "cl",    True,  None),
                ("Sel",                  None, None,   False, None),
                ("Poivre",               None, None,   False, None),
            ],
            "steps": [
                (1, "Préparation",   "Émincer l'oignon. Couper les champignons en lamelles. Maintenir le bouillon chaud dans une casserole à feu doux.", 5, ["Bouillon de légumes", "Oignon", "Champignons de Paris"]),
                (2, "Champignons",   "Dans une grande poêle, faire revenir les champignons dans l'huile d'olive à feu vif 5 min jusqu'à coloration. Réserver.", 6, ["Champignons de Paris", "Huile d'olive"]),
                (3, "Nacrer le riz", "Dans la même poêle, faire revenir l'oignon 3 min. Ajouter le riz et nacrer 2 min en remuant. Déglacer au vin blanc et laisser absorber.", 6, ["Oignon", "Riz arborio", "Vin blanc sec"]),
                (4, "Cuisson",       "Ajouter le bouillon chaud louche par louche en remuant constamment. Attendre que chaque louche soit absorbée avant d'en ajouter une autre. Compter 18-20 min.", 20, ["Bouillon de légumes"]),
                (5, "Finition",      "Incorporer les champignons réservés, le beurre et le parmesan. Mélanger vigoureusement. Assaisonner. Couvrir 2 min avant de servir.", 4, ["Champignons de Paris", "Beurre", "Parmesan", "Sel", "Poivre"]),
            ],
        },
        {
            "code":          "curry-legumes-pois-chiches",
            "name":          "Curry de légumes aux pois chiches",
            "category":      "Plat",
            "origin":        "Indien",
            "base_servings": 4,
            "is_batch":      1,
            "notes":         "Végétarien, se conserve 4 jours. Encore meilleur le lendemain.",
            "ingredients": [
                ("Pois chiches en boîte", 2,   "pièce", False, None),
                ("Tomates concassées",    400,  "g",    False, None),
                ("Lait de coco",          400,  "ml",   False, None),
                ("Poudre de curry",       2,    "cs",   False, None),
                ("Oignon",                1,    "pièce", False, None),
                ("Ail",                   3,    "gousse", False, None),
                ("Gingembre frais",       1,    "pièce", True,  None),
                ("Riz basmati",           300,  "g",    False, None),
                ("Huile d'olive",         2,    "cs",   False, None),
                ("Sel",                   None, None,   False, None),
                ("Coriandre fraîche",     None, None,   True,  "Pour servir"),
            ],
            "steps": [
                (1, "Cuisson du riz",  "Rincer le riz basmati. Cuire dans 600 ml d'eau salée, 12 min à feu doux à couvert. Laisser reposer 5 min.", 18, ["Riz basmati"]),
                (2, "Aromates",        "Émincer l'oignon, hacher l'ail et râper le gingembre. Faire revenir dans l'huile d'olive 4-5 min à feu moyen.", 6, ["Oignon", "Ail", "Gingembre frais", "Huile d'olive"]),
                (3, "Curry",           "Ajouter la poudre de curry, mélanger 1 min. Verser les tomates concassées et le lait de coco. Porter à légère ébullition.", 5, ["Poudre de curry", "Tomates concassées", "Lait de coco"]),
                (4, "Pois chiches",    "Égoutter et rincer les pois chiches, les ajouter à la sauce. Laisser mijoter 15 min à feu doux. Saler.", 15, ["Pois chiches en boîte", "Sel"]),
                (5, "Service",         "Servir sur le riz avec de la coriandre fraîche ciselée.", 2, ["Riz basmati", "Coriandre fraîche"]),
            ],
        },
        {
            "code":          "saumon-plancha-citron",
            "name":          "Saumon à la plancha, citron et herbes",
            "category":      "Plat",
            "origin":        None,
            "base_servings": 2,
            "is_batch":      0,
            "notes":         "Choisir des pavés de saumon avec peau pour un meilleur résultat.",
            "ingredients": [
                ("Filet de saumon",  2,    "pièce", False, None),
                ("Citron",           1,    "pièce", False, None),
                ("Huile d'olive",    2,    "cs",    False, None),
                ("Aneth frais",      None, None,    True,  None),
                ("Ciboulette",       None, None,    True,  None),
                ("Sel",              None, None,    False, None),
                ("Poivre",           None, None,    False, None),
            ],
            "steps": [
                (1, "Préparation", "Sortir le saumon du frigo 15 min avant cuisson. Sécher les filets avec du papier absorbant. Badigeonner d'huile d'olive, saler, poivrer.", 3, ["Filet de saumon", "Huile d'olive", "Sel", "Poivre"]),
                (2, "Cuisson",     "Chauffer une plancha ou poêle à feu très vif. Poser le saumon côté peau en premier. Cuire 3-4 min sans y toucher jusqu'à ce que la peau soit croustillante. Retourner et cuire 2 min côté chair (le cœur reste rosé).", 7, ["Filet de saumon"]),
                (3, "Service",     "Presser le citron sur le saumon. Parsemer d'aneth et de ciboulette ciselés. Servir immédiatement avec une salade verte ou des légumes vapeur.", 2, ["Citron", "Aneth frais", "Ciboulette"]),
            ],
        },
        {
            "code":          "tacos-poulet-avocat",
            "name":          "Tacos au poulet et à l'avocat",
            "category":      "Plat",
            "origin":        "Mexicain",
            "base_servings": 4,
            "is_batch":      0,
            "notes":         "Servir avec les garnitures au milieu de la table pour que chacun compose son taco.",
            "ingredients": [
                ("Blanc de poulet",  600,  "g",     False, None),
                ("Tortillas de blé", 8,    "pièce", False, None),
                ("Avocat",           2,    "pièce", False, None),
                ("Oignon rouge",     1,    "pièce", False, None),
                ("Citron vert",      2,    "pièce", False, None),
                ("Coriandre fraîche",None,  None,   True,  None),
                ("Crème fraîche",    10,   "cl",    True,  None),
                ("Paprika fumé",     1,    "cc",    False, None),
                ("Cumin",            1,    "cc",    False, None),
                ("Huile d'olive",    2,    "cs",    False, None),
                ("Sel",              None, None,    False, None),
            ],
            "steps": [
                (1, "Marinade",    "Couper le poulet en lamelles. Mélanger avec le paprika, le cumin, le sel et 1 cs d'huile. Laisser mariner 10 min.", 12, ["Blanc de poulet", "Paprika fumé", "Cumin", "Sel", "Huile d'olive"]),
                (2, "Guacamole",   "Écraser les avocats à la fourchette. Incorporer le jus d'un citron vert, saler. Ajouter l'oignon rouge émincé finement.", 5, ["Avocat", "Citron vert", "Oignon rouge"]),
                (3, "Cuisson",     "Cuire le poulet dans une poêle très chaude avec l'huile restante, 6-8 min en remuant jusqu'à légère caramélisation.", 8, ["Blanc de poulet", "Huile d'olive"]),
                (4, "Tortillas",   "Chauffer les tortillas 30 secondes de chaque côté dans une poêle sèche ou directement à la flamme du gaz.", 3, ["Tortillas de blé"]),
                (5, "Montage",     "Garnir chaque tortilla de guacamole, poulet, coriandre ciselée et un trait de crème. Servir avec le reste du citron vert.", 3, ["Guacamole", "Coriandre fraîche", "Crème fraîche", "Citron vert"]),
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
                ("Pâtes",            200,  "g",      False, None),
                ("Blanc de poulet",  300,  "g",      False, None),
                ("Crème fraîche",    20,   "cl",     False, None),
                ("Fromage râpé",     50,   "g",      True,  "Optionnel pour gratiner"),
                ("Ail",              1,    "gousse", False, None),
                ("Huile d'olive",    1,    "cs",     False, None),
                ("Sel",              None, None,     False, None),
                ("Poivre",           None, None,     False, None),
            ],
            "steps": [
                (1, "Cuisson pâtes",  "Faire bouillir une grande casserole d'eau salée. Cuire les pâtes al dente selon le paquet.", 10, ["Pâtes"]),
                (2, "Cuisson poulet", "Couper le poulet en lamelles. Faire revenir dans l'huile avec l'ail écrasé, saler et poivrer. 6-8 min à feu moyen.", 8, ["Blanc de poulet", "Ail", "Huile d'olive", "Sel", "Poivre"]),
                (3, "Sauce",          "Baisser le feu, ajouter la crème fraîche. Laisser réduire 2-3 min en mélangeant.", 3, ["Crème fraîche"]),
                (4, "Assemblage",     "Égoutter les pâtes, les mélanger à la sauce. Servir avec le fromage râpé si souhaité.", 2, ["Fromage râpé"]),
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
                ("Riz complet",      400,  "g",      False, None),
                ("Bœuf haché",       600,  "g",      False, None),
                ("Ail",              3,    "gousse", False, None),
                ("Sauce soja",       3,    "cs",     False, None),
                ("Huile d'olive",    1,    "cs",     False, None),
                ("Sel",              None, None,     False, None),
                ("Poivre",           None, None,     False, None),
            ],
            "steps": [
                (1, "Riz",            "Rincer le riz et le cuire dans 800 ml d'eau salée, 35-40 min à feu doux.", 40, ["Riz complet"]),
                (2, "Bœuf",           "Faire chauffer l'huile à feu vif. Faire revenir l'ail écrasé puis ajouter le bœuf haché. Émietter et cuire jusqu'à ce qu'il soit bien doré (8-10 min).", 10, ["Bœuf haché", "Ail", "Huile d'olive"]),
                (3, "Assaisonnement", "Ajouter la sauce soja, saler légèrement, poivrer. Mélanger 1 min à feu vif.", 2, ["Sauce soja", "Sel", "Poivre"]),
                (4, "Service",        "Mélanger le bœuf au riz ou servir séparément. Répartir en boîtes pour la semaine.", 2, []),
            ],
        },
        # ── Desserts ────────────────────────────────────────────────────────
        {
            "code":          "crepes-classiques",
            "name":          "Crêpes classiques",
            "category":      "Dessert",
            "origin":        "Français",
            "base_servings": 4,
            "is_batch":      0,
            "notes":         "La pâte peut être préparée la veille et conservée au frigo. Servir avec du sucre, de la confiture ou du Nutella.",
            "ingredients": [
                ("Farine",        250,  "g",     False, None),
                ("Lait",          500,  "ml",    False, None),
                ("Œufs",          3,    "pièce", False, None),
                ("Beurre",        30,   "g",     False, None),
                ("Sucre",         1,    "cs",    False, None),
                ("Sel",           None, None,    False, None),
                ("Rhum",          1,    "cs",    True,  "Pour parfumer"),
            ],
            "steps": [
                (1, "Pâte",     "Dans un saladier, mélanger la farine, le sucre et le sel. Creuser un puits, ajouter les œufs et la moitié du lait. Fouetter en partant du centre pour obtenir une pâte lisse. Ajouter le reste du lait, le beurre fondu et le rhum. Laisser reposer 30 min.", 35, ["Farine", "Lait", "Œufs", "Beurre", "Sucre", "Sel", "Rhum"]),
                (2, "Cuisson",  "Chauffer une crêpière légèrement beurrée à feu moyen-vif. Verser une petite louche de pâte en inclinant pour répartir. Cuire jusqu'à ce que les bords se décollent (1-2 min), retourner et cuire 30 sec. Empiler les crêpes sur une assiette.", 20, []),
                (3, "Service",  "Servir chaudes avec les garnitures au choix.", 2, []),
            ],
        },
        {
            "code":          "mousse-chocolat",
            "name":          "Mousse au chocolat",
            "category":      "Dessert",
            "origin":        "Français",
            "base_servings": 4,
            "is_batch":      0,
            "notes":         "Préparer à l'avance — se conserve 24h au frigo. Utiliser du chocolat noir 70% pour un résultat optimal.",
            "ingredients": [
                ("Chocolat noir",  200, "g",     False, None),
                ("Œufs",           4,   "pièce", False, None),
                ("Sucre",          40,  "g",     False, None),
                ("Beurre",         20,  "g",     False, None),
            ],
            "steps": [
                (1, "Chocolat",     "Casser le chocolat en morceaux. Le faire fondre au bain-marie avec le beurre en remuant jusqu'à obtenir un mélange lisse. Laisser tiédir 5 min.", 10, ["Chocolat noir", "Beurre"]),
                (2, "Jaunes",       "Séparer les blancs des jaunes. Incorporer les jaunes un à un dans le chocolat fondu avec le sucre. Bien mélanger.", 5, ["Œufs", "Sucre"]),
                (3, "Blancs",       "Monter les blancs en neige ferme avec une pincée de sel. Incorporer délicatement au mélange chocolaté en plusieurs fois, en soulevant la masse.", 8, ["Œufs"]),
                (4, "Réfrigération","Répartir dans des verrines ou un grand bol. Réfrigérer au moins 2h avant de servir.", 120, []),
            ],
        },
        {
            "code":          "tarte-pommes-rapide",
            "name":          "Tarte aux pommes express",
            "category":      "Dessert",
            "origin":        "Français",
            "base_servings": 6,
            "is_batch":      0,
            "notes":         "Avec une pâte du commerce, cette tarte est prête en 45 min. Servir tiède avec une boule de glace vanille.",
            "ingredients": [
                ("Pâte brisée",  1,   "pièce", False, None),
                ("Pommes",       4,   "pièce", False, None),
                ("Sucre",        50,  "g",     False, None),
                ("Beurre",       30,  "g",     False, None),
                ("Cannelle",     1,   "cc",    True,  None),
                ("Confiture d'abricot", 2, "cs", True, "Pour le nappage"),
            ],
            "steps": [
                (1, "Préchauffage", "Préchauffer le four à 200°C. Étaler la pâte dans un moule à tarte, piquer le fond avec une fourchette.", 8, ["Pâte brisée"]),
                (2, "Pommes",       "Éplucher et épépiner les pommes. Les couper en fines lamelles régulières.", 8, ["Pommes"]),
                (3, "Garnissage",   "Disposer les lamelles de pomme en rosace sur la pâte. Saupoudrer de sucre et de cannelle. Déposer des petits morceaux de beurre sur les pommes.", 5, ["Pommes", "Sucre", "Cannelle", "Beurre"]),
                (4, "Cuisson",      "Enfourner 30-35 min jusqu'à ce que les pommes soient dorées et la pâte cuite.", 35, []),
                (5, "Nappage",      "Chauffer la confiture d'abricot avec 1 cs d'eau. Badigeonner les pommes pour les faire briller. Servir tiède.", 3, ["Confiture d'abricot"]),
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

        ing_map = {}
        for name, qty, unit, optional, notes in r["ingredients"]:
            ing_id = get_or_create_ingredient(conn, name, default_unit=unit)
            cur2 = conn.execute(
                """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, qty, unit, optional, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (recipe_id, ing_id, qty, unit, 1 if optional else 0, notes),
            )
            ing_map[name] = cur2.lastrowid

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
    always_home = ["sel", "poivre", "huile d'olive", "huile"]
    for name in always_home:
        conn.execute(
            "UPDATE ingredient_catalog SET show_qty_in_list=0 WHERE norm_name=?",
            (normalize(name),),
        )
    conn.commit()
    print(f"\n── Articles 'toujours chez soi' marqués : {', '.join(always_home)}")


def seed_categories(conn):
    print("\n── Catégories ingrédients ──")
    mappings = [
        ("Boucherie",       ["blanc de poulet", "boeuf hache", "poulet surgele", "filet de saumon"]),
        ("Frais",           ["creme fraiche", "fromage rape", "gruyere rape", "parmesan",
                              "yaourt nature", "oeuf", "beurre", "lait", "avocat",
                              "champignons de paris", "courge butternut", "oignon", "oignons",
                              "oignon rouge", "tomates"]),
        ("Épicerie",        ["riz complet", "riz arborio", "riz basmati", "pates", "tortillas de ble",
                              "huile d'olive", "huile de coco", "sauce soja", "miel", "sucre", "farine",
                              "epices cajun", "cafe", "pain de mie", "pain ciabatta", "pain de campagne",
                              "sel", "poivre", "ail", "cannelle", "cumin", "paprika fume", "poudre de curry",
                              "levure chimique", "chocolat noir", "pate brisee", "flocons d avoine",
                              "noix de cajou", "amandes effilees", "raisins secs", "tomates concassees",
                              "pois chiches en boite", "bouillon de legumes", "bouillon de boeuf",
                              "confiture d abricot", "sirop d erable"]),
        ("Surgelés",        ["frites surgelees", "poulet surgele"]),
        ("Boissons",        ["eau gazeuse", "jus d'orange", "vin blanc sec", "lait de coco"]),
        ("Fruits & Légumes",["pommes", "citron", "citron vert", "tomates", "courge butternut",
                              "oignon", "oignons", "oignon rouge", "ail", "gingembre frais",
                              "basilic frais", "coriandre fraiche", "aneth frais", "ciboulette"]),
        ("Hygiène",         ["papier toilette", "liquide vaisselle", "lessive", "deodorant", "gel douche"]),
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
    print("\n✅ Seed démo terminé.\n")
