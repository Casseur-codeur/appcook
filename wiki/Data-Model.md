# Modele de donnees

Le modele AppCook repose sur une base SQLite centree sur les recettes, leurs ingredients, leurs etapes et les alias de normalisation.

## Tables principales

- `recipes`
- `ingredient_catalog`
- `recipe_ingredients`
- `steps`
- `step_ingredients`
- `ingredient_alias`
- `unit_alias`

## Idees clefs

- `recipes.code` sert d'identifiant stable dans l'API
- `base_servings` definit l'echelle de reference pour les quantites
- `ingredient_catalog` contient les ingredients canoniques
- `ingredient_alias` et `unit_alias` servent a la normalisation
- `step_ingredients` relie une etape aux ingredients utilises dans cette etape

## Points d'attention

- Eviter les doublons en s'appuyant sur `norm_name`
- Verifier la compatibilite des unites pour l'agregation des courses
- Respecter `show_qty_in_list` pour les ingredients toujours disponibles

## Migration et detail complet

Le document de reference pour les tables conservees, les champs supprimes et le script de migration est :

- [Schema DB et migration](../SCHEMA_DB.md)
