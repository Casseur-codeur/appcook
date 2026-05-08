"""
AppCook — API FastAPI v2
"""
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import db


# =============================================================================
# Lifespan — initialisation DB au démarrage
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = db.get_conn()
    db.ensure_schema(conn)
    conn.close()
    yield


app = FastAPI(title="AppCook API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Modèles Pydantic
# =============================================================================

class RecipeBase(BaseModel):
    name: str
    category: Optional[str] = ""
    origin: Optional[str] = ""
    base_servings: float = 1.0
    is_batch: bool = False
    notes: Optional[str] = ""


class StepIn(BaseModel):
    step_no: int
    title: Optional[str] = ""
    instruction: str
    time_min: Optional[float] = None
    ingredient_ids: Optional[List[int]] = []


class RecipeIn(RecipeBase):
    steps: Optional[List[StepIn]] = []


class IngredientIn(BaseModel):
    name: str
    qty: Optional[float] = None
    unit: Optional[str] = ""
    optional: bool = False
    notes: Optional[str] = ""


class ShoppingRequest(BaseModel):
    recipe_codes: List[str]
    persons: float = 1.0
    include_optional: bool = False


class CatalogUpdate(BaseModel):
    default_unit: Optional[str] = None
    show_qty_in_list: Optional[bool] = None
    category: Optional[str] = None


class MergeRequest(BaseModel):
    canonical_id: int
    duplicate_ids: List[int]


class ImportRequest(BaseModel):
    data: Dict[str, Any]
    on_conflict: str = "rename"


class BundleIn(BaseModel):
    name: str
    icon: Optional[str] = "🛒"
    position: int = 0


class BundleItemIn(BaseModel):
    name: str
    qty: Optional[float] = None
    unit: Optional[str] = ""
    category: Optional[str] = "Divers"
    position: int = 0


class GenerateShoppingRequest(BaseModel):
    recipe_codes: Optional[List[str]] = []
    persons: float = 1.0
    bundle_id: Optional[int] = None
    manual_items: Optional[List[Dict[str, Any]]] = []
    include_optional: bool = False


class ToggleItemRequest(BaseModel):
    checked: bool
    missing: bool = False


class AddManualItemRequest(BaseModel):
    name: str
    qty: Optional[float] = None
    unit: Optional[str] = ""
    category: Optional[str] = "Divers"


class FullIngredientIn(BaseModel):
    name: str
    qty: Optional[float] = None
    unit: Optional[str] = ""
    optional: bool = False
    notes: Optional[str] = ""


class FullStepIn(BaseModel):
    step_no: int = 1
    title: Optional[str] = ""
    instruction: str
    time_min: Optional[float] = None
    ingredient_names: Optional[List[str]] = []


class FullRecipeIn(BaseModel):
    name: str
    category: Optional[str] = ""
    origin: Optional[str] = ""
    base_servings: float = 1.0
    is_batch: bool = False
    notes: Optional[str] = ""
    ingredients: Optional[List[FullIngredientIn]] = []
    steps: Optional[List[FullStepIn]] = []


class SettingsUpdate(BaseModel):
    weekly_goal: Optional[int] = None
    # Extensible : ajouter d'autres clés ici


# =============================================================================
# Routes — Recettes
# =============================================================================

@app.get("/api/recipes")
def list_recipes(
    time_max: Optional[int] = Query(None, description="Temps max en minutes"),
    is_batch: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
):
    """Liste les recettes avec filtres optionnels."""
    conn = db.get_conn()
    try:
        return db.load_recipes_filtered(conn, time_max=time_max, is_batch=is_batch,
                                        category=category, origin=origin)
    finally:
        conn.close()


@app.get("/api/recipes/suggest")
def suggest(time_max: Optional[int] = Query(None)):
    """Retourne une suggestion de recette intelligente."""
    conn = db.get_conn()
    try:
        recipe = db.suggest_recipe(conn, time_max=time_max)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Aucune recette disponible")
        return recipe
    finally:
        conn.close()


@app.get("/api/recipes/{code}")
def get_recipe(code: str):
    """Détail complet d'une recette (steps + ingrédients)."""
    conn = db.get_conn()
    try:
        recipe = db.get_recipe_detail(conn, code)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recette introuvable")
        return recipe
    finally:
        conn.close()


@app.post("/api/recipes", status_code=201)
def create_recipe(payload: RecipeIn):
    conn = db.get_conn()
    try:
        base_code = db._slugify_code(payload.name)
        code = db.make_unique_code(conn, base_code)
        db.insert_recipe(conn, code, payload.name, payload.category or "",
                         payload.origin or "", payload.base_servings,
                         payload.is_batch, payload.notes or "")
        recipe_id = db.get_recipe_id_by_code(conn, code)
        for step in (payload.steps or []):
            db.insert_step(conn, recipe_id, step.step_no, step.title or "",
                           step.instruction, step.time_min)
        return {"code": code}
    finally:
        conn.close()


@app.put("/api/recipes/{code}")
def update_recipe(code: str, payload: RecipeBase):
    conn = db.get_conn()
    try:
        if db.get_recipe_id_by_code(conn, code) is None:
            raise HTTPException(status_code=404, detail="Recette introuvable")
        db.update_recipe_by_code(conn, code, payload.name, payload.category or "",
                                 payload.origin or "", payload.base_servings,
                                 payload.is_batch, payload.notes or "")
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/recipes/{code}")
def delete_recipe(code: str):
    conn = db.get_conn()
    try:
        if db.get_recipe_id_by_code(conn, code) is None:
            raise HTTPException(status_code=404, detail="Recette introuvable")
        db.delete_recipe_by_code(conn, code)
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/recipes/{code}/export")
def export_recipe(code: str):
    conn = db.get_conn()
    try:
        return db.export_recipe_to_json_by_code(conn, code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        conn.close()


@app.post("/api/recipes/full", status_code=201)
def create_full_recipe(payload: FullRecipeIn):
    """Crée une recette complète avec ingrédients et étapes en une seule requête."""
    conn = db.get_conn()
    try:
        base_code = db._slugify_code(payload.name)
        code = db.make_unique_code(conn, base_code)
        db.insert_recipe(conn, code, payload.name, payload.category or "",
                         payload.origin or "", payload.base_servings,
                         payload.is_batch, payload.notes or "")
        db.replace_recipe_full(
            conn, code,
            payload.name, payload.category or "", payload.origin or "",
            payload.base_servings, payload.is_batch, payload.notes or "",
            [i.dict() for i in (payload.ingredients or [])],
            [s.dict() for s in (payload.steps or [])],
        )
        return {"code": code}
    finally:
        conn.close()


@app.put("/api/recipes/{code}/full")
def update_full_recipe(code: str, payload: FullRecipeIn):
    """Remplace entièrement une recette (métadonnées + ingrédients + étapes)."""
    conn = db.get_conn()
    try:
        if db.get_recipe_id_by_code(conn, code) is None:
            raise HTTPException(status_code=404, detail="Recette introuvable")
        db.replace_recipe_full(
            conn, code,
            payload.name, payload.category or "", payload.origin or "",
            payload.base_servings, payload.is_batch, payload.notes or "",
            [i.dict() for i in (payload.ingredients or [])],
            [s.dict() for s in (payload.steps or [])],
        )
        return {"ok": True, "code": code}
    finally:
        conn.close()


@app.post("/api/recipes/import", status_code=201)
def import_recipe(payload: ImportRequest):
    try:
        recipe_id = db.import_recipe_from_json(payload.data, on_code_conflict=payload.on_conflict)
        return {"recipe_id": recipe_id}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


# =============================================================================
# Routes — Catégories & Origines (pour alimenter les filtres)
# =============================================================================

@app.get("/api/categories")
def list_categories():
    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT category FROM recipes WHERE category IS NOT NULL AND category != '' ORDER BY category"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


@app.get("/api/origins")
def list_origins():
    conn = db.get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT origin FROM recipes WHERE origin IS NOT NULL AND origin != '' ORDER BY origin"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


# =============================================================================
# Routes — Cooking history
# =============================================================================

@app.post("/api/history/{code}", status_code=201)
def log_cook(code: str):
    """Enregistre une session de cuisine (appelé à la fin du Focus Mode)."""
    conn = db.get_conn()
    try:
        db.log_cook(conn, code)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        conn.close()


@app.get("/api/history")
def get_history(limit: int = Query(20)):
    conn = db.get_conn()
    try:
        return db.get_cooking_history(conn, limit=limit)
    finally:
        conn.close()


# =============================================================================
# Routes — Shopping
# =============================================================================

@app.post("/api/shopping")
def generate_shopping_list(payload: ShoppingRequest):
    conn = db.get_conn()
    try:
        items, issues = db.aggregate_shopping_list(
            conn, payload.recipe_codes, payload.persons, payload.include_optional
        )
        return {"items": items, "issues": issues}
    finally:
        conn.close()


# =============================================================================
# Routes — Ingrédients (autocomplete)
# =============================================================================

@app.get("/api/ingredients/search")
def search_ingredients(q: str = Query(""), limit: int = Query(20)):
    conn = db.get_conn()
    try:
        rows = db.search_ingredients(conn, q, limit=limit)
        return [{"id": r[0], "name": r[1]} for r in rows]
    finally:
        conn.close()


# =============================================================================
# Routes — Catalogue
# =============================================================================

@app.get("/api/catalog")
def list_catalog():
    conn = db.get_conn()
    try:
        rows = db.list_catalog(conn)
        return [
            {"id": r[0], "name": r[1], "default_unit": r[2],
             "show_qty_in_list": bool(r[3]), "norm_name": r[4], "category": r[5]}
            for r in rows
        ]
    finally:
        conn.close()


@app.put("/api/catalog/{ingredient_id}")
def update_catalog(ingredient_id: int, payload: CatalogUpdate):
    conn = db.get_conn()
    try:
        if payload.default_unit is not None:
            db.set_catalog_default_unit(conn, ingredient_id, payload.default_unit)
        if payload.show_qty_in_list is not None:
            db.set_catalog_show_qty(conn, ingredient_id, 1 if payload.show_qty_in_list else 0)
        if payload.category is not None:
            db.set_catalog_category(conn, ingredient_id, payload.category)
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/catalog/merge")
def merge_catalog(payload: MergeRequest):
    conn = db.get_conn()
    try:
        merged = db.merge_ingredients(conn, payload.canonical_id, payload.duplicate_ids)
        return {"merged": merged}
    finally:
        conn.close()


# =============================================================================
# Routes — Bundles
# =============================================================================

@app.get("/api/bundles")
def list_bundles():
    conn = db.get_conn()
    try:
        return db.list_bundles(conn)
    finally:
        conn.close()


@app.post("/api/bundles", status_code=201)
def create_bundle(payload: BundleIn):
    conn = db.get_conn()
    try:
        bid = db.create_bundle(conn, payload.name, payload.icon or "🛒", payload.position)
        return {"id": bid}
    finally:
        conn.close()


@app.put("/api/bundles/{bundle_id}")
def update_bundle(bundle_id: int, payload: BundleIn):
    conn = db.get_conn()
    try:
        db.update_bundle(conn, bundle_id, payload.name, payload.icon or "🛒")
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/bundles/{bundle_id}")
def delete_bundle(bundle_id: int):
    conn = db.get_conn()
    try:
        db.delete_bundle(conn, bundle_id)
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/bundles/{bundle_id}/items", status_code=201)
def add_bundle_item(bundle_id: int, payload: BundleItemIn):
    conn = db.get_conn()
    try:
        item_id = db.add_bundle_item(
            conn, bundle_id, payload.name, payload.qty,
            payload.unit or "", payload.category or "Divers", payload.position,
        )
        return {"id": item_id}
    finally:
        conn.close()


@app.put("/api/bundles/{bundle_id}/items/{item_id}")
def update_bundle_item(bundle_id: int, item_id: int, payload: BundleItemIn):
    conn = db.get_conn()
    try:
        db.update_bundle_item(
            conn, item_id, payload.name, payload.qty,
            payload.unit or "", payload.category or "Divers",
        )
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/bundles/{bundle_id}/items/{item_id}")
def delete_bundle_item(bundle_id: int, item_id: int):
    conn = db.get_conn()
    try:
        db.delete_bundle_item(conn, item_id)
        return {"ok": True}
    finally:
        conn.close()


# =============================================================================
# Routes — Shopping list v2 (persistante)
# =============================================================================

@app.get("/api/shopping/current")
def get_current_list():
    """Retourne la liste de courses active (ou null si aucune)."""
    conn = db.get_conn()
    try:
        result = db.get_active_list(conn)
        return result or {}
    finally:
        conn.close()


@app.post("/api/shopping/generate", status_code=201)
def generate_list(payload: GenerateShoppingRequest):
    """Génère une nouvelle liste (recettes + bundle + items manuels) et la persiste.
    Retourne aussi les articles manquants de la liste précédente pour que le frontend
    propose à l'utilisateur de les inclure ou non."""
    conn = db.get_conn()
    try:
        active_list, issues, missing_from_previous = db.generate_shopping_list(
            conn,
            recipe_codes=payload.recipe_codes or [],
            persons=payload.persons,
            bundle_id=payload.bundle_id,
            manual_items=payload.manual_items or [],
            include_optional=payload.include_optional,
        )
        return {"list": active_list, "issues": issues, "missing_from_previous": missing_from_previous}
    finally:
        conn.close()


@app.patch("/api/shopping/items/{item_id}")
def toggle_item(item_id: int, payload: ToggleItemRequest):
    """Coche, décoche, ou marque comme manquant un article de la liste."""
    conn = db.get_conn()
    try:
        db.toggle_shopping_item(conn, item_id, payload.checked, payload.missing)
        return {"ok": True}
    finally:
        conn.close()


@app.post("/api/shopping/items", status_code=201)
def add_manual_item(payload: AddManualItemRequest):
    """Ajoute un article manuel à la liste active."""
    conn = db.get_conn()
    try:
        item_id = db.add_item_to_active_list(
            conn, payload.name, payload.qty, payload.unit or "", payload.category or "Divers"
        )
        return {"id": item_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        conn.close()


@app.delete("/api/shopping/items/{item_id}")
def delete_item(item_id: int):
    """Supprime un article de la liste."""
    conn = db.get_conn()
    try:
        db.delete_shopping_item(conn, item_id)
        return {"ok": True}
    finally:
        conn.close()


@app.delete("/api/shopping/current")
def complete_list():
    """Marque la liste active comme terminée (courses faites)."""
    conn = db.get_conn()
    try:
        db.complete_shopping_list(conn)
        return {"ok": True}
    finally:
        conn.close()


# =============================================================================
# Routes — Stats gamification
# =============================================================================

@app.get("/api/stats")
def get_stats():
    conn = db.get_conn()
    try:
        return db.get_stats(conn)
    finally:
        conn.close()


# =============================================================================
# Routes — Settings
# =============================================================================

@app.get("/api/settings")
def get_settings():
    conn = db.get_conn()
    try:
        return db.get_all_settings(conn)
    finally:
        conn.close()


@app.put("/api/settings")
def update_settings(payload: SettingsUpdate):
    conn = db.get_conn()
    try:
        if payload.weekly_goal is not None:
            db.set_setting(conn, "weekly_goal", str(payload.weekly_goal))
        return db.get_all_settings(conn)
    finally:
        conn.close()
