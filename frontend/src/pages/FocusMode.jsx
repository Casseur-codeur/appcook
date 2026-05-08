import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { getRecipe, logCook } from '../api/client'
import StepCard from '../components/StepCard'
import Timer from '../components/Timer'
import ProgressBar from '../components/ProgressBar'

export default function FocusMode() {
  const { code } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const persons = location.state?.persons || 1

  const [recipe, setRecipe] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getRecipe(code).then(r => { setRecipe(r); setLoading(false) })
  }, [code])

  const handleNext = () => {
    if (currentStep < recipe.steps.length - 1) {
      setCurrentStep(s => s + 1)
    } else {
      handleComplete()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) setCurrentStep(s => s - 1)
  }

  const handleComplete = async () => {
    await logCook(code).catch(() => {})  // Enregistrement silencieux
    setDone(true)
  }

  if (loading) return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
      Chargement...
    </div>
  )

  const steps = recipe.steps
  const step = steps[currentStep]

  // Écran de complétion
  if (done) {
    return (
      <div style={{
        height: '100vh', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '32px', textAlign: 'center',
        background: 'var(--bg-primary)',
      }}>
        <div style={{ fontSize: '5rem', marginBottom: '16px' }}>✅</div>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--success)', marginBottom: '8px' }}>
          Bien joué !
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginBottom: '32px' }}>
          {recipe.name} — c'est prêt 🎉
        </p>
        <button
          className="btn-primary"
          onClick={() => navigate('/recipes')}
        >
          Retour aux recettes
        </button>
        <button
          className="btn-secondary"
          style={{ marginTop: '12px' }}
          onClick={() => navigate('/')}
        >
          Accueil
        </button>
      </div>
    )
  }

  return (
    <div style={{
      height: '100vh', display: 'flex', flexDirection: 'column',
      background: 'var(--bg-primary)', overflow: 'hidden',
    }}>

      {/* Header : nom + quitter */}
      <div style={{
        padding: '12px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'var(--bg-secondary)',
        flexShrink: 0,
      }}>
        <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-muted)' }}>
          {recipe.name}
        </span>
        <button
          onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.85rem' }}
        >
          Quitter
        </button>
      </div>

      {/* Barre de progression */}
      <ProgressBar
        current={currentStep + 1}
        total={steps.length}
        label={`Étape ${currentStep + 1} sur ${steps.length}`}
      />

      {/* Contenu de l'étape (scrollable) */}
      <div style={{ flex: 1, overflowY: 'auto', paddingBottom: '8px' }}>
        <StepCard
          step={step}
          nextStep={currentStep < steps.length - 1 ? steps[currentStep + 1] : null}
          total={steps.length}
        />

        {/* Timer */}
        <div style={{ padding: '0 16px' }}>
          <Timer timeMin={step.time_min} />
        </div>
      </div>

      {/* Boutons navigation */}
      <div style={{
        padding: '12px 16px 24px',
        display: 'flex', gap: '12px',
        flexShrink: 0,
        background: 'var(--bg-primary)',
        borderTop: '1px solid var(--bg-tertiary)',
      }}>
        <button
          className="btn-secondary"
          style={{ flex: 1 }}
          onClick={handlePrev}
          disabled={currentStep === 0}
        >
          ← Précédente
        </button>
        <button
          className="btn-primary"
          style={{ flex: 2 }}
          onClick={handleNext}
        >
          {currentStep === steps.length - 1 ? '✅ Terminé !' : 'Suivante →'}
        </button>
      </div>

    </div>
  )
}
