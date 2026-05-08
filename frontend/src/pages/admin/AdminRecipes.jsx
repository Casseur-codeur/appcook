import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRecipes, deleteRecipe } from '../../api/client'

export default function AdminRecipes() {
  const navigate = useNavigate()
  const [recipes, setRecipes] = useState([])
  const [search, setSearch] = useState('')

  const load = () => getRecipes().then(setRecipes)
  useEffect(() => { load() }, [])

  const handleDelete = async (code, name) => {
    if (!confirm(`Supprimer "${name}" ? Cette action est irréversible.`)) return
    await deleteRecipe(code)
    load()
  }

  const filtered = search.trim()
    ? recipes.filter(r => {
        const q = search.toLowerCase()
        return (
          r.name.toLowerCase().includes(q) ||
          (r.category || '').toLowerCase().includes(q) ||
          (r.origin || '').toLowerCase().includes(q)
        )
      })
    : recipes

  return (
    <div style={{ padding: '16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '1.1rem' }}>
          Recettes {search ? `(${filtered.length}/${recipes.length})` : `(${recipes.length})`}
        </h2>
        <button className="btn-primary" style={{ width: 'auto', padding: '8px 16px', fontSize: '0.9rem' }}
          onClick={() => navigate('/admin/new')}>
          + Nouvelle
        </button>
      </div>

      {/* Recherche */}
      <input
        type="text"
        value={search}
        onChange={e => setSearch(e.target.value)}
        placeholder="🔍  Chercher par nom, catégorie, cuisine..."
        style={{
          width: '100%', boxSizing: 'border-box',
          background: 'var(--bg-secondary)', border: 'none', borderRadius: '12px',
          padding: '10px 14px', color: 'var(--text-primary)', fontSize: '0.9rem',
          outline: 'none', marginBottom: '12px',
        }}
      />

      {/* Liste */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {search ? `Aucune recette pour "${search}"` : 'Aucune recette'}
          </div>
        )}
        {filtered.map(r => (
          <div key={r.code} style={{
            background: 'var(--bg-secondary)', borderRadius: '12px',
            padding: '12px 14px', display: 'flex', alignItems: 'center', gap: '12px',
          }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 500 }}>{r.name}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {[r.category, r.origin, r.is_batch && '🥡 Batch'].filter(Boolean).join(' · ')}
              </div>
            </div>
            <button onClick={() => navigate(`/admin/${r.code}`)}
              style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px', padding: '6px 12px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem', flexShrink: 0 }}>
              Modifier
            </button>
            <button onClick={() => handleDelete(r.code, r.name)}
              style={{ background: 'rgba(244,67,54,0.15)', border: 'none', borderRadius: '8px', padding: '6px 10px', color: '#f44336', cursor: 'pointer', fontSize: '0.85rem', flexShrink: 0 }}>
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
