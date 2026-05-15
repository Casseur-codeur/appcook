import { useState, useEffect, useCallback } from 'react'
import { getCatalog, updateCatalogItem, mergeCatalogItems, addCatalogItem } from '../../api/client'

const UNITS = ['', 'g', 'kg', 'ml', 'cl', 'l', 'pièce', 'gousse', 'tranche', 'cube', 'pincée', 'cs', 'cc']
const CATEGORIES = ['', 'Épicerie', 'Frais', 'Boucherie', 'Fruits & Légumes', 'Surgelés', 'Boissons', 'Hygiène', 'Divers']

// ─── Ligne catalogue ──────────────────────────────────────────────────────────
function CatalogRow({ item, mergeMode, selected, onSelect, onSaved }) {
  const [editing, setEditing]   = useState(false)
  const [unit, setUnit]         = useState(item.default_unit || '')
  const [category, setCategory] = useState(item.category || '')
  const [showQty, setShowQty]   = useState(item.show_qty_in_list)
  const [saving, setSaving]     = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      await updateCatalogItem(item.id, { default_unit: unit || null, show_qty_in_list: showQty, category: category || null })
      onSaved(item.id, { default_unit: unit || null, show_qty_in_list: showQty, category: category || null })
      setEditing(false)
    } catch (e) {
      alert(e.message)
    } finally {
      setSaving(false)
    }
  }

  const cancel = () => {
    setUnit(item.default_unit || '')
    setShowQty(item.show_qty_in_list)
    setEditing(false)
  }

  if (mergeMode) {
    return (
      <div
        onClick={() => onSelect(item.id)}
        style={{
          background: selected ? 'rgba(255,107,53,0.15)' : 'var(--bg-secondary)',
          border: selected ? '1.5px solid var(--accent)' : '1.5px solid transparent',
          borderRadius: '10px', padding: '10px 14px',
          display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer',
          transition: 'all 0.15s',
        }}
      >
        <span style={{
          width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
          border: selected ? '2px solid var(--accent)' : '2px solid var(--text-muted)',
          background: selected ? 'var(--accent)' : 'transparent',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {selected && <span style={{ color: '#fff', fontSize: '0.7rem', fontWeight: 700 }}>✓</span>}
        </span>
        <span style={{ flex: 1, fontSize: '0.9rem' }}>{item.name}</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {item.default_unit || '—'}
        </span>
      </div>
    )
  }

  if (editing) {
    return (
      <div style={{
        background: 'var(--bg-secondary)', borderRadius: '10px', padding: '12px 14px',
        border: '1.5px solid var(--accent)',
      }}>
        <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '10px' }}>{item.name}</div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', flexShrink: 0 }}>Unité</label>
          <select
            value={unit}
            onChange={e => setUnit(e.target.value)}
            style={{
              background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
              padding: '6px 10px', color: 'var(--text-primary)', fontSize: '0.9rem',
              outline: 'none', flex: 1, minWidth: 80,
            }}
          >
            <option value="">— aucune —</option>
            {UNITS.filter(u => u).map(u => <option key={u} value={u}>{u}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', flexShrink: 0 }}>Rayon</label>
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            style={{
              background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
              padding: '6px 10px', color: 'var(--text-primary)', fontSize: '0.9rem',
              outline: 'none', flex: 1, minWidth: 80,
            }}
          >
            <option value="">— non défini —</option>
            {CATEGORIES.filter(c => c).map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div
          onClick={() => setShowQty(!showQty)}
          style={{
            display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer',
            marginBottom: '12px',
          }}
        >
          <div style={{
            width: 36, height: 20, borderRadius: 10, position: 'relative',
            background: showQty ? 'var(--accent)' : 'transparent',
            border: showQty ? 'none' : '2px solid var(--text-muted)',
            transition: 'all 0.2s', flexShrink: 0, boxSizing: 'border-box',
          }}>
            <div style={{
              position: 'absolute',
              top: showQty ? 3 : 1,
              left: showQty ? 18 : 1,
              width: showQty ? 14 : 14,
              height: showQty ? 14 : 14,
              borderRadius: '50%',
              background: showQty ? '#fff' : 'var(--text-muted)',
              transition: 'all 0.2s',
            }} />
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
            Afficher la quantité dans la liste
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button onClick={cancel} style={{
            background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
            padding: '6px 14px', color: 'var(--text-muted)', fontSize: '0.85rem', cursor: 'pointer',
          }}>Annuler</button>
          <button onClick={save} disabled={saving} style={{
            background: 'var(--accent)', border: 'none', borderRadius: '8px',
            padding: '6px 14px', color: '#fff', fontSize: '0.85rem', cursor: 'pointer',
            opacity: saving ? 0.7 : 1,
          }}>{saving ? '…' : 'Sauvegarder'}</button>
        </div>
      </div>
    )
  }

  return (
    <div
      onClick={() => setEditing(true)}
      style={{
        background: 'var(--bg-secondary)', borderRadius: '10px', padding: '10px 14px',
        display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer',
        transition: 'background 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
      onMouseLeave={e => e.currentTarget.style.background = 'var(--bg-secondary)'}
    >
      <span style={{ flex: 1, fontSize: '0.9rem' }}>{item.name}</span>
      {item.category && (
        <span style={{ fontSize: '0.72rem', background: 'var(--bg-tertiary)', borderRadius: '6px', padding: '2px 6px', color: 'var(--text-muted)' }}>
          {item.category}
        </span>
      )}
      <span style={{
        fontSize: '0.75rem',
        color: item.default_unit ? 'var(--text-muted)' : '#f44336',
        minWidth: 40, textAlign: 'right',
      }}>
        {item.default_unit || 'aucune'}
      </span>
      {!item.show_qty_in_list && (
        <span style={{
          fontSize: '0.7rem', background: 'var(--bg-tertiary)', borderRadius: '6px',
          padding: '2px 6px', color: 'var(--text-muted)',
        }}>
          toujours chez soi
        </span>
      )}
      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>✏️</span>
    </div>
  )
}

const EMPTY_FORM = { name: '', default_unit: '', category: '', show_qty_in_list: 1 }

// ─── Composant principal ──────────────────────────────────────────────────────
export default function AdminCatalog() {
  const [items, setItems]           = useState([])
  const [search, setSearch]         = useState('')
  const [mergeMode, setMergeMode]   = useState(false)
  const [selected, setSelected]     = useState([]) // IDs sélectionnés pour fusion
  const [canonical, setCanonical]   = useState(null) // ID de référence
  const [merging, setMerging]       = useState(false)
  const [filterNoUnit, setFilterNoUnit] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [addForm, setAddForm]           = useState(EMPTY_FORM)
  const [addError, setAddError]         = useState('')
  const [adding, setAdding]             = useState(false)

  useEffect(() => { getCatalog().then(setItems) }, [])

  const filtered = items.filter(i => {
    const matchSearch = i.name.toLowerCase().includes(search.toLowerCase())
    const matchFilter = filterNoUnit ? !i.default_unit : true
    return matchSearch && matchFilter
  })

  const handleSaved = useCallback((id, updates) => {
    setItems(prev => prev.map(i => i.id === id ? { ...i, ...updates } : i))
  }, [])

  const toggleSelect = (id) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
    if (canonical === id) setCanonical(null)
  }

  const doMerge = async () => {
    if (!canonical || selected.length < 2) return
    const duplicates = selected.filter(id => id !== canonical)
    if (duplicates.length === 0) return
    setMerging(true)
    try {
      await mergeCatalogItems(canonical, duplicates)
      const fresh = await getCatalog()
      setItems(fresh)
      setSelected([])
      setCanonical(null)
      setMergeMode(false)
    } catch (e) {
      alert(e.message)
    } finally {
      setMerging(false)
    }
  }

  const noUnitCount = items.filter(i => !i.default_unit).length

  const openAddModal = () => { setAddForm(EMPTY_FORM); setAddError(''); setShowAddModal(true) }
  const closeAddModal = () => { setShowAddModal(false); setAddError('') }

  const doAdd = async () => {
    if (!addForm.name.trim()) { setAddError('Le nom est obligatoire'); return }
    setAdding(true)
    setAddError('')
    try {
      await addCatalogItem(addForm)
      const fresh = await getCatalog()
      setItems(fresh)
      closeAddModal()
    } catch (e) {
      setAddError(e.message)
    } finally {
      setAdding(false)
    }
  }

  return (
    <div style={{ padding: '16px', paddingBottom: 100 }}>

      {/* En-tête */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '1.1rem' }}>
          Catalogue · <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>{items.length} ingrédients</span>
        </h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={openAddModal}
            style={{
              background: 'var(--accent)', border: 'none', borderRadius: '8px', padding: '7px 13px',
              color: '#fff', fontSize: '0.8rem', cursor: 'pointer',
            }}
          >
            + Ajouter
          </button>
          <button
            onClick={() => { setMergeMode(!mergeMode); setSelected([]); setCanonical(null) }}
            style={{
              background: mergeMode ? 'var(--accent)' : 'var(--bg-tertiary)',
              border: 'none', borderRadius: '8px', padding: '7px 13px',
              color: mergeMode ? '#fff' : 'var(--text-muted)',
              fontSize: '0.8rem', cursor: 'pointer',
            }}
          >
            {mergeMode ? '✕ Annuler fusion' : '🔀 Fusionner'}
          </button>
        </div>
      </div>

      {/* Modale ajout ingrédient */}
      {showAddModal && (
        <div
          onClick={closeAddModal}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000, padding: '16px',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: 'var(--bg-secondary)', borderRadius: '16px', padding: '24px',
              width: '100%', maxWidth: '400px',
            }}
          >
            <h3 style={{ margin: '0 0 16px', fontSize: '1rem' }}>Nouvel ingrédient</h3>

            {/* Nom */}
            <div style={{ marginBottom: '12px' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Nom <span style={{ color: 'var(--accent)' }}>*</span>
              </label>
              <input
                type="text"
                value={addForm.name}
                onChange={e => setAddForm(f => ({ ...f, name: e.target.value }))}
                onKeyDown={e => e.key === 'Enter' && doAdd()}
                placeholder="ex: Farine de blé"
                autoFocus
                style={{
                  width: '100%', boxSizing: 'border-box',
                  background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
                  padding: '8px 12px', color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none',
                }}
              />
            </div>

            {/* Unité */}
            <div style={{ marginBottom: '12px' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Unité par défaut
              </label>
              <select
                value={addForm.default_unit}
                onChange={e => setAddForm(f => ({ ...f, default_unit: e.target.value }))}
                style={{
                  width: '100%', background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
                  padding: '8px 12px', color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none',
                }}
              >
                <option value="">— aucune —</option>
                {UNITS.filter(u => u).map(u => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>

            {/* Rayon */}
            <div style={{ marginBottom: '12px' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Rayon
              </label>
              <select
                value={addForm.category}
                onChange={e => setAddForm(f => ({ ...f, category: e.target.value }))}
                style={{
                  width: '100%', background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
                  padding: '8px 12px', color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none',
                }}
              >
                <option value="">— non défini —</option>
                {CATEGORIES.filter(c => c).map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {/* Toggle show_qty */}
            <div
              onClick={() => setAddForm(f => ({ ...f, show_qty_in_list: f.show_qty_in_list ? 0 : 1 }))}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', marginBottom: '20px' }}
            >
              <div style={{
                width: 36, height: 20, borderRadius: 10, position: 'relative', flexShrink: 0,
                background: addForm.show_qty_in_list ? 'var(--accent)' : 'transparent',
                border: addForm.show_qty_in_list ? 'none' : '2px solid var(--text-muted)',
                transition: 'all 0.2s', boxSizing: 'border-box',
              }}>
                <div style={{
                  position: 'absolute',
                  top: addForm.show_qty_in_list ? 3 : 1,
                  left: addForm.show_qty_in_list ? 18 : 1,
                  width: 14, height: 14, borderRadius: '50%',
                  background: addForm.show_qty_in_list ? '#fff' : 'var(--text-muted)',
                  transition: 'all 0.2s',
                }} />
              </div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                Afficher la quantité dans la liste
              </span>
            </div>

            {/* Erreur */}
            {addError && (
              <div style={{
                background: 'rgba(244,67,54,0.1)', border: '1px solid #f44336',
                borderRadius: '8px', padding: '8px 12px', marginBottom: '16px',
                fontSize: '0.85rem', color: '#f44336',
              }}>
                {addError}
              </div>
            )}

            {/* Boutons */}
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button onClick={closeAddModal} style={{
                background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
                padding: '8px 16px', color: 'var(--text-muted)', fontSize: '0.85rem', cursor: 'pointer',
              }}>Annuler</button>
              <button onClick={doAdd} disabled={adding} style={{
                background: 'var(--accent)', border: 'none', borderRadius: '8px',
                padding: '8px 16px', color: '#fff', fontSize: '0.85rem', cursor: 'pointer',
                opacity: adding ? 0.7 : 1,
              }}>{adding ? '…' : 'Ajouter'}</button>
            </div>
          </div>
        </div>
      )}

      {/* Filtres */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
        <input
          type="text" value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Rechercher un ingrédient…"
          style={{
            flex: 1, minWidth: 180,
            background: 'var(--bg-tertiary)', border: 'none', borderRadius: '10px',
            padding: '10px 14px', color: 'var(--text-primary)', fontSize: '0.95rem', outline: 'none',
          }}
        />
        <button
          onClick={() => setFilterNoUnit(!filterNoUnit)}
          style={{
            background: filterNoUnit ? '#f4433620' : 'var(--bg-tertiary)',
            border: filterNoUnit ? '1.5px solid #f44336' : '1.5px solid transparent',
            borderRadius: '10px', padding: '8px 12px',
            color: filterNoUnit ? '#f44336' : 'var(--text-muted)',
            fontSize: '0.8rem', cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          Sans unité {noUnitCount > 0 && `(${noUnitCount})`}
        </button>
      </div>

      {/* Bandeau mode fusion */}
      {mergeMode && (
        <div style={{
          background: 'rgba(255,107,53,0.1)', border: '1px solid var(--accent)',
          borderRadius: '10px', padding: '12px 14px', marginBottom: '12px', fontSize: '0.85rem',
        }}>
          {selected.length < 2 ? (
            <span style={{ color: 'var(--text-muted)' }}>
              Sélectionne au moins 2 ingrédients à fusionner
            </span>
          ) : (
            <div>
              <div style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>
                Ingrédient canonique (celui qui sera conservé) :
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '10px' }}>
                {selected.map(id => {
                  const it = items.find(i => i.id === id)
                  return (
                    <button
                      key={id}
                      onClick={() => setCanonical(id)}
                      style={{
                        background: canonical === id ? 'var(--accent)' : 'var(--bg-tertiary)',
                        border: 'none', borderRadius: '20px', padding: '5px 12px',
                        color: canonical === id ? '#fff' : 'var(--text-primary)',
                        fontSize: '0.85rem', cursor: 'pointer',
                      }}
                    >
                      {it?.name}
                    </button>
                  )
                })}
              </div>
              <button
                onClick={doMerge}
                disabled={!canonical || merging}
                style={{
                  background: canonical ? 'var(--accent)' : 'var(--bg-tertiary)',
                  border: 'none', borderRadius: '8px', padding: '8px 16px',
                  color: canonical ? '#fff' : 'var(--text-muted)',
                  fontSize: '0.85rem', cursor: canonical ? 'pointer' : 'not-allowed',
                  opacity: merging ? 0.7 : 1,
                }}
              >
                {merging ? 'Fusion…' : `Fusionner ${selected.length} ingrédients`}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Liste */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {filtered.length === 0 && (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '24px' }}>
            Aucun ingrédient trouvé
          </p>
        )}
        {filtered.map(item => (
          <CatalogRow
            key={item.id}
            item={item}
            mergeMode={mergeMode}
            selected={selected.includes(item.id)}
            onSelect={toggleSelect}
            onSaved={handleSaved}
          />
        ))}
      </div>
    </div>
  )
}
