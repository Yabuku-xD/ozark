const items = [
  {
    lead: 'Stop',
    key: 'manual red-teaming',
    desc: 'Automate adversarial scenario generation so you do not have to think like an attacker every time.',
  },
  {
    lead: 'Stop guessing',
    key: 'production readiness',
    desc: 'Confidence scoring tells you exactly where your agent stands before anyone else finds out.',
  },
  {
    lead: 'Eliminate',
    key: 'regression surprises',
    desc: 'Every code change gets re-tested against your full scenario library automatically.',
  },
  {
    lead: 'No more',
    key: 'scattered evaluations',
    desc: 'Guardrails, tracing, scoring, and scenarios — unified in one local-first lab.',
  },
]

export default function DarkPanel() {
  return (
    <section className="section-compact">
      <div className="dark-panel-wrap">
        <div className="dark-panel reveal">
          <div className="dark-panel-grid" />
          <div className="dark-panel-inner">
            <div className="dark-panel-header">
              <p className="section-label">The Problem</p>
              <h2 className="section-title">Find the failures before your users do</h2>
              <p className="section-desc">
                Testing AI agents should not require a PhD in prompt engineering.
                Ozark runs the scenarios, enforces the rules, and tells you where you stand.
              </p>
            </div>
            <div className="dark-panel-items stagger reveal">
              {items.map((item, i) => (
                <div key={i} className="dark-panel-item">
                  <div className="dark-panel-num">{i + 1}</div>
                  <div>
                    <div className="dark-panel-item-title">
                      <span className="muted">{item.lead} </span>
                      <span>{item.key}</span>
                    </div>
                    <div className="dark-panel-item-desc">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
