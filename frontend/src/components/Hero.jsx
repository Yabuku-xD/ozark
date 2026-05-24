import { useEffect, useRef } from 'react'

export default function Hero() {
  const barRef = useRef(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.querySelector('.hero-card-bar-fill')?.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.3 }
    )
    if (barRef.current) observer.observe(barRef.current)
    return () => observer.disconnect()
  }, [])

  return (
    <section className="hero" id="index">
      <div className="hero-bg" />
      <div className="container">
        <a href="#" className="hero-brand reveal">
          <img src="/assets/logo.png" alt="" width="28" height="28" aria-hidden="true" />
          <span>ozark</span>
        </a>
        <div className="hero-grid">
          <div>
            <div className="hero-label reveal">
              <span className="dot" aria-hidden="true" />
              Local-first agent simulation
            </div>
            <h1 className="hero-headline reveal">
              Test your AI agents <span className="accent">before production</span>
            </h1>
            <p className="hero-sub reveal">
              The only zero-cost, zero-API-key simulation engine. Run 50,000+ scenarios, enforce guardrails at runtime, and get deployment confidence scores. No cloud required.
            </p>
            <div className="hero-actions reveal">
              <a href="#" className="btn btn-primary">Get Started Free</a>
              <a href="#" className="btn btn-secondary">View on GitHub</a>
            </div>
            <div className="hero-trust reveal">
              <span className="badge badge-cream">Local-first</span>
              <span className="badge badge-cream">Zero config</span>
              <span className="badge badge-cream">Open source</span>
            </div>
          </div>

          <div className="hero-visual reveal" ref={barRef}>
            <div className="hero-card">
              <div className="hero-card-header">
                <span className="badge badge-copper">Live</span>
                <span className="hero-card-status">
                  <span className="status-dot" aria-hidden="true" />
                  runner ready
                </span>
              </div>
              <div className="hero-card-metrics">
                <div className="hero-metric">
                  <div className="val">87.4%</div>
                  <div className="lbl">Confidence</div>
                </div>
                <div className="hero-metric">
                  <div className="val">42/50</div>
                  <div className="lbl">Passed</div>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--brown-light)', marginBottom: '8px' }}>
                <span>Coverage</span>
                <span>78%</span>
              </div>
              <div className="hero-card-bar">
                <div className="hero-card-bar-fill" />
              </div>
              <div className="hero-card-tags">
                <span className="badge badge-pass">pass</span>
                <span className="badge badge-warn">warn</span>
                <span className="badge badge-pass">pass</span>
                <span className="badge badge-fail">block</span>
                <span className="badge badge-pass">pass</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
