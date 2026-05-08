import { useNavigate } from 'react-router-dom'

export default function Home() {
  const navigate = useNavigate()

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      justifyContent: 'center', alignItems: 'center',
      padding: '32px 24px', gap: '20px',
    }}>

      <div style={{ textAlign: 'center', marginBottom: '16px' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🍳</div>
        <h1 style={{ margin: 0, fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          AppCook
        </h1>
        <p style={{ margin: '6px 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Qu'est-ce qu'on fait ?
        </p>
      </div>

      <button
        className="btn-primary"
        style={{ fontSize: '1.1rem', padding: '20px 24px' }}
        onClick={() => navigate('/recipes')}
      >
        🍳 Cuisiner une recette
      </button>

      <button
        className="btn-secondary"
        style={{ fontSize: '1.1rem', padding: '20px 24px' }}
        onClick={() => navigate('/shopping')}
      >
        🛒 Faire les courses
      </button>

    </div>
  )
}
