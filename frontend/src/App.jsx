import { useEffect } from 'react'
import Hero from './components/Hero'
import Scenarios from './components/Scenarios'
import Terminal from './components/Terminal'
import Guardrails from './components/Guardrails'
import Scoring from './components/Scoring'
import Coverage from './components/Coverage'
import Godmode from './components/Godmode'
import Run from './components/Run'

export default function App() {
  useEffect(() => {
    const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    const cleanups = []

    if (!reducedMotion) {
      const groups = [
        { sel: '.s1-content',   items: '> *' },
        { sel: '.s1-radar',     items: null },
        { sel: '.s2-grid',      items: '> *' },
        { sel: '.s2-list',      items: '> .row' },
        { sel: '.s2-scroller',  items: null },
        { sel: '.s3-frame',     items: null },
        { sel: '.s4-header',    items: '> *' },
        { sel: '.s4-bento',     items: '> .s4-cell' },
        { sel: '.s5-grid',      items: '> *' },
        { sel: '.s5-legend',    items: '> .row' },
        { sel: '.s6-head',      items: '> *' },
        { sel: '.s6-heat-wrap', items: '> *' },
        { sel: '.s7-head',      items: '> *' },
        { sel: '.s7-intercept', items: null },
        { sel: '.s7-defenses',  items: '> .s7-def' },
        { sel: '.s8-content',   items: '> *' },
      ]
      groups.forEach(({ sel, items }) => {
        const parent = document.querySelector(sel)
        if (!parent) return
        if (items === null) {
          parent.classList.add('reveal')
        } else {
          parent.classList.add('stagger')
          parent.querySelectorAll(':scope ' + items).forEach(el => el.classList.add('reveal'))
        }
      })

      const io = new IntersectionObserver((entries) => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            e.target.classList.add('is-visible')
            io.unobserve(e.target)
          }
        })
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' })

      document.querySelectorAll('.reveal, .stagger').forEach(el => io.observe(el))
      cleanups.push(() => io.disconnect())

      const topo = document.querySelector('.s1-topo')
      if (topo) {
        let raf = null
        const onScroll = () => {
          if (raf) return
          raf = requestAnimationFrame(() => {
            const y = Math.min(window.scrollY, 900)
            topo.style.transform = `translate3d(0, ${y * 0.18}px, 0)`
            raf = null
          })
        }
        window.addEventListener('scroll', onScroll, { passive: true })
        cleanups.push(() => window.removeEventListener('scroll', onScroll))
      }

      const radar = document.querySelector('.s1-radar')
      const s1el = document.querySelector('.s1')
      if (radar && s1el) {
        radar.style.transition = 'transform 600ms cubic-bezier(0.32, 0.72, 0, 1)'
        const onMove = (e) => {
          const r = radar.getBoundingClientRect()
          const cx = r.left + r.width / 2
          const cy = r.top + r.height / 2
          radar.style.transform = `translate3d(${(e.clientX - cx) / 80}px, ${(e.clientY - cy) / 80}px, 0)`
        }
        const onLeave = () => { radar.style.transform = 'translate3d(0, 0, 0)' }
        s1el.addEventListener('mousemove', onMove)
        s1el.addEventListener('mouseleave', onLeave)
        cleanups.push(() => {
          s1el.removeEventListener('mousemove', onMove)
          s1el.removeEventListener('mouseleave', onLeave)
        })
      }
    }

    return () => cleanups.forEach(fn => fn())
  }, [])

  return (
    <>
      <Hero />
      <Scenarios />
      <Terminal />
      <Guardrails />
      <Scoring />
      <Coverage />
      <Godmode />
      <Run />
    </>
  )
}
