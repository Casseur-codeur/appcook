/**
 * Carte d'une étape en Focus Mode.
 * Props : step { step_no, title, instruction, time_min, ingredients }
 *         nextStep : étape suivante (pour l'aperçu), peut être null
 *         total    : nombre total d'étapes
 */
export default function StepCard({ step, nextStep, total, scale = 1 }) {
  const { step_no, title, instruction, time_min, ingredients } = step

  const formatQty = (qty) => {
    const scaled = qty * scale
    return scaled % 1 === 0 ? scaled : scaled.toFixed(1)
  }

  return (
    <div style={{ padding: '16px' }}>

      {/* Badge étape */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: '8px',
        background: 'var(--accent)', color: 'white',
        borderRadius: '20px', padding: '4px 12px',
        fontSize: '0.85rem', fontWeight: 700, marginBottom: '16px',
      }}>
        Étape {step_no}/{total}
      </div>

      {/* Titre optionnel */}
      {title && (
        <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
          {title}
        </div>
      )}

      {/* Instruction principale */}
      <div style={{
        fontSize: '1.3rem', lineHeight: 1.5,
        color: 'var(--text-primary)', fontWeight: 400,
        marginBottom: '16px',
      }}>
        {instruction}
      </div>

      {/* Ingrédients de cette étape */}
      {ingredients && ingredients.length > 0 && (
        <div style={{
          background: 'var(--bg-tertiary)', borderRadius: '12px',
          padding: '12px 14px', marginBottom: '12px',
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px', letterSpacing: '0.05em' }}>
            INGRÉDIENTS
          </div>
          {ingredients.map((ing, i) => (
            <div key={i} style={{
              display: 'flex', justifyContent: 'space-between',
              fontSize: '0.95rem', color: 'var(--text-primary)',
              padding: '4px 0',
              borderTop: i > 0 ? '1px solid var(--bg-secondary)' : 'none',
            }}>
              <span>{ing.name}</span>
              {ing.qty && <span style={{ color: 'var(--text-muted)' }}>{formatQty(ing.qty)} {ing.unit}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Aperçu étape suivante */}
      {nextStep && (
        <div style={{
          borderTop: '1px solid var(--bg-tertiary)', paddingTop: '12px', marginTop: '4px',
        }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '4px', letterSpacing: '0.05em' }}>
            ENSUITE →
          </div>
          <div style={{
            fontSize: '0.85rem', color: 'var(--text-muted)',
            overflow: 'hidden', textOverflow: 'ellipsis',
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
          }}>
            {nextStep.instruction}
          </div>
        </div>
      )}
    </div>
  )
}
