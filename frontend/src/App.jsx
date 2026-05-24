import { useEffect } from 'react'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import TrustBar from './components/TrustBar'
import DarkPanel from './components/DarkPanel'
import Features from './components/Features'
import Scenarios from './components/Scenarios'
import Scoring from './components/Scoring'
import Testimonials from './components/Testimonials'
import TerminalTrace from './components/TerminalTrace'
import Faq from './components/Faq'
import Footer from './components/Footer'

export default function App() {
  useEffect(() => {
    const revealEls = document.querySelectorAll('.reveal, .stagger')
    if (revealEls.length === 0) return

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            io.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.06, rootMargin: '0px 0px -10% 0px' }
    )
    revealEls.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])

  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <TrustBar />
        <DarkPanel />
        <Features />
        <Scenarios />
        <Scoring />
        <Testimonials />
        <TerminalTrace />
        <Faq />
      </main>
      <Footer />
    </>
  )
}
