export default function Hero() {
  const scrollToIntro = () => {
    const el = document.getElementById('intro')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="hero">
      <div className="hero-content">
        <h1 className="hero-headline">
          Ship your vibe-coded agents<br />after they survive.
        </h1>
        <div className="hero-body">
          <p>Production simulation testing for AI agents. Run thousands of scenarios, enforce guardrails at runtime, replay failures deterministically. Score deployment confidence before users ever touch your agent.</p>
          <div className="hero-actions">
            <button className="btn-text-flat" onClick={scrollToIntro}>Explore</button>
          </div>
        </div>
      </div>
      <div className="hero-metric">
        <div className="metric-value">98<sup>%</sup></div>
        <div className="metric-label">Confidence across<br />1,000+ scenarios</div>
      </div>
      <div className="hero-scroll">SCROLL TO EXPLORE</div>
    </section>
  )
}
