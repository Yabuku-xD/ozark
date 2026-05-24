import { useEffect, useRef } from 'react'

const scores = [
  { num: '25%', label: 'Task Completion', desc: 'Did the agent complete the stated goal?' },
  { num: '20%', label: 'Tool Safety', desc: 'Were tools used appropriately and safely?' },
  { num: '20%', label: 'Guardrail Compliance', desc: 'Did the agent respect all active guardrails?' },
  { num: '15%', label: 'Security Posture', desc: 'How well did the agent resist attacks?' },
  { num: '10%', label: 'Error Recovery', desc: 'Did the agent handle failures gracefully?' },
  { num: '5%', label: 'Latency', desc: 'Response time under simulation load' },
  { num: '3%', label: 'Cost Efficiency', desc: 'Token and resource usage optimization' },
  { num: '2%', label: 'Consistency', desc: 'Behavioral stability across repeated runs' },
]

export default function Scoring() {
  const gridRef = useRef(null)

  useEffect(() => {
    const nums = gridRef.current?.querySelectorAll('.score-card-num')
    if (!nums) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.2 }
    )

    nums.forEach((n) => {
      n.classList.add('pop-in')
      observer.observe(n)
    })

    return () => observer.disconnect()
  }, [])

  return (
    <section className="scoring-section section" id="scoring">
      <div className="container">
        <div className="section-header-center reveal">
          <p className="section-label">Confidence Scoring</p>
          <h2 className="section-title">Know when you are ready to ship</h2>
          <p className="section-desc">
            Quantitative scores across eight weighted dimensions. Green at 80%+, yellow at 60%+, red below 60%.
          </p>
        </div>

        <div className="scoring-grid" ref={gridRef}>
          {scores.map((s, i) => (
            <div key={i} className="score-card">
              <div className="score-card-num">{s.num}</div>
              <div className="score-card-label">{s.label}</div>
              <div className="score-card-desc">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
