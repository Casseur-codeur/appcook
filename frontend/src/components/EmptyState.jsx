/**
 * EmptyState — illustration + message pour les écrans sans contenu.
 * Props :
 *   title   : string  — titre principal (ex: "Aucune recette")
 *   message : string  — sous-titre explicatif (optionnel)
 *   action  : { label: string, onClick: fn } — bouton CTA (optionnel)
 */
export default function EmptyState({ title, message, action }) {
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
        src="/illustration.png"
        alt="Oh non j'ai faim"
        style={{
          width: '200px',
          height: '200px',
          objectFit: 'contain',
          borderRadius: '16px',
          opacity: 0.9,
        }}
      />

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <p style={{
          margin: 0,
          fontSize: '1.1rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
        }}>
          {title}
        </p>

        {message && (
          <p style={{
            margin: 0,
            fontSize: '0.9rem',
            color: 'var(--text-muted)',
            lineHeight: 1.5,
          }}>
            {message}
          </p>
        )}
      </div>

      {action && (
        <button className="btn-primary" onClick={action.onClick} style={{ marginTop: '8px', width: 'auto', padding: '12px 28px' }}>
          {action.label}
        </button>
      )}
    </div>
  )
}
