# API backend

Le backend expose une API REST FastAPI sous le prefixe `/api`.

## Endpoints principaux

### Recettes

- `GET /api/recipes`
- `GET /api/recipes/{code}`
- `POST /api/recipes`
- `PUT /api/recipes/{code}`
- `DELETE /api/recipes/{code}`
- `POST /api/recipes/import`

### Liste de courses et ingredients

- `GET /api/shopping?codes=a,b&p=2`
- `GET /api/ingredients/search?q=...`

### Catalogue

- `GET /api/catalog`
- `PUT /api/catalog/{id}`

## Comportement attendu

- Les recettes sont identifiees cote URL par leur `code`
- Les quantites sont basees sur `base_servings`
- La liste de courses agrege les ingredients compatibles par unite canonique

## Ou regarder dans le code

- [`backend/main.py`](../backend/main.py)
- [`backend/db.py`](../backend/db.py)

## Reference fonctionnelle

Pour la vue d'ensemble de l'API et des flux :

- [Architecture technique detaillee](../ARCHITECTURE.md)
