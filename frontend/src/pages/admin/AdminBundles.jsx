import { useState, useEffect } from 'react'
import {
  getBundles, createBundle, updateBundle, deleteBundle,
  addBundleItem, updateBundleItem, deleteBundleItem,
} from '../../api/client'

// ─────────────────────────────────────────────────────────────────────────────
// Constantes
// ─────────────────────────────────────────────────────────────────────────────

const UNITS = ['', 'g', 'kg', 'ml', 'cl', 'l', 'pièce', 'gousse', 'tranche', 'cube', 'pincée', 'cs', 'cc']

const CATEGORIES = ['Épicerie', 'Frais', 'Boucherie', 'Fruits & Légumes', 'Surgelés', 'Boissons', 'Hygiène', 'Divers']

const EMPTY_ITEM = { name: '', qty: '', unit: 'pièce', category: 'Divers' }

// ─────────────────────────────────────────────────────────────────────────────
// Styles réutilisables
// ─────────────────────────────────────────────────────────────────────────────

const inputStyle = {
  background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
  padding: '8px 10px', color: 'var(--text-primary)', fontSize: '0.9rem',
  outline: 'none',
}
const iconBtn = (color = 'var(--text-muted)', bg = 'var(--bg-tertiary)') => ({
  background: bg, border: 'none', borderRadius: '8px',
  padding: '6px 10px', color, cursor: 'pointer', fontSize: '0.8rem', flexShrink: 0,
})

// ─────────────────────────────────────────────────────────────────────────────
// Sous-composant : ligne d'un article
// ─────────────────────────────────────────────────────────────────────────────

function ItemRow({ item, bundleId, onDelete, onSave }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: item.name,
    qty: item.qty != null ? String(item.qty) : '',
    unit: item.unit || '',
    category: item.category || 'Divers',
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    await onSave(item.id, {
      name: form.name.trim(),
      qty: form.qty !== '' ? parseFloat(form.qty) : null,
      unit: form.unit,
      category: form.category,
    })
    setEditing(false)
    setSaving(false)
  }

  if (editing) {
    return (
      <div style={{
        background: 'var(--bg-primary)', borderRadius: '10px',
        padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px',
      }}>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          <input
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            placeholder="Nom *"
            style={{ ...inputStyle, flex: 2, minWidth: '120px' }}
          />
          <input
            type="number" min="0" step="any"
            value={form.qty}
            onChange={e => setForm(f => ({ ...f, qty: e.target.value }))}
            placeholder="Qté"
            style={{ ...inputStyle, width: '64px', textAlign: 'center' }}
          />
          <select
            value={form.unit}
            onChange={e => setForm(f => ({ ...f, unit: e.target.value }))}
            style={{ ...inputStyle, cursor: 'pointer' }}
          >
            {UNITS.map(u => <option key={u} value={u}>{u || '—'}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <select
            value={form.category}
            onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
            style={{ ...inputStyle, flex: 1, cursor: 'pointer' }}
          >
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <button onClick={handleSave} disabled={!form.name.trim() || saving}
            style={{ ...iconBtn('white', 'var(--accent)'), padding: '7px 12px' }}>
            {saving ? '...' : '✓'}
          </button>
          <button onClick={() => setEditing(false)} style={iconBtn()}>✕</button>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '10px',
      padding: '8px 10px', borderRadius: '8px',
      background: 'var(--bg-primary)',
    }}>
      <span style={{ flex: 1, fontSize: '0.9rem' }}>{item.name}</span>
      <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
        {item.qty != null ? `${item.qty % 1 === 0 ? item.qty : item.qty.toFixed(1)} ${item.unit}` : item.unit || ''}
      </span>
      <span style={{
        fontSize: '0.72rem', padding: '2px 8px', borderRadius: '20px',
        background: 'var(--bg-tertiary)', color: 'var(--text-muted)', whiteSpace: 'nowrap',
      }}>
        {item.category}
      </span>
      <button onClick={() => setEditing(true)} style={iconBtn()}>✏</button>
      <button onClick={() => onDelete(item.id)}
        style={iconBtn('#f44336', 'rgba(244,67,54,0.1)')}>✕</button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Sous-composant : formulaire ajout d'un article
// ─────────────────────────────────────────────────────────────────────────────

function AddItemForm({ onAdd, onCancel }) {
  const [form, setForm] = useState(EMPTY_ITEM)
  const [saving, setSaving] = useState(false)

  const handleAdd = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    await onAdd({
      name: form.name.trim(),
      qty: form.qty !== '' ? parseFloat(form.qty) : null,
      unit: form.unit,
      category: form.category,
    })
    setForm(EMPTY_ITEM)
    setSaving(false)
  }

  return (
    <div style={{
      background: 'var(--bg-primary)', borderRadius: '10px',
      padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px',
      border: '1.5px dashed var(--accent)',
    }}>
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        <input
          value={form.name}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          onKeyDown={e => e.key === 'Enter' && handleAdd()}
          placeholder="Nom de l'article *"
          style={{ ...inputStyle, flex: 2, minWidth: '120px' }}
          autoFocus
        />
        <input
          type="number" min="0" step="any"
          value={form.qty}
          onChange={e => setForm(f => ({ ...f, qty: e.target.value }))}
          placeholder="Qté"
          style={{ ...inputStyle, width: '64px', textAlign: 'center' }}
        />
        <select
          value={form.unit}
          onChange={e => setForm(f => ({ ...f, unit: e.target.value }))}
          style={{ ...inputStyle, cursor: 'pointer' }}
        >
          {UNITS.map(u => <option key={u} value={u}>{u || '—'}</option>)}
        </select>
      </div>
      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
        <select
          value={form.category}
          onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
          style={{ ...inputStyle, flex: 1, cursor: 'pointer' }}
        >
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button
          onClick={handleAdd}
          disabled={!form.name.trim() || saving}
          style={{ ...iconBtn('white', 'var(--accent)'), padding: '7px 14px', opacity: !form.name.trim() ? 0.4 : 1 }}
        >
          {saving ? '...' : '+ Ajouter'}
        </button>
        <button onClick={onCancel} style={iconBtn()}>✕</button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Sous-composant : carte d'un bundle
// ─────────────────────────────────────────────────────────────────────────────

function BundleCard({ bundle, expanded, onToggle, onDelete, onSaved }) {
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({ name: bundle.name, icon: bundle.icon })
  const [saving, setSaving] = useState(false)
  const [addingItem, setAddingItem] = useState(false)

  const handleSaveBundle = async () => {
    if (!editForm.name.trim()) return
    setSaving(true)
    try {
      await updateBundle(bundle.id, { name: editForm.name.trim(), icon: editForm.icon || '🛒' })
      await onSaved()
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteItem = async (itemId) => {
    await deleteBundleItem(bundle.id, itemId)
    onSaved()
  }

  const handleSaveItem = async (itemId, data) => {
    await updateBundleItem(bundle.id, itemId, data)
    onSaved()
  }

  const handleAddItem = async (data) => {
    await addBundleItem(bundle.id, data)
    setAddingItem(false)
    onSaved()
  }

  return (
    <div style={{
      background: 'var(--bg-secondary)', borderRadius: '14px',
      border: '1.5px solid var(--bg-tertiary)', overflow: 'hidden',
    }}>
      {/* En-tête du bundle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '14px' }}>
        {editing ? (
          <>
            {/* Icône */}
            <input
              value={editForm.icon}
              onChange={e => setEditForm(f => ({ ...f, icon: e.target.value }))}
              style={{ ...inputStyle, width: '48px', textAlign: 'center', fontSize: '1.2rem', padding: '6px' }}
              maxLength={4}
            />
            {/* Nom */}
            <input
              value={editForm.name}
              onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
              onKeyDown={e => e.key === 'Enter' && handleSaveBundle()}
              style={{ ...inputStyle, flex: 1 }}
              autoFocus
            />
            <button onClick={handleSaveBundle} disabled={!editForm.name.trim() || saving}
              style={{ ...iconBtn('white', 'var(--accent)'), padding: '7px 12px' }}>
              {saving ? '...' : '✓'}
            </button>
            <button onClick={() => setEditing(false)} style={iconBtn()}>✕</button>
          </>
        ) : (
          <>
            {/* Header cliquable pour expand */}
            <div onClick={onToggle} style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, cursor: 'pointer' }}>
              <span style={{ fontSize: '1.4rem' }}>{bundle.icon}</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{bundle.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1px' }}>
                  {bundle.items.length} article{bundle.items.length !== 1 ? 's' : ''}
                </div>
              </div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginLeft: 'auto' }}>
                {expanded ? '▲' : '▼'}
              </span>
            </div>
            <button onClick={() => { setEditing(true); setEditForm({ name: bundle.name, icon: bundle.icon }) }}
              style={iconBtn()}>✏</button>
            <button onClick={() => onDelete(bundle.id, bundle.name)}
              style={iconBtn('#f44336', 'rgba(244,67,54,0.1)')}>✕</button>
          </>
        )}
      </div>

      {/* Contenu dépliable */}
      {expanded && !editing && (
        <div style={{
          padding: '0 14px 14px',
          display: 'flex', flexDirection: 'column', gap: '6px',
          borderTop: '1px solid var(--bg-tertiary)',
          paddingTop: '12px',
        }}>
          {bundle.items.length === 0 && !addingItem && (
            <div style={{ textAlign: 'center', padding: '12px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Aucun article — ajoutes-en un ci-dessous
            </div>
          )}

          {bundle.items.map(item => (
            <ItemRow
              key={item.id}
              item={item}
              bundleId={bundle.id}
              onDelete={handleDeleteItem}
              onSave={handleSaveItem}
            />
          ))}

          {addingItem ? (
            <AddItemForm
              onAdd={handleAddItem}
              onCancel={() => setAddingItem(false)}
            />
          ) : (
            <button
              onClick={() => setAddingItem(true)}
              style={{
                width: '100%', padding: '10px', borderRadius: '10px',
                border: '1.5px dashed var(--bg-tertiary)', background: 'transparent',
                color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem',
                transition: 'all 0.15s', marginTop: '2px',
              }}
              onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--accent)' }}
              onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--bg-tertiary)'; e.currentTarget.style.color = 'var(--text-muted)' }}
            >
              + Ajouter un article
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Composant principal
// ─────────────────────────────────────────────────────────────────────────────

export default function AdminBundles() {
  const [bundles, setBundles] = useState([])
  const [expandedId, setExpandedId] = useState(null)
  const [creating, setCreating] = useState(false)
  const [newBundle, setNewBundle] = useState({ name: '', icon: '🛒' })
  const [saving, setSaving] = useState(false)

  const load = () => getBundles().then(setBundles)
  useEffect(() => { load() }, [])

  const handleCreateBundle = async () => {
    if (!newBundle.name.trim()) return
    setSaving(true)
    try {
      const { id } = await createBundle({ name: newBundle.name.trim(), icon: newBundle.icon || '🛒' })
      await load()
      setExpandedId(id)
      setCreating(false)
      setNewBundle({ name: '', icon: '🛒' })
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteBundle = async (id, name) => {
    if (!confirm(`Supprimer le bundle "${name}" et tous ses articles ?`)) return
    await deleteBundle(id)
    if (expandedId === id) setExpandedId(null)
    load()
  }

  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: '1.1rem' }}>
          Bundles {bundles.length > 0 && <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({bundles.length})</span>}
        </h2>
        {!creating && (
          <button
            className="btn-primary"
            style={{ width: 'auto', padding: '8px 16px', fontSize: '0.9rem' }}
            onClick={() => setCreating(true)}
          >
            + Nouveau
          </button>
        )}
      </div>

      {/* Formulaire de création */}
      {creating && (
        <div style={{
          background: 'var(--bg-secondary)', borderRadius: '14px', padding: '14px',
          border: '1.5px solid var(--accent)', display: 'flex', flexDirection: 'column', gap: '10px',
        }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--accent)', fontWeight: 600 }}>Nouveau bundle</div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              value={newBundle.icon}
              onChange={e => setNewBundle(f => ({ ...f, icon: e.target.value }))}
              style={{ ...inputStyle, width: '52px', textAlign: 'center', fontSize: '1.3rem', padding: '6px' }}
              maxLength={4}
              placeholder="🛒"
            />
            <input
              value={newBundle.name}
              onChange={e => setNewBundle(f => ({ ...f, name: e.target.value }))}
              onKeyDown={e => e.key === 'Enter' && handleCreateBundle()}
              placeholder="Nom du bundle (ex : Courses du mois)"
              style={{ ...inputStyle, flex: 1 }}
              autoFocus
            />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleCreateBundle}
              disabled={!newBundle.name.trim() || saving}
              className="btn-primary"
              style={{ flex: 1, opacity: !newBundle.name.trim() ? 0.4 : 1 }}
            >
              {saving ? '...' : 'Créer'}
            </button>
            <button
              onClick={() => { setCreating(false); setNewBundle({ name: '', icon: '🛒' }) }}
              className="btn-secondary"
              style={{ flex: 1 }}
            >
              Annuler
            </button>
          </div>
        </div>
      )}

      {/* Liste des bundles */}
      {bundles.length === 0 && !creating ? (
        <div style={{
          textAlign: 'center', padding: '40px 24px',
          background: 'var(--bg-secondary)', borderRadius: '14px',
          color: 'var(--text-muted)', fontSize: '0.9rem',
        }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📦</div>
          <div>Aucun bundle créé.</div>
          <div style={{ fontSize: '0.82rem', marginTop: '6px' }}>
            Un bundle = une liste d'articles permanents ajoutés automatiquement aux courses.
          </div>
        </div>
      ) : (
        bundles.map(bundle => (
          <BundleCard
            key={bundle.id}
            bundle={bundle}
            expanded={expandedId === bundle.id}
            onToggle={() => setExpandedId(v => v === bundle.id ? null : bundle.id)}
            onDelete={handleDeleteBundle}
            onSaved={load}
          />
        ))
      )}

    </div>
  )
}
