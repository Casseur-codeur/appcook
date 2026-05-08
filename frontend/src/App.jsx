import { useState, useEffect } from 'react'
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

export default function App() {
  const [appReady, setAppReady] = useState(false)

  useEffect(() => {
    // Splash screen au démarrage — laisse l'API le temps de répondre
    const timer = setTimeout(() => setAppReady(true), 1500)
    return () => clearTimeout(timer)
  }, [])

  if (!appReady) return <LoadingScreen />

  return (
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
  )
}
