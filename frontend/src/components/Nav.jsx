import { useEffect, useState } from 'react'

const NAV_ITEMS = ['INTRO', 'AGENTS', 'SCENARIOS', 'SCORING']

export default function Nav() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const scrollTo = (id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <nav className={`nav ${scrolled ? 'scrolled' : ''}`}>
      <div className="nav-left">
        <span className="nav-wordmark">OZARK</span>
      </div>
      <div className="nav-right">
        {NAV_ITEMS.map((item) => (
          <button
            key={item}
            className="nav-item"
            onClick={() => scrollTo(item.toLowerCase())}
          >
            {item}
          </button>
        ))}
      </div>
    </nav>
  )
}
