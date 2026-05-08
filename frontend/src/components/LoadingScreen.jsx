import { useEffect, useState } from 'react'

const MESSAGES = [
  'Chargement des recettes...',
  'On réfléchit à ce qu\'on mange...',
  'Le chat juge tes choix alimentaires...',
  'Calcul des courses en cours...',
]

/**
 * LoadingScreen — affiché au démarrage pendant le fetch initial.
 * Props :
 *   message : string — message custom (optionnel, sinon rotation automatique)
 */
export default function LoadingScreen({ message }) {
  const [msgIndex, setMsgIndex] = useState(0)

  useEffect(() => {
    if (message) return
    const interval = setInterval(() => {
      setMsgIndex(i => (i + 1) % MESSAGES.length)
    }, 2000)
    return () => clearInterval(interval)
  }, [message])

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'var(--bg-primary)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '24px',
      zIndex: 9999,
    }}>
      <img
        src="/illustration.png"
        alt="Chargement"
        style={{
          width: '180px',
          height: '180px',
          objectFit: 'contain',
          borderRadius: '16px',
          animation: 'pulse 2s ease-in-out infinite',
        }}
      />

      <p style={{
        margin: 0,
        fontSize: '0.95rem',
        color: 'var(--text-muted)',
        transition: 'opacity 0.3s',
      }}>
        {message || MESSAGES[msgIndex]}
      </p>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50%       { opacity: 0.8; transform: scale(0.97); }
        }
      `}</style>
    </div>
  )
}
