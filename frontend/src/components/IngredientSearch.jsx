import { useState, useEffect, useRef } from 'react'
import { searchIngredients } from '../api/client'

/**
 * Searchbox ingrédients avec création à la volée.
 * Props : onSelect (ingredient) => void
 */
export default function IngredientSearch({ onSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const timeoutRef = useRef(null)

  useEffect(() => {
    clearTimeout(timeoutRef.current)
    if (!query.trim()) { setResults([]); return }

    timeoutRef.current = setTimeout(async () => {
      const data = await searchIngredients(query).catch(() => [])
      const hasExact = data.some(d => d.name.toLowerCase() === query.toLowerCase())
      setResults([
        ...data,
        ...(!hasExact ? [{ id: null, name: `➕ Créer : ${query}` }] : []),
      ])
      setOpen(true)
    }, 300)
  }, [query])

  const handleSelect = (item) => {
    const isNew = item.id === null
    onSelect({ id: item.id, name: isNew ? query : item.name, isNew })
    setQuery('')
    setResults([])
    setOpen(false)
  }

  return (
    <div style={{ position: 'relative' }}>
      <input
        type="text"
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Rechercher un ingrédient..."
        style={{
          width: '100%',
          background: 'var(--bg-tertiary)',
          border: 'none',
          borderRadius: '10px',
          padding: '12px 14px',
          color: 'var(--text-primary)',
          fontSize: '1rem',
          outline: 'none',
        }}
      />
      {open && results.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50,
          background: 'var(--bg-secondary)', borderRadius: '10px',
          border: '1px solid var(--bg-tertiary)', marginTop: '4px',
          maxHeight: '240px', overflowY: 'auto',
        }}>
          {results.map((item, i) => (
            <div
              key={i}
              onClick={() => handleSelect(item)}
              style={{
                padding: '12px 14px',
                cursor: 'pointer',
                borderTop: i > 0 ? '1px solid var(--bg-tertiary)' : 'none',
                color: item.id === null ? 'var(--accent)' : 'var(--text-primary)',
                fontSize: '0.95rem',
              }}
            >
              {item.name}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
