import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRecipes, getSuggestedRecipe, getCategories, getOrigins, getStats } from '../api/client'
import RecipeCard from '../components/RecipeCard'
import FilterChips from '../components/FilterChips'
import LoadingScreen from '../components/LoadingScreen'
import EmptyState from '../components/EmptyState'

const TIME_OPTIONS = [
  { value: '20',  label: '⚡ < 20 min' },
  { value: '35',  label: '🕐 ~30 min'  },
  { value: null,  label: '🍽 J\'ai le temps' },
]

export default function Recipes() {
  const navigate = useNavigate()
  const [recipes, setRecipes] = useState([])
  const [suggested, setSuggested] = useState(null)
  const [categories, setCategories] = useState([])
  const [origins, setOrigins] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  // Filtres actifs
  const [timeMax, setTimeMax] = useState(null)
  const [isBatch, setIsBatch] = useState(null)
  const [category, setCategory] = useState(null)
  const [origin, setOrigin] = useState(null)
  const [search, setSearch] = useState('')

  // Charger filtres disponibles + stats
  useEffect(() => {
    getCategories().then(c => setCategories(c.map(v => ({ value: v, label: v }))))
    getOrigins().then(o => setOrigins(o.map(v => ({ value: v, label: v }))))
    getStats().then(setStats).catch(() => {})
  }, [])

  // Charger recettes à chaque changement de filtre
  useEffect(() => {
    setLoading(true)
    const params = {}
    if (timeMax) params.time_max = timeMax
    if (isBatch !== null) params.is_batch = isBatch
    if (category) params.category = category
    if (origin) params.origin = origin

    Promise.all([
      getRecipes(params),
      getSuggestedRecipe(timeMax).catch(() => null),
    ]).then(([list, suggest]) => {
      setSuggested(suggest)
      // Retirer la suggestion de la grille pour éviter le doublon
      setRecipes(suggest ? list.filter(r => r.code !== suggest.code) : list)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [timeMax, isBatch, category, origin])

  // Filtre texte côté client (name + category + origin)
  const q = search.trim().toLowerCase()
  const matchesSearch = (r) =>
    !q ||
    r.name?.toLowerCase().includes(q) ||
    r.category?.toLowerCase().includes(q) ||
    r.origin?.toLowerCase().includes(q)

  const filteredSuggested = suggested && matchesSearch(suggested) ? suggested : null
  const filteredRecipes = recipes.filter(matchesSearch)

  return (
    <div style={{ paddingTop: '16px' }}>

      {/* Header */}
      <div style={{ padding: '0 16px 8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '1.3rem', fontWeight: 700 }}>Recettes</div>
      </div>

      {/* Recherche texte */}
      <div style={{ padding: '0 16px 8px' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="🔍 Rechercher..."
          style={{
            width: '100%', padding: '10px 14px', borderRadius: '12px', border: 'none',
            background: 'var(--bg-secondary)', color: 'var(--text-primary)',
            fontSize: '0.95rem', outline: 'none', boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Bandeau stats hebdo */}
      {stats && (
        <div
          onClick={() => navigate('/stats')}
          style={{
            margin: '0 16px 12px', padding: '10px 14px', borderRadius: '12px',
            background: 'var(--bg-secondary)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '12px',
          }}
        >
          <span style={{ fontSize: '1.2rem' }}>🔥</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Semaine : {stats.weekly_cooks}/{stats.weekly_goal} recette{stats.weekly_goal > 1 ? 's' : ''}
            </div>
            <div style={{ background: 'var(--bg-tertiary)', borderRadius: '4px', height: '6px', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: '4px',
                background: stats.weekly_cooks >= stats.weekly_goal ? 'var(--success)' : 'var(--accent)',
                width: `${Math.min(100, Math.round((stats.weekly_cooks / stats.weekly_goal) * 100))}%`,
                transition: 'width 0.3s',
              }} />
            </div>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>›</span>
        </div>
      )}

      {/* Filtre temps */}
      <div style={{ marginBottom: '8px' }}>
        <FilterChips
          options={TIME_OPTIONS}
          selected={timeMax}
          onChange={val => setTimeMax(val)}
        />
      </div>

      {/* Filtre batch */}
      <div style={{ marginBottom: '8px' }}>
        <FilterChips
          options={[{ value: true, label: '🥡 Batch cooking' }]}
          selected={isBatch}
          onChange={val => setIsBatch(val)}
        />
      </div>

      {/* Filtres catégorie & origine */}
      {categories.length > 0 && (
        <div style={{ marginBottom: '8px' }}>
          <FilterChips options={categories} selected={category} onChange={setCategory} />
        </div>
      )}
      {origins.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <FilterChips options={origins} selected={origin} onChange={setOrigin} />
        </div>
      )}

      {loading ? (
        <LoadingScreen message="Chargement des recettes..." />
      ) : (
        <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Suggestion en haut */}
          {filteredSuggested && <RecipeCard recipe={filteredSuggested} highlighted />}

          {/* Grille */}
          {filteredRecipes.map(r => <RecipeCard key={r.code} recipe={r} />)}

          {filteredRecipes.length === 0 && !filteredSuggested && (
            <EmptyState
              title={q ? `Aucun résultat pour "${search}"` : 'Aucune recette pour ces filtres'}
              message={q ? 'Essaie un autre mot-clé.' : 'Essaie de changer les filtres ou ajoute de nouvelles recettes.'}
            />
          )}

        </div>
      )}
    </div>
  )
}
