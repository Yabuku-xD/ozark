import { useState } from 'react'

const links = [
  { id: 'features', label: 'Capabilities' },
  { id: 'scenarios', label: 'Scenarios' },
  { id: 'scoring', label: 'Scoring' },
  { id: 'faq', label: 'FAQ' },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="navbar" aria-label="Primary">
      <div className="nav-pill-wrap">
        <div className={`nav-pill${open ? ' is-open' : ''}`}>
          {links.map((l) => (
            <a key={l.id} href={`#${l.id}`} className="nav-pill-link" onClick={() => setOpen(false)}>
              {l.label}
            </a>
          ))}
        </div>

        <button
          className="navbar-toggle"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-label={open ? 'Close menu' : 'Open menu'}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            {open ? (
              <><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></>
            ) : (
              <><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" /></>
            )}
          </svg>
        </button>
      </div>
    </nav>
  )
}
