import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getRecipe, createFullRecipe, updateFullRecipe } from '../../api/client'
import IngredientSearch from '../../components/IngredientSearch'

// ─────────────────────────────────────────────────────────────────────────────
// Constantes
// ─────────────────────────────────────────────────────────────────────────────

const UNITS = ['', 'g', 'kg', 'ml', 'cl', 'l', 'pièce', 'gousse', 'tranche', 'cube', 'pincée', 'cs', 'cc']

let _nextId = 1
const uid = () => `_${_nextId++}`

// ─────────────────────────────────────────────────────────────────────────────
// Helpers styles inline
// ─────────────────────────────────────────────────────────────────────────────

const inputStyle = {
  background: 'var(--bg-tertiary)', border: 'none', borderRadius: '10px',
  padding: '10px 12px', color: 'var(--text-primary)', fontSize: '0.95rem',
  outline: 'none', width: '100%',
}
const smallInputStyle = {
  background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
  padding: '8px 10px', color: 'var(--text-primary)', fontSize: '0.85rem',
  outline: 'none',
}
const iconBtnStyle = {
  background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
  padding: '6px 10px', color: 'var(--text-muted)', cursor: 'pointer',
  fontSize: '0.8rem', flexShrink: 0,
}

// ─────────────────────────────────────────────────────────────────────────────
// Sous-composant : ligne d'un ingrédient
// ─────────────────────────────────────────────────────────────────────────────

function IngredientRow({ ing, onChange, onDelete }) {
  return (
    <div style={{
      background: 'var(--bg-tertiary)', borderRadius: '12px',
      padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px',
    }}>
      {/* Ligne principale */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ flex: 1, fontWeight: 500, fontSize: '0.9rem', minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {ing.name}
        </span>
        {/* Quantité */}
        <input
          type="number" min="0" step="any"
          value={ing.qty}
          onChange={e => onChange({ ...ing, qty: e.target.value })}
          placeholder="Qté"
          style={{ ...smallInputStyle, width: '68px', textAlign: 'center' }}
        />
        {/* Unité */}
        <select
          value={ing.unit}
          onChange={e => onChange({ ...ing, unit: e.target.value })}
          style={{ ...smallInputStyle, cursor: 'pointer' }}
        >
          {UNITS.map(u => <option key={u} value={u}>{u || '—'}</option>)}
        </select>
        {/* Optional toggle */}
        <button
          onClick={() => onChange({ ...ing, optional: !ing.optional })}
          style={{
            ...iconBtnStyle,
            background: ing.optional ? 'rgba(255,152,0,0.2)' : 'var(--bg-tertiary)',
            color: ing.optional ? '#FF9800' : 'var(--text-muted)',
          }}
        >
          {ing.optional ? 'Opt.' : 'Requis'}
        </button>
        {/* Supprimer */}
        <button
          onClick={onDelete}
          style={{ ...iconBtnStyle, color: '#f44336', background: 'rgba(244,67,54,0.1)' }}
        >
          ✕
        </button>
      </div>
      {/* Notes */}
      <input
        value={ing.notes}
        onChange={e => onChange({ ...ing, notes: e.target.value })}
        placeholder="Notes (ex : émincé finement)"
        style={{ ...smallInputStyle, width: '100%' }}
      />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Sous-composant : carte d'une étape
// ─────────────────────────────────────────────────────────────────────────────

function StepCard({ step, index, total, allIngredients, onChange, onDelete, onMoveUp, onMoveDown }) {
  const toggleIngredient = (name) => {
    const names = step.ingredient_names.includes(name)
      ? step.ingredient_names.filter(n => n !== name)
      : [...step.ingredient_names, name]
    onChange({ ...step, ingredient_names: names })
  }

  return (
    <div style={{
      background: 'var(--bg-secondary)', borderRadius: '14px',
      padding: '14px', border: '1.5px solid var(--bg-tertiary)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        {/* Badge numéro */}
        <div style={{
          minWidth: '28px', height: '28px', borderRadius: '8px',
          background: 'var(--accent)', color: 'white',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 700, fontSize: '0.85rem', flexShrink: 0,
        }}>
          {index + 1}
        </div>
        {/* Titre */}
        <input
          value={step.title}
          onChange={e => onChange({ ...step, title: e.target.value })}
          placeholder="Titre de l'étape (optionnel)"
          style={{ ...smallInputStyle, flex: 1 }}
        />
        {/* Durée */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
          <input
            type="number" min="0" step="1"
            value={step.time_min}
            onChange={e => onChange({ ...step, time_min: e.target.value })}
            placeholder="0"
            style={{ ...smallInputStyle, width: '48px', textAlign: 'center' }}
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>min</span>
        </div>
        {/* Reorder */}
        <button onClick={onMoveUp} disabled={index === 0}
          style={{ ...iconBtnStyle, opacity: index === 0 ? 0.3 : 1 }}>↑</button>
        <button onClick={onMoveDown} disabled={index === total - 1}
          style={{ ...iconBtnStyle, opacity: index === total - 1 ? 0.3 : 1 }}>↓</button>
        {/* Supprimer */}
        <button onClick={onDelete}
          style={{ ...iconBtnStyle, color: '#f44336', background: 'rgba(244,67,54,0.1)' }}>✕</button>
      </div>

      {/* Instruction */}
      <textarea
        value={step.instruction}
        onChange={e => onChange({ ...step, instruction: e.target.value })}
        placeholder="Instruction * (ex : Faire revenir le poulet 5 min à feu vif)"
        rows={3}
        style={{
          ...inputStyle, resize: 'vertical', fontSize: '0.9rem', padding: '10px 12px',
        }}
      />

      {/* Chips ingrédients */}
      {allIngredients.length > 0 && (
        <div style={{ marginTop: '10px' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
            Ingrédients utilisés dans cette étape
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {allIngredients.map(ing => {
              const selected = step.ingredient_names.includes(ing.name)
              return (
                <button
                  key={ing.name}
                  onClick={() => toggleIngredient(ing.name)}
                  style={{
                    padding: '4px 12px', borderRadius: '20px', border: 'none',
                    cursor: 'pointer', fontSize: '0.8rem', transition: 'all 0.15s',
                    background: selected ? 'var(--accent)' : 'var(--bg-tertiary)',
                    color: selected ? 'white' : 'var(--text-muted)',
                    fontWeight: selected ? 600 : 400,
                  }}
                >
                  {ing.name}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Composant principal
// ─────────────────────────────────────────────────────────────────────────────

export default function AdminRecipeEdit() {
  const { code } = useParams()
  const navigate = useNavigate()
  const isEdit = !!code

  const [currentStep, setCurrentStep] = useState(0)
  const [form, setForm] = useState({
    name: '', category: '', origin: '', base_servings: 1, is_batch: false, notes: '',
  })
  const [ingredients, setIngredients] = useState([])  // [{ _id, name, qty, unit, optional, notes }]
  const [steps, setSteps] = useState([])              // [{ _id, title, instruction, time_min, ingredient_names }]
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(isEdit)

  // ── Chargement de la recette en mode édition ──────────────────────────────
  useEffect(() => {
    if (!isEdit) return
    getRecipe(code).then(r => {
      setForm({
        name: r.name, category: r.category, origin: r.origin,
        base_servings: r.base_servings, is_batch: r.is_batch, notes: r.notes,
      })
      setIngredients(r.ingredients.map(i => ({
        _id: uid(), name: i.name,
        qty: i.qty != null ? String(i.qty) : '',
        unit: i.unit || '', optional: i.optional, notes: i.notes || '',
      })))
      setSteps(r.steps.map(s => ({
        _id: uid(), title: s.title || '',
        instruction: s.instruction,
        time_min: s.time_min != null ? String(s.time_min) : '',
        ingredient_names: (s.ingredients || []).map(i => i.name),
      })))
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [code])

  // ── Handlers ingrédients ──────────────────────────────────────────────────
  const handleAddIngredient = ({ name }) => {
    if (ingredients.some(i => i.name.toLowerCase() === name.toLowerCase())) return
    setIngredients(prev => [...prev, { _id: uid(), name, qty: '', unit: '', optional: false, notes: '' }])
  }

  const handleChangeIngredient = (id, updated) => {
    setIngredients(prev => prev.map(i => i._id === id ? updated : i))
  }

  const handleDeleteIngredient = (id, name) => {
    setIngredients(prev => prev.filter(i => i._id !== id))
    // Retirer cet ingrédient de toutes les étapes
    setSteps(prev => prev.map(s => ({
      ...s,
      ingredient_names: s.ingredient_names.filter(n => n !== name),
    })))
  }

  // ── Handlers étapes ───────────────────────────────────────────────────────
  const handleAddStep = () => {
    setSteps(prev => [...prev, {
      _id: uid(), title: '', instruction: '', time_min: '', ingredient_names: [],
    }])
  }

  const handleChangeStep = (id, updated) => {
    setSteps(prev => prev.map(s => s._id === id ? updated : s))
  }

  const handleDeleteStep = (id) => {
    setSteps(prev => prev.filter(s => s._id !== id))
  }

  const handleMoveStep = (index, dir) => {
    setSteps(prev => {
      const next = [...prev]
      const target = index + dir
      if (target < 0 || target >= next.length) return next
      ;[next[index], next[target]] = [next[target], next[index]]
      return next
    })
  }

  // ── Sauvegarde ────────────────────────────────────────────────────────────
  const handleSave = async () => {
    setError(null)
    // Validation minimale
    if (!form.name.trim()) { setCurrentStep(0); return }
    if (steps.length === 0) {
      setError('Ajoute au moins une étape.')
      return
    }
    const invalidStep = steps.findIndex(s => !s.instruction.trim())
    if (invalidStep !== -1) {
      setError(`L'étape ${invalidStep + 1} n'a pas d'instruction.`)
      return
    }

    setSaving(true)
    try {
      const payload = {
        name: form.name.trim(),
        category: form.category.trim(),
        origin: form.origin.trim(),
        base_servings: parseFloat(form.base_servings) || 1,
        is_batch: form.is_batch,
        notes: form.notes.trim(),
        ingredients: ingredients.map(i => ({
          name: i.name,
          qty: i.qty !== '' ? parseFloat(i.qty) : null,
          unit: i.unit,
          optional: i.optional,
          notes: i.notes,
        })),
        steps: steps.map((s, idx) => ({
          step_no: idx + 1,
          title: s.title.trim(),
          instruction: s.instruction.trim(),
          time_min: s.time_min !== '' ? parseFloat(s.time_min) : null,
          ingredient_names: s.ingredient_names,
        })),
      }

      if (isEdit) {
        await updateFullRecipe(code, payload)
      } else {
        await createFullRecipe(payload)
      }
      navigate('/admin')
    } catch (e) {
      setError('Erreur : ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Rendu
  // ─────────────────────────────────────────────────────────────────────────

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
      Chargement...
    </div>
  )

  const STEP_LABELS = ['Infos', 'Ingrédients', 'Étapes']

  return (
    <div style={{ padding: '16px', paddingBottom: '32px' }}>

      {/* Fil d'étapes */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {STEP_LABELS.map((label, i) => (
          <div
            key={i}
            onClick={() => i < currentStep && setCurrentStep(i)}
            style={{
              flex: 1, textAlign: 'center', fontSize: '0.75rem',
              fontWeight: i === currentStep ? 700 : 400,
              color: i === currentStep ? 'var(--accent)' : i < currentStep ? 'var(--success)' : 'var(--text-muted)',
              borderBottom: `2px solid ${i === currentStep ? 'var(--accent)' : i < currentStep ? 'var(--success)' : 'var(--bg-tertiary)'}`,
              paddingBottom: '6px',
              cursor: i < currentStep ? 'pointer' : 'default',
            }}
          >
            {i < currentStep ? '✓ ' : ''}{label}
          </div>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════
          ÉTAPE 0 : Infos de base
      ═══════════════════════════════════════════════════ */}
      {currentStep === 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Nom */}
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Nom de la recette *
            </label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              placeholder="Ex : Poulet cajun au riz"
              style={inputStyle}
              autoFocus
            />
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            {/* Catégorie */}
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Catégorie</label>
              <input type="text" value={form.category}
                onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
                placeholder="Viande, Féculents..."
                style={inputStyle} />
            </div>
            {/* Cuisine */}
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Cuisine</label>
              <input type="text" value={form.origin}
                onChange={e => setForm(f => ({ ...f, origin: e.target.value }))}
                placeholder="Mexicain, Japonais..."
                style={inputStyle} />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
            {/* Portions */}
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Portions de base</label>
              <input
                type="number" min="1" value={form.base_servings}
                onChange={e => setForm(f => ({ ...f, base_servings: e.target.value }))}
                style={inputStyle}
              />
            </div>
            {/* Batch */}
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Batch cooking</label>
              <button
                onClick={() => setForm(f => ({ ...f, is_batch: !f.is_batch }))}
                style={{
                  padding: '10px 16px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                  background: form.is_batch ? 'rgba(76,175,80,0.2)' : 'var(--bg-tertiary)',
                  color: form.is_batch ? 'var(--success)' : 'var(--text-muted)',
                  fontWeight: form.is_batch ? 600 : 400, fontSize: '0.9rem', whiteSpace: 'nowrap',
                }}
              >
                🥡 {form.is_batch ? 'Oui' : 'Non'}
              </button>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Notes</label>
            <textarea
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              placeholder="Notes libres, conseils..."
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>

          <button
            className="btn-primary"
            onClick={() => setCurrentStep(1)}
            disabled={!form.name.trim()}
            style={{ opacity: !form.name.trim() ? 0.4 : 1, marginTop: '4px' }}
          >
            Suivant — Ingrédients →
          </button>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          ÉTAPE 1 : Ingrédients
      ═══════════════════════════════════════════════════ */}
      {currentStep === 1 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Searchbox */}
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Cherche un ingrédient ou tape un nouveau nom pour le créer
            </div>
            <IngredientSearch onSelect={handleAddIngredient} />
          </div>

          {/* Liste des ingrédients ajoutés */}
          {ingredients.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {ingredients.length} ingrédient{ingredients.length > 1 ? 's' : ''}
              </div>
              {ingredients.map(ing => (
                <IngredientRow
                  key={ing._id}
                  ing={ing}
                  onChange={updated => handleChangeIngredient(ing._id, updated)}
                  onDelete={() => handleDeleteIngredient(ing._id, ing.name)}
                />
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '0.9rem', background: 'var(--bg-secondary)', borderRadius: '12px' }}>
              Aucun ingrédient ajouté
            </div>
          )}

          {/* Navigation */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
            <button className="btn-secondary" style={{ flex: 1 }} onClick={() => setCurrentStep(0)}>
              ← Retour
            </button>
            <button className="btn-primary" style={{ flex: 2 }} onClick={() => setCurrentStep(2)}>
              Suivant — Étapes →
            </button>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════
          ÉTAPE 2 : Étapes + Sauvegarde
      ═══════════════════════════════════════════════════ */}
      {currentStep === 2 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Résumé ingrédients */}
          {ingredients.length > 0 && (
            <div style={{
              background: 'var(--bg-secondary)', borderRadius: '12px',
              padding: '10px 14px', fontSize: '0.82rem', color: 'var(--text-muted)',
            }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Ingrédients disponibles : </span>
              {ingredients.map(i => i.name).join(', ')}
            </div>
          )}

          {/* Liste des étapes */}
          {steps.map((step, index) => (
            <StepCard
              key={step._id}
              step={step}
              index={index}
              total={steps.length}
              allIngredients={ingredients}
              onChange={updated => handleChangeStep(step._id, updated)}
              onDelete={() => handleDeleteStep(step._id)}
              onMoveUp={() => handleMoveStep(index, -1)}
              onMoveDown={() => handleMoveStep(index, 1)}
            />
          ))}

          {/* Ajouter une étape */}
          <button
            onClick={handleAddStep}
            style={{
              width: '100%', padding: '14px', borderRadius: '12px',
              border: '2px dashed var(--bg-tertiary)', background: 'transparent',
              color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem',
              transition: 'all 0.15s',
            }}
            onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--accent)' }}
            onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--bg-tertiary)'; e.currentTarget.style.color = 'var(--text-muted)' }}
          >
            + Ajouter une étape
          </button>

          {/* Message d'erreur */}
          {error && (
            <div style={{
              padding: '12px 14px', borderRadius: '10px',
              background: 'rgba(244,67,54,0.12)', color: '#f44336', fontSize: '0.9rem',
            }}>
              {error}
            </div>
          )}

          {/* Navigation + Enregistrer */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
            <button className="btn-secondary" style={{ flex: 1 }} onClick={() => setCurrentStep(1)}>
              ← Retour
            </button>
            <button
              className="btn-primary"
              style={{ flex: 2, opacity: saving ? 0.5 : 1 }}
              disabled={saving || steps.length === 0}
              onClick={handleSave}
            >
              {saving
                ? '⏳ Enregistrement...'
                : isEdit
                  ? '✓ Enregistrer les modifications'
                  : '✓ Créer la recette'}
            </button>
          </div>

          {steps.length === 0 && (
            <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', margin: 0 }}>
              Ajoute au moins une étape pour pouvoir enregistrer
            </p>
          )}
        </div>
      )}

    </div>
  )
}
