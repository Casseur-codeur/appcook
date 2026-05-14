import { useEffect, useState } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'

// --- Sous-pages Admin ---
import AdminRecipes from './admin/AdminRecipes'
import AdminRecipeEdit from './admin/AdminRecipeEdit'
import AdminCatalog from './admin/AdminCatalog'
import AdminImportExport from './admin/AdminImportExport'
import AdminBundles from './admin/AdminBundles'
import {
  clearAdminToken,
  hasAdminToken,
  setAdminToken,
  verifyAdminAccess,
} from '../api/client'

export default function Admin() {
  const [token, setToken] = useState('')
  const [unlocked, setUnlocked] = useState(hasAdminToken())
  const [checking, setChecking] = useState(hasAdminToken())
  const [error, setError] = useState('')

  useEffect(() => {
    const syncAuthState = () => {
      setUnlocked(hasAdminToken())
    }

    window.addEventListener('appcook-admin-auth-changed', syncAuthState)
    return () => window.removeEventListener('appcook-admin-auth-changed', syncAuthState)
  }, [])

  useEffect(() => {
    if (!hasAdminToken()) {
      setChecking(false)
      setUnlocked(false)
      return
    }

    setChecking(true)
    verifyAdminAccess()
      .then(() => {
        setUnlocked(true)
        setError('')
      })
      .catch((e) => {
        setUnlocked(false)
        setError(e.message)
      })
      .finally(() => setChecking(false))
  }, [])

  const handleUnlock = async (e) => {
    e.preventDefault()
    setError('')
    setChecking(true)
    setAdminToken(token)
    try {
      await verifyAdminAccess()
      setUnlocked(true)
      setToken('')
    } catch (e2) {
      clearAdminToken()
      setUnlocked(false)
      setError(e2.message)
    } finally {
      setChecking(false)
    }
  }

  const handleLock = () => {
    clearAdminToken()
    setUnlocked(false)
    setToken('')
    setError('')
  }

  if (checking) {
    return (
      <div style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
        Vérification de l'accès admin...
      </div>
    )
  }

  if (!unlocked) {
    return (
      <div style={{ padding: '20px 16px 32px' }}>
        <div style={{
          background: 'var(--bg-secondary)',
          borderRadius: '16px',
          padding: '20px',
          maxWidth: '480px',
          margin: '0 auto',
          border: '1px solid var(--bg-tertiary)',
        }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--warning)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>
            Admin protégé
          </div>
          <h2 style={{ margin: '0 0 8px' }}>Déverrouiller l'espace admin</h2>
          <p style={{ margin: '0 0 16px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            Entre le secret admin du serveur. S'il n'y a pas de variable
            <code> APPCOOK_ADMIN_TOKEN </code>, AppCook en génère un automatiquement
            à côté de la base SQLite et le garde uniquement dans cette session du navigateur.
          </p>

          <form onSubmit={handleUnlock} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Secret admin"
              autoComplete="current-password"
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid var(--bg-tertiary)',
                background: 'var(--bg-tertiary)',
                color: 'var(--text-primary)',
                fontSize: '0.95rem',
                outline: 'none',
              }}
            />
            <button className="btn-primary" type="submit" disabled={!token.trim()}>
              Déverrouiller
            </button>
          </form>

          {error && (
            <div style={{
              marginTop: '12px',
              padding: '12px 14px',
              borderRadius: '12px',
              background: 'rgba(244,67,54,0.12)',
              color: '#ff8a80',
              fontSize: '0.9rem',
            }}>
              {error}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        padding: '12px 16px 0',
      }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Session admin active
        </div>
        <button
          onClick={handleLock}
          style={{
            background: 'var(--bg-tertiary)',
            color: 'var(--text-muted)',
            border: 'none',
            borderRadius: '999px',
            padding: '8px 12px',
            cursor: 'pointer',
            fontSize: '0.8rem',
          }}
        >
          Verrouiller
        </button>
      </div>

      {/* Sous-navigation Admin */}
      <div style={{
        display: 'flex', gap: '0', borderBottom: '1px solid var(--bg-tertiary)',
        padding: '0 16px', overflowX: 'auto',
      }}>
        {[
          { to: '/admin',          label: 'Recettes', exact: true },
          { to: '/admin/catalog',  label: 'Catalogue' },
          { to: '/admin/bundles',  label: 'Bundles' },
          { to: '/admin/io',       label: 'Import/Export' },
        ].map(({ to, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            style={({ isActive }) => ({
              padding: '12px 16px',
              fontSize: '0.9rem',
              fontWeight: isActive ? 600 : 400,
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              textDecoration: 'none',
              borderBottom: isActive ? '2px solid var(--accent)' : '2px solid transparent',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s',
            })}
          >
            {label}
          </NavLink>
        ))}
      </div>

      {/* Contenu de la sous-page */}
      <Routes>
        <Route index           element={<AdminRecipes />} />
        <Route path="new"      element={<AdminRecipeEdit />} />
        <Route path=":code"    element={<AdminRecipeEdit />} />
        <Route path="catalog"  element={<AdminCatalog />} />
        <Route path="bundles"  element={<AdminBundles />} />
        <Route path="io"       element={<AdminImportExport />} />
      </Routes>
    </div>
  )
}
