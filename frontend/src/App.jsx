import { useState, useEffect, Component } from 'react'
import { Routes, Route } from 'react-router-dom'
import BottomNav from './components/BottomNav'
import LoadingScreen from './components/LoadingScreen'
import Home from './pages/Home'
import Recipes from './pages/Recipes'
import RecipeDetail from './pages/RecipeDetail'
import FocusMode from './pages/FocusMode'
import ShoppingSelect from './pages/ShoppingSelect'
import ShoppingList from './pages/ShoppingList'
import Stats from './pages/Stats'
import Admin from './pages/Admin'

// ─── ErrorBoundary globale ───────────────────────────────────────────────────
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          height: '100vh', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          padding: '32px', textAlign: 'center', background: 'var(--bg-primary)',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>💥</div>
          <h2 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>Oups, quelque chose a planté</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
            Une erreur inattendue s&#39;est produite.
          </p>
          <button
            className="btn-primary"
            onClick={() => { this.setState({ hasError: false }); window.location.href = '/' }}
          >
            Retour à l&#39;accueil
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  const [appReady, setAppReady] = useState(false)

  useEffect(() => {
    // Splash screen au démarrage — laisse l'API le temps de répondre
    const timer = setTimeout(() => setAppReady(true), 1500)
    return () => clearTimeout(timer)
  }, [])

  if (!appReady) return <LoadingScreen />

  return (
    <ErrorBoundary>
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>

      {/* Zone de contenu principale (scrollable) */}
      <main style={{ flex: 1, overflowY: 'auto', paddingBottom: '72px' }}>
        <Routes>
          <Route path="/"                    element={<Home />} />
          <Route path="/recipes"             element={<Recipes />} />
          <Route path="/recipes/:code"       element={<RecipeDetail />} />
          <Route path="/recipes/:code/focus" element={<FocusMode />} />
          <Route path="/shopping"            element={<ShoppingSelect />} />
          <Route path="/shopping/new"        element={<ShoppingSelect forceNew />} />
          <Route path="/shopping/list"       element={<ShoppingList />} />
          <Route path="/stats"               element={<Stats />} />
          <Route path="/admin/*"             element={<Admin />} />
        </Routes>
      </main>

      {/* Bottom nav — cachée en Focus Mode via CSS */}
      <BottomNav />

    </div>
    </ErrorBoundary>
  )
}
