import { useEffect, useRef, useState } from 'react'

const links = [
  { id: 'engine', label: 'Engine' },
  { id: 'features', label: 'Capabilities' },
  { id: 'scenarios', label: 'Scenarios' },
  { id: 'scoring', label: 'Scoring' },
  { id: 'faq', label: 'FAQ' },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const linksRef = useRef(null)

  useEffect(() => {
    const linksEl = linksRef.current
    if (!linksEl || open) return undefined

    linksEl.classList.add('is-closing')
    const closeMs = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--dropdown-close-dur')) || 150
    const timeout = window.setTimeout(() => linksEl.classList.remove('is-closing'), closeMs)

    return () => window.clearTimeout(timeout)
  }, [open])

  return (
    <nav className="navbar" aria-label="Primary">
      <a href="#top" className="brand-mark" aria-label="Ozark home">
        <img src="/assets/logo.svg" alt="" width="24" height="24" aria-hidden="true" />
        <span>Ozark</span>
      </a>

      <button
        className="nav-toggle"
        type="button"
        aria-expanded={open}
        aria-controls="primary-navigation"
        onClick={() => setOpen((value) => !value)}
      >
        <span>{open ? 'Close' : 'Menu'}</span>
      </button>

      <div
        id="primary-navigation"
        ref={linksRef}
        className={`nav-links${open ? ' is-open' : ''}`}
        data-origin="top-center"
      >
        {links.map((link) => (
          <a key={link.id} href={`#${link.id}`} onClick={() => setOpen(false)}>
            {link.label}
          </a>
        ))}
      </div>
    </nav>
  )
}
