/**
 * Barre de progression générique.
 * Props : current (int), total (int), label (string optionnel)
 */
export default function ProgressBar({ current, total, label }) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div style={{ padding: '12px 16px 0' }}>
      {label && (
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px',
        }}>
          <span>{label}</span>
          <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{current}/{total}</span>
        </div>
      )}
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
