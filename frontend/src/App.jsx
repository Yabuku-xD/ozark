import { useState, useEffect } from 'react'
import Nav from './components/Nav'
import Hero from './components/Hero'
import Intro from './components/Intro'
import Agents from './components/Agents'
import Scenarios from './components/Scenarios'
import Scoring from './components/Scoring'
import Guardrails from './components/Guardrails'
import CTA from './components/CTA'
import Footer from './components/Footer'

export default function App() {
  const [scrollHidden, setScrollHidden] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrollHidden(window.scrollY > 100)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="shell">
      <Nav />
      <Hero />
      <Intro />
      <Agents />
      <Scenarios />
      <Scoring />
      <Guardrails />
      <CTA />
      <Footer />
      <div className={`scroll-prompt ${scrollHidden ? 'hidden' : ''}`}>SCROLL TO EXPLORE</div>
      <div className={`scroll-chevron ${scrollHidden ? 'hidden' : ''}`}>&#x2193;</div>
    </div>
  )
}

