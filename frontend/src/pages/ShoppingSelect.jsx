import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getRecipes, getBundles, generateList, getCurrentList,
  deleteShoppingItem, addShoppingItem, searchIngredients, getCatalog,
} from '../api/client'

const CATEGORIES = ['Épicerie', 'Frais', 'Boucherie', 'Fruits & Légumes', 'Surgelés', 'Boissons', 'Hygiène', 'Divers']

// ─── Indicateur d'étapes ─────────────────────────────────────────────────────
function StepBar({ step }) {
  const steps = ['Recettes', 'Bundle', 'Révision']
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      gap: '0', padding: '16px 16px 0',
    }}>
      {steps.map((label, i) => {
        const n = i + 1
        const active  = step === n
        const done    = step > n
        return (
          <div key={n} style={{ display: 'flex', alignItems: 'center' }}>
            {i > 0 && (
              <div style={{
                width: 32, height: 2,
                background: done ? 'var(--accent)' : 'var(--bg-tertiary)',
                transition: 'background 0.3s',
              }} />
            )}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                background: done ? 'var(--accent)' : active ? 'rgba(255,107,53,0.15)' : 'var(--bg-tertiary)',
                border: active ? '2px solid var(--accent)' : done ? 'none' : '2px solid var(--bg-tertiary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: done ? '#fff' : active ? 'var(--accent)' : 'var(--text-muted)',
                fontSize: '0.8rem', fontWeight: 700,
                transition: 'all 0.3s',
              }}>
                {done ? '✓' : n}
              </div>
              <span style={{
                fontSize: '0.7rem',
                color: active ? 'var(--accent)' : done ? 'var(--text-muted)' : 'var(--bg-tertiary)',
                fontWeight: active ? 700 : 400,
                transition: 'color 0.3s',
              }}>
                {label}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ─── Étape 1 : Recettes ───────────────────────────────────────────────────────
function StepRecettes({ recipes, selected, setSelected, onNext }) {
  const [includeOptional, setIncludeOptional] = useState(false)

  const toggle = (code, base_servings) => {
    setSelected(prev => {
      if (prev[code]) { const n = { ...prev }; delete n[code]; return n }
      return { ...prev, [code]: { persons: base_servings } }
    })
  }

  const setPersons = (code, val) =>
    setSelected(prev => ({ ...prev, [code]: { ...prev[code], persons: Math.max(1, val) } }))

  const canNext = Object.keys(selected).length > 0

  return (
    <div style={{ padding: '20px 16px', paddingBottom: 100 }}>
      <h2 style={{ margin: '0 0 4px' }}>Quoi manger cette semaine ?</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 20px' }}>
        Sélectionne une ou plusieurs recettes.
      </p>

      {/* Toggle optionnels */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'var(--bg-secondary)', borderRadius: '12px',
        padding: '12px 14px', marginBottom: '12px',
      }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Inclure les ingrédients optionnels</span>
        <button
          onClick={() => setIncludeOptional(v => !v)}
          style={{
            width: '44px', height: '24px', borderRadius: '12px', border: 'none', cursor: 'pointer',
            background: includeOptional ? 'var(--accent)' : 'var(--bg-tertiary)',
            position: 'relative', transition: 'background 0.2s', flexShrink: 0,
          }}
        >
          <span style={{
            position: 'absolute', top: 3, left: includeOptional ? 23 : 3,
            width: 18, height: 18, background: 'white', borderRadius: '50%', transition: 'left 0.2s',
          }} />
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '28px' }}>
        {recipes.map(r => {
          const isSel = !!selected[r.code]
          return (
            <div key={r.code} style={{
              background: isSel ? 'rgba(255,107,53,0.08)' : 'var(--bg-secondary)',
              border: `1.5px solid ${isSel ? 'var(--accent)' : 'transparent'}`,
              borderRadius: '12px', padding: '12px 14px',
              transition: 'all 0.15s',
            }}>
              <div onClick={() => toggle(r.code, r.base_servings)}
                style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                <div style={{
                  width: 22, height: 22, borderRadius: '6px', flexShrink: 0,
                  border: `2px solid ${isSel ? 'var(--accent)' : 'var(--bg-tertiary)'}`,
                  background: isSel ? 'var(--accent)' : 'transparent',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'white', fontSize: '0.8rem', transition: 'all 0.15s',
                }}>
                  {isSel && '✓'}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: '0.95rem' }}>{r.name}</div>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '2px' }}>
                    {r.is_batch && <span style={{ fontSize: '0.72rem', color: 'var(--success)' }}>🥡 Batch</span>}
                    {r.category && <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{r.category}</span>}
                  </div>
                </div>
              </div>

              {isSel && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '10px', paddingLeft: 34 }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Portions :</span>
                  <button onClick={() => setPersons(r.code, selected[r.code].persons - 1)}
                    style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '6px', width: 28, height: 28, color: 'var(--text-primary)', cursor: 'pointer', fontSize: '1.1rem' }}>−</button>
                  <span style={{ fontWeight: 700, minWidth: 20, textAlign: 'center' }}>{selected[r.code].persons}</span>
                  <button onClick={() => setPersons(r.code, selected[r.code].persons + 1)}
                    style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '6px', width: 28, height: 28, color: 'var(--text-primary)', cursor: 'pointer', fontSize: '1.1rem' }}>+</button>
                </div>
              )}
            </div>
          )
        })}

        {recipes.length === 0 && (
          <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Aucune recette enregistrée
          </div>
        )}
      </div>

      {/* Stocker includeOptional pour le step suivant */}
      <div style={{ position: 'fixed', bottom: 64, left: 0, right: 0, padding: '16px', background: 'var(--bg-primary)', borderTop: '1px solid var(--bg-tertiary)' }}>
        <button
          className="btn-primary"
          disabled={!canNext}
          onClick={() => onNext(includeOptional)}
          style={{ opacity: canNext ? 1 : 0.4 }}
        >
          Suivant →
        </button>
        {!canNext && (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', margin: '8px 0 0' }}>
            Sélectionne au moins une recette
          </p>
        )}
      </div>
    </div>
  )
}

// ─── Étape 2 : Bundle ─────────────────────────────────────────────────────────
function StepBundle({ bundles, selectedBundle, setSelectedBundle, onNext, onBack }) {
  const selected = bundles.find(b => b.id === selectedBundle)

  return (
    <div style={{ padding: '20px 16px', paddingBottom: 100 }}>
      <h2 style={{ margin: '0 0 4px' }}>Articles permanents</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 24px' }}>
        Choisis un bundle à ajouter à ta liste, ou passe cette étape.
      </p>

      {/* Chips bundles */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {bundles.map(b => (
          <button
            key={b.id}
            onClick={() => setSelectedBundle(b.id === selectedBundle ? null : b.id)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              padding: '16px 20px', borderRadius: '16px', border: 'none', cursor: 'pointer',
              background: selectedBundle === b.id ? 'rgba(255,107,53,0.12)' : 'var(--bg-secondary)',
              outline: selectedBundle === b.id ? '2px solid var(--accent)' : '2px solid transparent',
              transition: 'all 0.15s', minWidth: 90,
            }}
          >
            <span style={{ fontSize: '1.8rem', marginBottom: '6px' }}>{b.icon}</span>
            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: selectedBundle === b.id ? 'var(--accent)' : 'var(--text-primary)' }}>
              {b.name}
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {b.items?.length || 0} article{(b.items?.length || 0) > 1 ? 's' : ''}
            </span>
          </button>
        ))}
      </div>

      {/* Aperçu des articles du bundle sélectionné */}
      {selected && (
        <div style={{
          background: 'var(--bg-secondary)', borderRadius: '14px', padding: '14px 16px',
          marginBottom: '16px',
        }}>
          <div style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase',
            letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Contenu du bundle {selected.name}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {(selected.items || []).map(item => (
              <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '0.9rem', flex: 1 }}>{item.name}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {item.qty != null ? `${item.qty % 1 === 0 ? item.qty : item.qty.toFixed(1)} ${item.unit}` : '—'}
                </span>
                <span style={{
                  fontSize: '0.7rem', color: 'var(--text-muted)',
                  background: 'var(--bg-tertiary)', borderRadius: '6px', padding: '2px 6px',
                }}>
                  {item.category}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ position: 'fixed', bottom: 64, left: 0, right: 0, padding: '16px', background: 'var(--bg-primary)', borderTop: '1px solid var(--bg-tertiary)', display: 'flex', gap: '10px' }}>
        <button
          onClick={onBack}
          style={{
            flex: 1, padding: '14px', borderRadius: '14px', border: 'none',
            background: 'var(--bg-tertiary)', color: 'var(--text-muted)',
            fontWeight: 600, fontSize: '0.95rem', cursor: 'pointer',
          }}
        >
          ← Retour
        </button>
        <button
          className="btn-primary"
          onClick={onNext}
          style={{ flex: 2 }}
        >
          {selectedBundle ? 'Suivant →' : 'Passer →'}
        </button>
      </div>
    </div>
  )
}

// ─── Étape 3 : Révision ───────────────────────────────────────────────────────
const ISSUE_LABELS = {
  unit_error:        'Unité incompatible — ajouté sans conversion',
  unit_incompatible: 'Unité incompatible — ajouté sans conversion',
}

function StepRevision({ onBack, onConfirm, issues = [] }) {
  const [items, setItems]     = useState([])
  const [catalog, setCatalog] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery]           = useState('')
  const [createMode, setCreateMode] = useState(false)
  const [newUnit, setNewUnit]       = useState('')
  const [newCat, setNewCat]         = useState('Divers')
  const [adding, setAdding]         = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    Promise.all([getCurrentList(), getCatalog()]).then(([listData, cat]) => {
      setItems(listData?.items || [])
      setCatalog(cat || [])
      setLoading(false)
    })
  }, [])

  const listNames = new Set(items.map(i => i.name.toLowerCase()))
  const q = query.toLowerCase()

  // Articles déjà dans la liste (filtrés par recherche)
  const selectedItems = items.filter(i => !q || i.name.toLowerCase().includes(q))
  const selectedGrouped = selectedItems.reduce((acc, item) => {
    const cat = item.category || 'Divers'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})

  // Catalogue NON encore dans la liste (filtrés par recherche)
  const availableCatalog = catalog.filter(ing =>
    !listNames.has(ing.name.toLowerCase()) &&
    (!q || ing.name.toLowerCase().includes(q))
  )
  const availableGrouped = availableCatalog.reduce((acc, ing) => {
    const cat = ing.category || 'Divers'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(ing)
    return acc
  }, {})
  const availableCategories = Object.keys(availableGrouped).sort()

  const handleRemove = async (id) => {
    setItems(prev => prev.filter(i => i.id !== id))
    try { await deleteShoppingItem(id) } catch {}
  }

  const handleAdd = async (ing) => {
    try {
      const { id } = await addShoppingItem({ name: ing.name, unit: ing.default_unit || '', category: 'Divers' })
      setItems(prev => [...prev, { id, name: ing.name, qty: null, unit: ing.default_unit || '', category: 'Divers', checked: false, source: 'manual' }])
    } catch (e) { alert(e.message) }
  }

  const handleCreate = async () => {
    const name = query.trim()
    if (!name) return
    setAdding(true)
    try {
      const { id } = await addShoppingItem({ name, unit: newUnit, category: newCat })
      setItems(prev => [...prev, { id, name, qty: null, unit: newUnit, category: newCat, checked: false, source: 'manual' }])
      setQuery(''); setNewUnit(''); setNewCat('Divers'); setCreateMode(false)
    } catch (e) { alert(e.message) }
    setAdding(false)
  }

  const notInCatalog = query.trim() && !catalog.some(i => i.name.toLowerCase() === query.trim().toLowerCase())

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
      Génération de la liste...
    </div>
  )

  return (
    <div style={{ padding: '20px 16px', paddingBottom: 160 }}>
      <h2 style={{ margin: '0 0 4px' }}>Vérification</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 16px' }}>
        {items.length} article{items.length > 1 ? 's' : ''} — retire ou ajoute avant de partir.
      </p>

      {/* ── Bandeau d'issues (ingrédients sans unité, conversions impossibles) ── */}
      {issues.length > 0 && (
        <div style={{
          background: 'rgba(255,152,0,0.1)', border: '1.5px solid rgba(255,152,0,0.4)',
          borderRadius: '12px', padding: '12px 14px', marginBottom: '16px',
        }}>
          <div style={{ fontWeight: 600, color: '#FF9800', fontSize: '0.85rem', marginBottom: '6px' }}>
            ⚠ {issues.length} ingrédient{issues.length > 1 ? 's' : ''} avec problème d'unité
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {issues.map((issue, i) => (
              <div key={i} style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{issue.ingredient}</span>
                {' — '}{ISSUE_LABELS[issue.reason] || issue.reason}
              </div>
            ))}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '8px' }}>
            Corrige les unités dans Admin → Catalogue pour éviter ce problème la prochaine fois.
          </div>
        </div>
      )}

      {/* ── Articles sélectionnés (recettes + bundle) ── */}
      {Object.keys(selectedGrouped).sort().map(cat => (
        <div key={cat} style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '6px', paddingLeft: 4 }}>
            {cat}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {selectedGrouped[cat].map(item => (
              <div key={item.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(255,107,53,0.07)', border: '1.5px solid rgba(255,107,53,0.25)', borderRadius: '12px', padding: '11px 14px' }}>
                <span style={{ flex: 1, fontSize: '0.92rem' }}>{item.name}</span>
                {item.qty != null && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.qty % 1 === 0 ? item.qty : item.qty.toFixed(1)} {item.unit}</span>}
                <button onClick={() => handleRemove(item.id)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '1.1rem', padding: '0 2px', lineHeight: 1 }}>×</button>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* ── Séparateur + barre de recherche ── */}
      <div style={{ borderTop: '1px solid var(--bg-tertiary)', margin: '20px 0 14px' }} />
      <div style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '10px' }}>
        Ajouter depuis le catalogue
      </div>

      <div style={{ marginBottom: '12px' }}>
        <input
          ref={inputRef}
          value={query}
          onChange={e => { setQuery(e.target.value); setCreateMode(false) }}
          placeholder="Rechercher un article..."
          style={{ width: '100%', padding: '12px 14px', borderRadius: '12px', border: 'none', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '0.95rem', outline: 'none', boxSizing: 'border-box' }}
        />

        {/* Créer si absent du catalogue */}
        {notInCatalog && !createMode && (
          <button onClick={() => setCreateMode(true)} style={{ marginTop: '8px', width: '100%', padding: '11px 14px', borderRadius: '12px', border: '1.5px dashed var(--accent)', background: 'rgba(255,107,53,0.06)', color: 'var(--accent)', fontSize: '0.9rem', cursor: 'pointer', textAlign: 'left', boxSizing: 'border-box' }}>
            + Créer "{query.trim()}"
          </button>
        )}

        {createMode && (
          <div style={{ marginTop: '8px', background: 'var(--bg-secondary)', borderRadius: '12px', padding: '14px', border: '1.5px solid var(--accent)' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
              Nouvel article : <strong style={{ color: 'var(--text-primary)' }}>{query.trim()}</strong>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <select value={newCat} onChange={e => setNewCat(e.target.value)} style={{ flex: 2, padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none' }}>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <input value={newUnit} onChange={e => setNewUnit(e.target.value)} placeholder="Unité" style={{ flex: 1, padding: '10px 12px', borderRadius: '10px', border: 'none', background: 'var(--bg-tertiary)', color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none' }} />
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={() => setCreateMode(false)} style={{ flex: 1, padding: '10px', borderRadius: '10px', border: 'none', background: 'var(--bg-tertiary)', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem' }}>Annuler</button>
              <button onClick={handleCreate} disabled={adding} style={{ flex: 2, padding: '10px', borderRadius: '10px', border: 'none', background: 'var(--accent)', color: '#fff', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600 }}>{adding ? '…' : '+ Ajouter'}</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Reste du catalogue (non sélectionné) ── */}
      {availableCategories.map(cat => (
        <div key={cat} style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '6px', paddingLeft: 4 }}>
            {cat}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {availableGrouped[cat].map(ing => (
              <div key={ing.id} onClick={() => handleAdd(ing)} style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg-secondary)', borderRadius: '12px', padding: '11px 14px', cursor: 'pointer', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-secondary)'}
              >
                <div style={{ width: 22, height: 22, borderRadius: '6px', flexShrink: 0, border: '2px solid var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '1rem' }}>+</div>
                <span style={{ flex: 1, fontSize: '0.92rem' }}>{ing.name}</span>
                {ing.default_unit && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{ing.default_unit}</span>}
              </div>
            ))}
          </div>
        </div>
      ))}

      {availableCatalog.length === 0 && query && !notInCatalog && (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>Tout est déjà dans la liste</p>
      )}

      {/* Boutons fixes */}
      <div style={{ position: 'fixed', bottom: 64, left: 0, right: 0, padding: '12px 16px', background: 'var(--bg-primary)', borderTop: '1px solid var(--bg-tertiary)', display: 'flex', gap: '10px' }}>
        <button onClick={onBack} style={{ flex: 1, padding: '14px', borderRadius: '14px', border: 'none', background: 'var(--bg-tertiary)', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.95rem', cursor: 'pointer' }}>← Retour</button>
        <button className="btn-primary" onClick={onConfirm} style={{ flex: 2 }}>C'est parti 🛒</button>
      </div>
    </div>
  )
}

// ─── Composant principal ──────────────────────────────────────────────────────
export default function ShoppingSelect({ forceNew = false }) {
  const navigate = useNavigate()

  const [step, setStep]                       = useState(1)
  const [recipes, setRecipes]                 = useState([])
  const [bundles, setBundles]                 = useState([])
  const [selectedRecipes, setSelectedRecipes] = useState({})
  const [selectedBundle, setSelectedBundle]   = useState(null)
  const [includeOptional, setIncludeOptional] = useState(false)
  const [checkingList, setCheckingList]       = useState(!forceNew)
  const [generating, setGenerating]           = useState(false)
  const [genIssues, setGenIssues]             = useState([])   // issues remontées par le backend
  const [missingFromPrevious, setMissingFromPrevious] = useState([]) // articles manquants de la liste précédente

  useEffect(() => {
    getRecipes().then(setRecipes)
    getBundles().then(setBundles)

    if (!forceNew) {
      getCurrentList().then(data => {
        if (data?.id) navigate('/shopping/list', { replace: true })
        else setCheckingList(false)
      }).catch(() => setCheckingList(false))
    }
  }, [])

  const handleStep1Next = (incOpt) => {
    setIncludeOptional(incOpt)
    setStep(2)
  }

  const handleStep2Next = async () => {
    setGenerating(true)
    try {
      const codes = Object.keys(selectedRecipes)
      const avgPersons = codes.length > 0
        ? Object.values(selectedRecipes).reduce((s, v) => s + v.persons, 0) / codes.length
        : 1
      const result = await generateList({
        recipe_codes: codes,
        persons: avgPersons,
        bundle_id: selectedBundle,
        manual_items: [],
        include_optional: includeOptional,
      })
      // Capturer les issues (ingrédients sans unité ou unités incompatibles)
      setGenIssues(result?.issues || [])
      // Capturer les articles manquants de la liste précédente pour les proposer à ShoppingList
      setMissingFromPrevious(result?.missing_from_previous || [])
      setStep(3)
    } catch (e) {
      alert('Erreur lors de la génération : ' + e.message)
    } finally {
      setGenerating(false)
    }
  }

  if (checkingList || generating) return (
    <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
      {generating ? 'Génération en cours...' : 'Chargement...'}
    </div>
  )

  return (
    <div>
      <StepBar step={step} />

      {step === 1 && (
        <StepRecettes
          recipes={recipes}
          selected={selectedRecipes}
          setSelected={setSelectedRecipes}
          onNext={handleStep1Next}
        />
      )}

      {step === 2 && (
        <StepBundle
          bundles={bundles}
          selectedBundle={selectedBundle}
          setSelectedBundle={setSelectedBundle}
          onBack={() => setStep(1)}
          onNext={handleStep2Next}
        />
      )}

      {step === 3 && (
        <StepRevision
          issues={genIssues}
          onBack={() => {
            // On ne peut pas "dé-générer" proprement, on repart à zéro
            setStep(1)
            setSelectedRecipes({})
            setSelectedBundle(null)
          }}
          onConfirm={() => navigate('/shopping/list', { state: { missingFromPrevious } })}
        />
      )}
    </div>
  )
}
