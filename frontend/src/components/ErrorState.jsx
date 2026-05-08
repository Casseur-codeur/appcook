/**
 * ErrorState — affiché quand l'API plante ou qu'une page plante.
 * Props :
 *   message : string — détail de l'erreur (optionnel)
 *   onRetry : fn     — callback pour le bouton "Réessayer" (optionnel)
 */
export default function ErrorState({ message, onRetry }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      textAlign: 'center',
      gap: '16px',
    }}>
      <img
        src="/icons/icon-192.png"
        alt="Erreur"
        style={{
          width: '96px',
          height: '96px',
          objectFit: 'contain',
          borderRadius: '16px',
          filter: 'grayscale(30%)',
        }}
      />

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <p style={{
          margin: 0,
          fontSize: '1.1rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
        }}>
          Oh non… mais pas de faim cette fois
        </p>

        <p style={{
          margin: 0,
          fontSize: '0.9rem',
          color: 'var(--text-muted)',
          lineHeight: 1.5,
        }}>
          {message || 'Une erreur est survenue. Le chat est aussi surpris que toi.'}
        </p>
      </div>

      {onRetry && (
        <button className="btn-secondary" onClick={onRetry} style={{ marginTop: '8px', width: 'auto', padding: '12px 28px' }}>
          Réessayer
        </button>
      )}
    </div>
  )
}
