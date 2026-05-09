/**
 * Import / Export JSON de recettes.
 */
import { useState, useRef } from 'react'
import { importRecipe, exportAllRecipes } from '../../api/client'

export default function AdminImportExport() {
  const [importResults, setImportResults] = useState([])
  const [importing, setImporting] = useState(false)
  const fileInputRef = useRef(null)

  // Importe un ou plusieurs fichiers JSON
  const handleFiles = async (files) => {
    setImporting(true)
    setImportResults([])
    const results = []

    for (const file of files) {
      try {
        const text = await file.text()
        const data = JSON.parse(text)

        // Supporte un fichier = 1 recette OU un fichier = tableau de recettes
        const recipes = Array.isArray(data) ? data : [data]

        for (const recipe of recipes) {
          const result = await importRecipe(recipe)
          const name = recipe?.recipe?.title || file.name
          results.push({ ok: true, message: `✓ "${name}" importée` })
        }
      } catch (e) {
        results.push({ ok: false, message: `✗ ${file.name} — ${e.message}` })
      }
    }

    setImportResults(results)
    setImporting(false)
  }

  const handleFileInput = (e) => {
    if (e.target.files.length > 0) handleFiles(Array.from(e.target.files))
  }

  // Drag & drop
  const handleDrop = (e) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.json'))
    if (files.length > 0) handleFiles(files)
  }

  const handleExportAll = async () => {
    try {
      const exports = await exportAllRecipes()
      const blob = new Blob([JSON.stringify(exports, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'appcook_recettes.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('Erreur export : ' + e.message)
    }
  }

  return (
    <div style={{ padding: '16px' }}>
      <h2 style={{ marginTop: 0, marginBottom: '16px', fontSize: '1.1rem' }}>Import / Export</h2>

      {/* Export */}
      <div style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '16px', marginBottom: '16px' }}>
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>Export</div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 12px' }}>
          Télécharge toutes tes recettes au format JSON.
        </p>
        <button className="btn-secondary" onClick={handleExportAll}>
          ⬇ Exporter toutes les recettes
        </button>
      </div>

      {/* Import */}
      <div style={{ background: 'var(--bg-secondary)', borderRadius: '12px', padding: '16px' }}>
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>Import</div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 12px' }}>
          Sélectionne un ou plusieurs fichiers <code style={{ color: 'var(--accent)' }}>.json</code>.
          Tu peux aussi en glisser-déposer plusieurs d'un coup.
        </p>

        {/* Zone drag & drop */}
        <div
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed var(--bg-tertiary)',
            borderRadius: '12px',
            padding: '32px 16px',
            textAlign: 'center',
            cursor: 'pointer',
            marginBottom: '12px',
            transition: 'border-color 0.15s',
          }}
          onDragEnter={e => e.currentTarget.style.borderColor = 'var(--accent)'}
          onDragLeave={e => e.currentTarget.style.borderColor = 'var(--bg-tertiary)'}
        >
          <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📂</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {importing ? 'Import en cours...' : 'Clique ou glisse des fichiers .json ici'}
          </div>
        </div>

        {/* Input caché */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          multiple
          style={{ display: 'none' }}
          onChange={handleFileInput}
        />

        {/* Résultats */}
        {importResults.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {importResults.map((r, i) => (
              <div key={i} style={{
                padding: '10px 14px', borderRadius: '8px', fontSize: '0.85rem',
                background: r.ok ? 'rgba(76,175,80,0.15)' : 'rgba(244,67,54,0.15)',
                color: r.ok ? 'var(--success)' : '#f44336',
              }}>
                {r.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
