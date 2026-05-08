import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getRecipe, exportRecipe } from '../api/client'
import ProgressBar from '../components/ProgressBar'

export default function RecipeDetail() {
  const { code } = useParams()
  const navigate = useNavigate()
  const [recipe, setRecipe] = useState(null)
  const [persons, setPersons] = useState(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  const handleExport = async () => {
    setExporting(true)
    try {
      const data = await exportRecipe(code)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${code}.appcook.json`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  useEffect(() => {
    getRecipe(code).then(r => {
      setRecipe(r)
      setPersons(r.base_servings)
      setLoading(false)
    })
  }, [code])

  if (loading) return (
    <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
      Chargement...
    </div>
  )

  if (!recipe) return (
    <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
      Recette introuvable.
    </div>
  )

  const scale = persons / recipe.base_servings
  const totalTime = recipe.total_time

  const timeLabel = totalTime
    ? `~${Math.round(totalTime)} min`
    : null

  // Ancrage temporel concret (heure de fin estimée)
  const endTime = totalTime
    ? (() => {
        const end = new Date(Date.now() + totalTime * 60 * 1000)
        return `avant ${end.getHours()}h${String(end.getMinutes()).padStart(2, '0')}`
      })()
    : null

  return (
    <div style={{ paddingBottom: '24px' }}>

      {/* Header */}
      <div style={{ padding: '16px 16px 0', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer', padding: '4px' }}
        >
          ←
        </button>
        <h1 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 700, flex: 1 }}>{recipe.name}</h1>
        <button
          onClick={handleExport}
          disabled={exporting}
          title="Exporter en JSON"
          style={{
            background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px',
            padding: '6px 10px', color: 'var(--text-muted)', cursor: 'pointer',
            fontSize: '0.9rem', flexShrink: 0, opacity: exporting ? 0.5 : 1,
          }}
        >
          ↓ JSON
        </button>
      </div>

      {/* Métadonnées */}
      <div style={{ padding: '12px 16px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {timeLabel && (
          <span style={{ background: 'var(--bg-tertiary)', borderRadius: '10px', padding: '4px 10px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            ⏱ {timeLabel}
          </span>
        )}
        {recipe.is_batch && (
          <span style={{ background: 'rgba(76,175,80,0.15)', borderRadius: '10px', padding: '4px 10px', fontSize: '0.85rem', color: 'var(--success)' }}>
            🥡 Batch
          </span>
        )}
        {recipe.origin && (
          <span style={{ background: 'var(--bg-tertiary)', borderRadius: '10px', padding: '4px 10px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {recipe.origin}
          </span>
        )}
      </div>

      {/* Ancrage temporel */}
      {endTime && (
        <div style={{ padding: '0 16px 12px', color: 'var(--accent)', fontSize: '0.95rem', fontWeight: 500 }}>
          ✅ Tu as le temps — terminé {endTime}
        </div>
      )}

      {/* Scaling portions */}
      <div style={{
        margin: '0 16px 16px',
        background: 'var(--bg-secondary)',
        borderRadius: '12px', padding: '12px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Portions</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => setPersons(p => Math.max(1, p - 1))}
            style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px', width: '32px', height: '32px', fontSize: '1.2rem', color: 'var(--text-primary)', cursor: 'pointer' }}
          >−</button>
          <span style={{ fontWeight: 700, fontSize: '1.1rem', minWidth: '24px', textAlign: 'center' }}>{persons}</span>
          <button
            onClick={() => setPersons(p => p + 1)}
            style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px', width: '32px', height: '32px', fontSize: '1.2rem', color: 'var(--text-primary)', cursor: 'pointer' }}
          >+</button>
        </div>
      </div>

      {/* Ingrédients */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ fontWeight: 600, marginBottom: '10px' }}>Ingrédients</div>
        <div style={{ background: 'var(--bg-secondary)', borderRadius: '12px', overflow: 'hidden' }}>
          {recipe.ingredients.map((ing, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between', padding: '10px 14px',
              borderTop: i > 0 ? '1px solid var(--bg-tertiary)' : 'none',
              fontSize: '0.95rem',
            }}>
              <span style={{ color: ing.optional ? 'var(--text-muted)' : 'var(--text-primary)' }}>
                {ing.name}{ing.optional ? ' (optionnel)' : ''}
              </span>
              {ing.qty && (
                <span style={{ color: 'var(--text-muted)' }}>
                  {(ing.qty * scale).toFixed(scale % 1 === 0 ? 0 : 1)} {ing.unit}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Étapes */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ fontWeight: 600, marginBottom: '10px' }}>Préparation</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {recipe.steps.map(step => (
            <div key={step.step_no} style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '12px 14px' }}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                <span style={{
                  background: 'var(--accent)', color: 'white', borderRadius: '50%',
                  width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.75rem', fontWeight: 700, flexShrink: 0, marginTop: '2px',
                }}>
                  {step.step_no}
                </span>
                <div>
                  {step.title && <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '4px' }}>{step.title}</div>}
                  <div style={{ color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: 1.5 }}>{step.instruction}</div>
                  {step.time_min && (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>⏱ {Math.round(step.time_min)} min</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bouton Cuisiner */}
      <div style={{ padding: '0 16px' }}>
        <button
          className="btn-primary"
          style={{ fontSize: '1.1rem', padding: '18px' }}
          onClick={() => navigate(`/recipes/${code}/focus`, { state: { persons } })}
        >
          🎯 Cuisiner maintenant
        </button>
      </div>

    </div>
  )
}
