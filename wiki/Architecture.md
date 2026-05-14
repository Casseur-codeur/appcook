# Architecture

## Stack

- Frontend : React + Vite
- Backend : FastAPI
- Base de donnees : SQLite
- Reverse proxy : nginx
- Orchestration : Docker Compose

## Flux principal

```text
Client mobile / navigateur
  -> nginx frontend
  -> proxy /api/*
  -> FastAPI
  -> SQLite
```

## Organisation du depot

- `frontend/` : SPA React, pages, composants, styles
- `backend/` : API FastAPI, acces base de donnees, seed
- `deploy/` : certificats et elements de deploiement
- `assets/` : icones et illustrations
- `recettes_exemple/` : recettes JSON d'exemple

## Points fonctionnels notables

- Interface mobile-first
- Focus mode pour suivre les etapes d'une recette
- Liste de courses generee a partir des recettes
- Espace admin pour gerer recettes, bundles et catalogue

## Lecture recommandee

Cette page est un resume. Pour le schema complet et les choix techniques :

- [Architecture technique detaillee](../ARCHITECTURE.md)
