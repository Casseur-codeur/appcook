import { useNavigate } from 'react-router-dom'

/**
 * Carte recette pour la grille.
 * Props : recipe { code, name, category, origin, is_batch, total_time }
 *         highlighted : bool — met la carte en avant (suggestion)
 */
export default function RecipeCard({ recipe, highlighted = false }) {
  const navigate = useNavigate()
  const { code, name, origin, is_batch, total_time } = recipe

  const timeLabel = total_time
    ? total_time < 60
      ? `${Math.round(total_time)} min`
      : `${Math.round(total_time / 60)}h${String(Math.round(total_time % 60)).padStart(2, '0')}`
    : null

  return (
    <div
      onClick={() => navigate(`/recipes/${code}`)}
      style={{
        background: highlighted ? 'linear-gradient(135deg, var(--accent-dark), var(--accent))' : 'var(--bg-secondary)',
        borderRadius: '16px',
        padding: '16px',
        cursor: 'pointer',
        border: highlighted ? 'none' : '1px solid var(--bg-tertiary)',
        transition: 'transform 0.1s',
        active: { transform: 'scale(0.98)' },
      }}
    >
      {highlighted && (
        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'rgba(255,255,255,0.8)', marginBottom: '6px', letterSpacing: '0.05em' }}>
          ✨ SUGGÉRÉ POUR TOI
        </div>
      )}

      <div style={{ fontWeight: 600, fontSize: '1rem', color: highlighted ? 'white' : 'var(--text-primary)', marginBottom: '8px' }}>
        {name}
      </div>

      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        {timeLabel && (
          <span style={{
            fontSize: '0.75rem', padding: '3px 8px', borderRadius: '10px',
            background: highlighted ? 'rgba(255,255,255,0.2)' : 'var(--bg-tertiary)',
            color: highlighted ? 'white' : 'var(--text-muted)',
          }}>
            ⏱ {timeLabel}
          </span>
        )}
        {is_batch && (
          <span style={{
            fontSize: '0.75rem', padding: '3px 8px', borderRadius: '10px',
            background: highlighted ? 'rgba(255,255,255,0.2)' : 'rgba(76,175,80,0.15)',
            color: highlighted ? 'white' : 'var(--success)',
          }}>
            🥡 Batch
          </span>
        )}
        {origin && (
          <span style={{
            fontSize: '0.75rem', padding: '3px 8px', borderRadius: '10px',
            background: highlighted ? 'rgba(255,255,255,0.2)' : 'var(--bg-tertiary)',
            color: highlighted ? 'white' : 'var(--text-muted)',
          }}>
            {origin}
          </span>
        )}
      </div>
    </div>
  )
}
