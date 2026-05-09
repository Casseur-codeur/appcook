import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCurrentList, toggleShoppingItem, addShoppingItem, deleteShoppingItem, completeShoppingList } from '../api/client'
import ProgressBar from '../components/ProgressBar'

// États d'un article : 'unchecked' → 'checked' → 'missing' → 'unchecked'
function nextState(item) {
  if (item.missing) return 'unchecked'
  if (item.checked) return 'missing'
  return 'checked'
}

export default function ShoppingList() {
  const navigate = useNavigate()
const [items, setItems] = useState([])
  const [listId, setListId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [newItemName, setNewItemName] = useState('')
  const [addingItem, setAddingItem] = useState(false)
  const inputRef = useRef(null)

  // (les articles "abandonnés" sont désormais proposés en Step 3 de ShoppingSelect)

  useEffect(() => {
    loadList()
  }, [])

  const loadList = () => {
    getCurrentList().then(data => {
      if (data && data.id) {
        setListId(data.id)
        setItems(data.items || [])
      } else {
        setListId(null)
        setItems([])
      }
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  // Grouper les items par catégorie
  const grouped = items.reduce((acc, item) => {
    const cat = item.category || 'Divers'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(item)
    return acc
  }, {})
  const categories = Object.keys(grouped).sort()

  // checked OU missing compte dans la progression
  const checkedCount = items.filter(i => i.checked || i.missing).length
  const allDone = items.length > 0 && checkedCount === items.length

  // Toggle optimiste : unchecked → checked → missing → unchecked
  const handleToggle = async (item) => {
    const state = nextState(item)
    const newChecked = state === 'checked' || state === 'missing'
    const newMissing = state === 'missing'
    setItems(prev => prev.map(i =>
      i.id === item.id ? { ...i, checked: newChecked, missing: newMissing } : i
    ))
    try {
      await toggleShoppingItem(item.id, newChecked, newMissing)
    } catch {
      setItems(prev => prev.map(i =>
        i.id === item.id ? { ...i, checked: item.checked, missing: item.missing } : i
      ))
    }
  }

  // Supprimer un item
  const handleDelete = async (itemId) => {
    setItems(prev => prev.filter(i => i.id !== itemId))
    try {
      await deleteShoppingItem(itemId)
    } catch {
      loadList() // recharger si erreur
    }
  }

  // Ajouter un article manuel
  const handleAddItem = async () => {
    const name = newItemName.trim()
    if (!name || addingItem) return   // guard double-submit via Enter rapide
    setAddingItem(true)
    try {
      const { id } = await addShoppingItem({ name, category: 'Divers' })
      setItems(prev => [...prev, { id, name, qty: null, unit: '', category: 'Divers', checked: false, source: 'manual' }])
      setNewItemName('')
      inputRef.current?.focus()
    } catch (e) {
      alert('Erreur : ' + e.message)
    }
    setAddingItem(false)
  }

  // Terminer les courses
  const handleComplete = async () => {
    if (!confirm('Marquer les courses comme terminées ? La liste sera archivée.')) return
    try {
      await completeShoppingList()
      sessionStorage.removeItem('appcook_abandoned')  // nettoyage après archivage
      navigate('/shopping')
    } catch (e) {
      alert('Erreur lors de la clôture : ' + e.message)
    }
  }

  const copyToClipboard = () => {
    const lines = categories.flatMap(cat => [
      `\n── ${cat} ──`,
      ...grouped[cat].map(item =>
        item.qty ? `• ${item.name} — ${item.qty % 1 === 0 ? item.qty : item.qty.toFixed(1)} ${item.unit}` : `• ${item.name}`
      ),
    ])
    navigator.clipboard.writeText(lines.join('\n').trim())
      .catch(() => alert('Copie non disponible (HTTP requis). Appuyez longuement sur la liste pour copier manuellement.'))
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
      Chargement...
    </div>
  )

  if (!listId) return (
    <div style={{ padding: '32px 16px', textAlign: 'center' }}>
      <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🛒</div>
      <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
        Pas de liste de courses active.
      </p>
      <button className="btn-primary" onClick={() => navigate('/shopping')}>
        Créer une liste
      </button>
    </div>
  )

  return (
    <div style={{ paddingBottom: '100px' }}>

      {/* Header */}
      <div style={{ padding: '16px 16px 0', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <h2 style={{ margin: 0, flex: 1 }}>Liste de courses</h2>
        <button onClick={copyToClipboard}
          style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px', padding: '6px 12px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem' }}>
          📋
        </button>
        <button
          onClick={() => navigate('/shopping/new')}
          style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px', padding: '6px 12px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem' }}
          title="Nouvelle liste"
        >
          ✚
        </button>
      </div>

      {/* Progression */}
      <ProgressBar current={checkedCount} total={items.length} label="Articles cochés" />


      {/* Message de complétion */}
      {allDone && (
        <div style={{
          margin: '0 16px 16px', padding: '16px', borderRadius: '12px',
          background: 'rgba(76,175,80,0.15)', textAlign: 'center',
          color: 'var(--success)', fontWeight: 600,
        }}>
          🎉 Tous les articles sont cochés !
        </div>
      )}

      {/* Items groupés par catégorie */}
      <div style={{ padding: '0 16px' }}>
        {categories.map(cat => (
          <div key={cat} style={{ marginBottom: '20px' }}>

            {/* Titre de catégorie */}
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase',
              letterSpacing: '0.08em', color: 'var(--text-muted)',
              marginBottom: '8px', paddingLeft: '4px',
            }}>
              {cat}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {grouped[cat].map(item => (
                <ShoppingItem
                  key={item.id}
                  item={item}
                  onToggle={() => handleToggle(item)}
                  onDelete={() => handleDelete(item.id)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Ajouter un article manuel */}
      <div style={{ padding: '0 16px', marginBottom: '24px' }}>
        <div style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase',
          letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Ajouter un article
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            ref={inputRef}
            value={newItemName}
            onChange={e => setNewItemName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAddItem()}
            placeholder="Liquide vaisselle, PQ..."
            style={{
              flex: 1, padding: '12px 14px', borderRadius: '12px', border: 'none',
              background: 'var(--bg-secondary)', color: 'var(--text-primary)',
              fontSize: '0.95rem', outline: 'none',
            }}
          />
          <button
            onClick={handleAddItem}
            disabled={!newItemName.trim() || addingItem}
            style={{
              background: 'var(--accent)', border: 'none', borderRadius: '12px',
              width: '48px', color: 'white', fontSize: '1.3rem', cursor: 'pointer',
              opacity: !newItemName.trim() ? 0.4 : 1,
            }}
          >
            +
          </button>
        </div>
      </div>

      {/* Bouton Terminer */}
      <div style={{ padding: '0 16px' }}>
        <button
          onClick={handleComplete}
          disabled={items.length === 0}
          style={{
            width: '100%', padding: '14px', borderRadius: '14px', border: 'none',
            background: allDone ? 'var(--success)' : 'var(--bg-secondary)',
            color: allDone ? 'white' : 'var(--text-muted)',
            fontWeight: 600, fontSize: '0.95rem', cursor: items.length === 0 ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s', opacity: items.length === 0 ? 0.4 : 1,
          }}
        >
          {allDone ? '✓ Courses terminées — Archiver' : 'Terminer les courses'}
        </button>
      </div>

    </div>
  )
}

function ShoppingItem({ item, onToggle, onDelete }) {
  const [showDelete, setShowDelete] = useState(false)

  // Couleurs selon l'état
  const isMissing = item.missing
  const isDone = item.checked || item.missing
  const checkBg = isMissing ? '#FF9800' : isDone ? 'var(--success)' : 'transparent'
  const checkBorder = isMissing ? '#FF9800' : isDone ? 'var(--success)' : 'var(--bg-tertiary)'
  const rowBg = isDone ? 'var(--bg-tertiary)' : 'var(--bg-secondary)'

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '14px',
      padding: '13px 16px', borderRadius: '12px',
      background: rowBg, transition: 'background 0.15s',
      opacity: isDone ? 0.6 : 1, position: 'relative',
    }}>
      {/* Checkbox — tap pour cycler : ☐ → ✓ → ⚠ → ☐ */}
      <div
        onClick={onToggle}
        style={{
          width: '28px', height: '28px', borderRadius: '8px', flexShrink: 0,
          border: `2px solid ${checkBorder}`,
          background: checkBg,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', fontSize: isMissing ? '0.85rem' : '1rem',
          cursor: 'pointer', transition: 'all 0.15s',
        }}
      >
        {isMissing ? '⚠' : isDone ? '✓' : ''}
      </div>

      {/* Nom + quantité */}
      <div onClick={onToggle} style={{ flex: 1, cursor: 'pointer' }}>
        <span style={{
          fontSize: '1rem',
          textDecoration: isDone ? 'line-through' : 'none',
          color: isDone ? 'var(--text-muted)' : 'var(--text-primary)',
        }}>
          {item.name}
        </span>
        {item.qty != null && (
          <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
            {item.qty % 1 === 0 ? item.qty : item.qty.toFixed(1)} {item.unit}
          </span>
        )}
        {/* Indication : re-taper pour marquer manquant */}
        {isDone && !isMissing && (
          <span style={{
            marginLeft: '8px', fontSize: '0.68rem', color: 'var(--text-muted)',
            opacity: 0.6,
          }}>
            · retaper → ⚠
          </span>
        )}
        {/* Badge manquant reporté */}
        {item.source === 'missing' && !isDone && (
          <span style={{
            marginLeft: '8px', fontSize: '0.7rem', color: '#FF9800',
            background: 'rgba(255,152,0,0.12)', padding: '1px 6px', borderRadius: '6px',
          }}>
            reporté
          </span>
        )}
      </div>

      {/* Bouton supprimer (items manuels uniquement) */}
      {(item.source === 'manual' || item.source === 'missing') && (
        <span
          onClick={() => setShowDelete(v => !v)}
          style={{
            fontSize: '0.7rem', color: 'var(--text-muted)', cursor: 'pointer',
            padding: '2px 6px', borderRadius: '6px', background: 'var(--bg-tertiary)',
          }}
        >
          ✏
        </span>
      )}
      {(item.source === 'manual' || item.source === 'missing') && showDelete && (
        <button
          onClick={onDelete}
          style={{
            background: '#f44336', border: 'none', borderRadius: '8px',
            color: 'white', padding: '4px 10px', cursor: 'pointer', fontSize: '0.8rem',
          }}
        >
          Suppr.
        </button>
      )}
    </div>
  )
}
