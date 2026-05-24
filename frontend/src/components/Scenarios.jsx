const scenarios = [
  {
    title: 'Prompt Injection',
    desc: 'System prompt override, role manipulation, hidden instruction attacks',
    tags: ['adversarial', 'critical'],
    gradient: 'linear-gradient(150deg, #1c1917 0%, #292524 100%)',
  },
  {
    title: 'Edge Cases',
    desc: 'Boundary conditions, ambiguous inputs, out-of-distribution queries',
    tags: ['boundary', 'high'],
    gradient: 'linear-gradient(150deg, #1c1917 0%, #1f2937 100%)',
  },
  {
    title: 'Multi-Turn',
    desc: 'Context leakage, role drift, memory corruption across chains',
    tags: ['conversation', 'high'],
    gradient: 'linear-gradient(150deg, #1c1917 0%, #312e81 100%)',
  },
  {
    title: 'Fault Tolerance',
    desc: 'Timeout recovery, tool failure cascades, degraded APIs',
    tags: ['reliability', 'high'],
    gradient: 'linear-gradient(150deg, #1c1917 0%, #365314 100%)',
  },
  {
    title: 'Data Extraction',
    desc: 'PII harvesting, schema inference, sensitive file access',
    tags: ['privacy', 'critical'],
    gradient: 'linear-gradient(150deg, #1c1917 0%, #701a75 100%)',
  },
  {
    title: 'Security',
    desc: 'Jailbreak frameworks, G0DM0D3 detection, parameter tests',
    tags: ['security', 'critical'],
    gradient: 'linear-gradient(150deg, #1c1917 0%, #881337 100%)',
  },
]

export default function Scenarios() {
  return (
    <section className="scenarios-section section" id="scenarios">
      <div className="container">
        <div className="section-header reveal">
          <p className="section-label">Scenario Library</p>
          <h2 className="section-title">50,000+ scenarios across six families</h2>
          <p className="section-desc">
            Ozark composes scenarios from generative families, each branching into hundreds of distinct variations for comprehensive coverage.
          </p>
        </div>

        <div className="scenarios-grid stagger reveal">
          <div className="scenario-tile large" style={{ background: 'linear-gradient(135deg, rgba(5,150,105,0.12), rgba(5,150,105,0.04))' }}>
            <div className="scenario-tile-overlay" style={{ background: 'linear-gradient(to top, rgba(28,25,23,0.85) 0%, rgba(28,25,23,0.2) 60%, transparent 100%)' }} />
            <div className="scenario-tile-content">
              <div className="scenario-tile-count">50K+</div>
              <div style={{ fontSize: '15px', color: 'var(--stone-300)' }}>total scenarios</div>
              <div className="scenario-tile-tags">
                <span className="badge badge-emerald">adversarial</span>
                <span className="badge badge-stone">edge</span>
                <span className="badge badge-stone">multi-turn</span>
                <span className="badge badge-stone">fault</span>
                <span className="badge badge-stone">security</span>
                <span className="badge badge-stone">happy-path</span>
              </div>
            </div>
          </div>

          {scenarios.map((s, i) => (
            <div key={i} className="scenario-tile" style={{ background: s.gradient }}>
              <div className="scenario-tile-overlay" />
              <div className="scenario-tile-content">
                <div className="scenario-tile-title">{s.title}</div>
                <div className="scenario-tile-desc">{s.desc}</div>
                <div className="scenario-tile-tags">
                  {s.tags.map((t, j) => (
                    <span key={j} className={`badge ${t === 'critical' ? 'badge-fail' : t === 'high' ? 'badge-warn' : 'badge-stone'}`}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
