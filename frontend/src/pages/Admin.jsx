import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'

// --- Sous-pages Admin ---
import AdminRecipes from './admin/AdminRecipes'
import AdminRecipeEdit from './admin/AdminRecipeEdit'
import AdminCatalog from './admin/AdminCatalog'
import AdminImportExport from './admin/AdminImportExport'
import AdminBundles from './admin/AdminBundles'

export default function Admin() {
  return (
    <div>
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
