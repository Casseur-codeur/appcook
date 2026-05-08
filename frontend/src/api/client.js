const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Erreur ${res.status}`)
  }
  return res.json()
}

// --- Recettes ---
export const getRecipes = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v != null && v !== ''))
  ).toString()
  return request(`/recipes${qs ? '?' + qs : ''}`)
}

export const getSuggestedRecipe = (timeMax) =>
  request(`/recipes/suggest${timeMax ? '?time_max=' + timeMax : ''}`)

export const getRecipe = (code) => request(`/recipes/${code}`)
export const createRecipe = (data) => request('/recipes', { method: 'POST', body: JSON.stringify(data) })
export const updateRecipe = (code, data) => request(`/recipes/${code}`, { method: 'PUT', body: JSON.stringify(data) })
export const createFullRecipe = (data) => request('/recipes/full', { method: 'POST', body: JSON.stringify(data) })
export const updateFullRecipe = (code, data) => request(`/recipes/${code}/full`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteRecipe = (code) => request(`/recipes/${code}`, { method: 'DELETE' })
export const exportRecipe = (code) => request(`/recipes/${code}/export`)
export const importRecipe = (data, onConflict = 'rename') =>
  request('/recipes/import', { method: 'POST', body: JSON.stringify({ data, on_conflict: onConflict }) })

// --- Filtres ---
export const getCategories = () => request('/categories')
export const getOrigins = () => request('/origins')

// --- Historique ---
export const logCook = (code) => request(`/history/${code}`, { method: 'POST' })
export const getHistory = (limit = 20) => request(`/history?limit=${limit}`)

// --- Courses (ancien endpoint, conservé pour compatibilité) ---
export const generateShoppingList = (recipeCodes, persons, includeOptional) =>
  request('/shopping', {
    method: 'POST',
    body: JSON.stringify({ recipe_codes: recipeCodes, persons, include_optional: includeOptional }),
  })

// --- Bundles ---
export const getBundles = () => request('/bundles')
export const createBundle = (data) =>
  request('/bundles', { method: 'POST', body: JSON.stringify(data) })
export const updateBundle = (id, data) =>
  request(`/bundles/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteBundle = (id) =>
  request(`/bundles/${id}`, { method: 'DELETE' })
export const addBundleItem = (bundleId, data) =>
  request(`/bundles/${bundleId}/items`, { method: 'POST', body: JSON.stringify(data) })
export const updateBundleItem = (bundleId, itemId, data) =>
  request(`/bundles/${bundleId}/items/${itemId}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteBundleItem = (bundleId, itemId) =>
  request(`/bundles/${bundleId}/items/${itemId}`, { method: 'DELETE' })

// --- Shopping list v2 (persistante) ---
export const getCurrentList = () => request('/shopping/current')
export const generateList = (payload) =>
  request('/shopping/generate', { method: 'POST', body: JSON.stringify(payload) })
export const toggleShoppingItem = (id, checked, missing = false) =>
  request(`/shopping/items/${id}`, { method: 'PATCH', body: JSON.stringify({ checked, missing }) })
export const addShoppingItem = (data) =>
  request('/shopping/items', { method: 'POST', body: JSON.stringify(data) })
export const deleteShoppingItem = (id) =>
  request(`/shopping/items/${id}`, { method: 'DELETE' })
export const completeShoppingList = () =>
  request('/shopping/current', { method: 'DELETE' })

// --- Stats ---
export const getStats = () => request('/stats')

// --- Settings ---
export const getSettings = () => request('/settings')
export const updateSettings = (data) =>
  request('/settings', { method: 'PUT', body: JSON.stringify(data) })

// --- Ingrédients ---
export const searchIngredients = (q) => request(`/ingredients/search?q=${encodeURIComponent(q)}`)

// --- Catalogue ---
export const getCatalog = () => request('/catalog')
export const updateCatalogItem = (id, data) =>
  request(`/catalog/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const mergeCatalogItems = (canonicalId, duplicateIds) =>
  request('/catalog/merge', { method: 'POST', body: JSON.stringify({ canonical_id: canonicalId, duplicate_ids: duplicateIds }) })
