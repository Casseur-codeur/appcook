/**
 * Chips de filtre horizontaux (scroll horizontal sur mobile).
 * Props :
 *   options  : [{ value, label }]
 *   selected : valeur sélectionnée (ou null)
 *   onChange : (value) => void
 *   multi    : bool — permet plusieurs sélections
 */
export default function FilterChips({ options, selected, onChange, multi = false }) {
  const isSelected = (val) =>
    multi ? (selected || []).includes(val) : selected === val

  const handleClick = (val) => {
    if (multi) {
      const current = selected || []
      onChange(
        current.includes(val) ? current.filter(v => v !== val) : [...current, val]
      )
    } else {
      onChange(isSelected(val) ? null : val)
    }
  }

  return (
    <div style={{
      display: 'flex',
      gap: '8px',
      overflowX: 'auto',
      padding: '0 16px',
      paddingBottom: '4px',
      scrollbarWidth: 'none',
    }}>
      {options.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => handleClick(value)}
          style={{
            flexShrink: 0,
            padding: '6px 14px',
            borderRadius: '20px',
            border: '1.5px solid',
            borderColor: isSelected(value) ? 'var(--accent)' : 'var(--bg-tertiary)',
            background: isSelected(value) ? 'var(--accent)' : 'var(--bg-secondary)',
            color: isSelected(value) ? 'white' : 'var(--text-muted)',
            fontSize: '0.85rem',
            fontWeight: isSelected(value) ? 600 : 400,
            cursor: 'pointer',
            transition: 'all 0.15s',
            whiteSpace: 'nowrap',
          }}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
