import { useState, useEffect, useRef } from 'react'

/**
 * Timer countdown par étape.
 * Props : timeMin (float, durée en minutes), onComplete (callback optionnel)
 */
export default function Timer({ timeMin, onComplete }) {
  const totalSec = Math.round((timeMin || 0) * 60)
  const [remaining, setRemaining] = useState(totalSec)
  const [running, setRunning] = useState(false)
  const intervalRef = useRef(null)

  // Reset quand l'étape change
  useEffect(() => {
    setRemaining(Math.round((timeMin || 0) * 60))
    setRunning(false)
    clearInterval(intervalRef.current)
  }, [timeMin])

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => {
        setRemaining(prev => {
          if (prev <= 1) {
            clearInterval(intervalRef.current)
            setRunning(false)
            onComplete?.()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } else {
      clearInterval(intervalRef.current)
    }
    return () => clearInterval(intervalRef.current)
  }, [running, onComplete])

  if (!timeMin) return null

  const min = Math.floor(remaining / 60)
  const sec = remaining % 60
  const pct = totalSec > 0 ? ((totalSec - remaining) / totalSec) * 100 : 0
  const isWarning = remaining <= 30 && remaining > 0
  const isDone = remaining === 0

  return (
    <div style={{
      background: 'var(--bg-tertiary)',
      borderRadius: '12px',
      padding: '12px 16px',
      marginTop: '12px',
    }}>
      {/* Affichage du temps */}
      <div style={{
        textAlign: 'center',
        fontSize: '2rem',
        fontWeight: 700,
        fontVariantNumeric: 'tabular-nums',
        color: isDone ? 'var(--success)' : isWarning ? 'var(--warning)' : 'var(--text-primary)',
        marginBottom: '8px',
      }}>
        {isDone ? '✅ Terminé !' : `${min}:${String(sec).padStart(2, '0')}`}
      </div>

      {/* Barre de progression du timer */}
      {!isDone && (
        <div className="progress-bar" style={{ marginBottom: '12px' }}>
          <div className="progress-bar-fill" style={{ width: `${pct}%`, background: isWarning ? 'var(--warning)' : 'var(--accent)' }} />
        </div>
      )}

      {/* Bouton play/pause */}
      {!isDone && (
        <button
          onClick={() => setRunning(r => !r)}
          style={{
            width: '100%',
            background: running ? 'var(--bg-secondary)' : 'var(--accent)',
            color: running ? 'var(--text-muted)' : 'white',
            border: 'none',
            borderRadius: '8px',
            padding: '10px',
            fontSize: '0.9rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {running ? '⏸ Pause' : '▶ Démarrer'}
        </button>
      )}
    </div>
  )
}
