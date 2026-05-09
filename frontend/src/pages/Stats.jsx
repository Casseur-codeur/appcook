import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getStats, updateSettings } from '../api/client'

export default function Stats() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [editingGoal, setEditingGoal] = useState(false)
  const [newGoal, setNewGoal] = useState('')
  const [saving, setSaving] = useState(false)

  const [error, setError] = useState(false)

  useEffect(() => {
    getStats().then(setStats).catch(() => setError(true))
  }, [])

  const handleSaveGoal = async () => {
    const val = parseInt(newGoal)
    if (!val || val < 1 || val > 14) return
    setSaving(true)
    await updateSettings({ weekly_goal: val })
    const fresh = await getStats()
    setStats(fresh)
    setEditingGoal(false)
    setSaving(false)
  }

  if (error) return (
    <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
      <div style={{ fontSize: '2rem', marginBottom: '12px' }}>⚠️</div>
      <p>Impossible de charger les stats.</p>
      <button className="btn-primary" onClick={() => { setError(false); getStats().then(setStats).catch(() => setError(true)) }}>
        Réessayer
      </button>
    </div>
  )

  if (!stats) return (
    <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
      Chargement...
    </div>
  )

  const weekPct = Math.min(100, Math.round((stats.weekly_cooks / stats.weekly_goal) * 100))

  return (
    <div style={{ padding: '16px', paddingBottom: '32px' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <button onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}>←</button>
        <h2 style={{ margin: 0, flex: 1 }}>Mes stats</h2>
      </div>

      {/* Objectif de la semaine */}
      <div style={{ background: 'var(--bg-secondary)', borderRadius: '16px', padding: '20px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem' }}>🎯 Objectif semaine</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
              {stats.weekly_cooks} / {stats.weekly_goal} recette{stats.weekly_goal > 1 ? 's' : ''}
            </div>
          </div>
          {!editingGoal ? (
            <button
              onClick={() => { setNewGoal(String(stats.weekly_goal)); setEditingGoal(true) }}
              style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px', padding: '6px 12px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.8rem' }}
            >
              ✏ Modifier
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              <input
                type="number" min="1" max="14"
                value={newGoal}
                onChange={e => setNewGoal(e.target.value)}
                style={{
                  width: '52px', padding: '6px 8px', borderRadius: '8px', border: 'none',
                  background: 'var(--bg-tertiary)', color: 'var(--text-primary)',
                  fontSize: '0.9rem', textAlign: 'center',
                }}
              />
              <button
                onClick={handleSaveGoal}
                disabled={saving}
                style={{ background: 'var(--accent)', border: 'none', borderRadius: '8px', padding: '6px 10px', color: 'white', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ✓
              </button>
              <button
                onClick={() => setEditingGoal(false)}
                style={{ background: 'var(--bg-tertiary)', border: 'none', borderRadius: '8px', padding: '6px 10px', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* Barre de progression hebdo */}
        <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px', height: '12px', overflow: 'hidden' }}>
          <div style={{
            height: '100%', borderRadius: '8px', transition: 'width 0.4s ease',
            background: weekPct >= 100 ? 'var(--success)' : 'var(--accent)',
            width: `${weekPct}%`,
          }} />
        </div>

        {weekPct >= 100 && (
          <div style={{ marginTop: '10px', color: 'var(--success)', fontWeight: 600, fontSize: '0.9rem', textAlign: 'center' }}>
            🏆 Objectif atteint cette semaine !
          </div>
        )}
      </div>

      {/* Stats globales */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
        <StatCard value={stats.total_cooks} label="Sessions de cuisine" icon="🍳" />
        <StatCard value={stats.unique_recipes_cooked} label="Recettes différentes" icon="📖" />
        <StatCard value={stats.total_lists_completed} label="Listes complétées" icon="🛒" />
        <StatCard value={stats.weekly_cooks} label="Cette semaine" icon="📅" />
      </div>

      {/* Dernières sessions */}
      {stats.recent_cooks && stats.recent_cooks.length > 0 && (
        <div style={{ background: 'var(--bg-secondary)', borderRadius: '16px', padding: '16px' }}>
          <div style={{ fontWeight: 700, marginBottom: '12px', fontSize: '0.95rem' }}>
            🕐 Dernières sessions
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {stats.recent_cooks.map((c, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.9rem' }}>{c.name}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {new Date(c.cooked_at).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}

function StatCard({ value, label, icon }) {
  return (
    <div style={{ background: 'var(--bg-secondary)', borderRadius: '14px', padding: '16px', textAlign: 'center' }}>
      <div style={{ fontSize: '1.6rem', marginBottom: '4px' }}>{icon}</div>
      <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent)' }}>{value}</div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>{label}</div>
    </div>
  )
}
