import { NavLink, useLocation } from 'react-router-dom'

const tabs = [
  { to: '/shopping', icon: '🛒', label: 'Courses'  },
  { to: '/recipes',  icon: '🍳', label: 'Recettes' },
  { to: '/admin',    icon: '⚙️', label: 'Admin'    },
]

export default function BottomNav() {
  const { pathname } = useLocation()

  // Cacher la bottom nav en Focus Mode
  if (pathname.includes('/focus')) return null

  return (
    <nav style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      height: '64px',
      background: 'var(--bg-secondary)',
      borderTop: '1px solid var(--bg-tertiary)',
      display: 'flex',
      zIndex: 100,
    }}>
      {tabs.map(({ to, icon, label }) => (
        <NavLink
          key={to}
          to={to}
          style={({ isActive }) => ({
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '2px',
            textDecoration: 'none',
            color: isActive ? 'var(--accent)' : 'var(--text-muted)',
            fontSize: '0.7rem',
            fontWeight: isActive ? 600 : 400,
            transition: 'color 0.15s',
          })}
        >
          <span style={{ fontSize: '1.4rem', lineHeight: 1 }}>{icon}</span>
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
