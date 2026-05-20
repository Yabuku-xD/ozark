const SCENARIOS = [
  { name: 'Happy path', desc: 'Standard user flow — everything works as expected', cls: 'happy' },
  { name: 'Edge case', desc: 'Unexpected inputs, nulls, empty strings, boundary values', cls: 'edge' },
  { name: 'Error recovery', desc: 'Fault injection — timeouts, auth errors, rate limits, data corruption', cls: 'error' },
  { name: 'Security probe', desc: 'Prompt injection, jailbreak attempts, PII leakage, and data exfiltration', cls: 'security' },
  { name: 'Adversarial', desc: 'Actively hostile inputs designed to break agent constraints', cls: 'adversarial' },
  { name: 'Multi-turn', desc: 'Long conversations with context drift, topic shifts, and memory pressure', cls: 'multi' },
  { name: 'Compliance', desc: 'Regulatory checks — GDPR data handling, SOX audit trails, HIPAA safeguards', cls: 'compliance' },
]

export default function Scenarios() {
  return (
    <section className="section" id="scenarios">
      <div className="section-label rotated">SCENARIOS</div>
      <div className="section-content split reverse">
        <div className="split-left">
          <div className="scenario-list">
            {SCENARIOS.map((s) => (
              <div className="scenario-item" key={s.name}>
                <div className={`scenario-dot ${s.cls}`} />
                <strong>{s.name}</strong>
                <span>{s.desc}</span>
              </div>
            ))}
          </div>
          <div className="scenario-total">1,000+ scenarios auto-generated per agent configuration</div>
        </div>
        <div className="split-right">
          <h2>Every scenario<br />type. Every edge<br />case. No blind<br />spots.</h2>
          <p>Seven scenario families cover the full failure surface. From routine paths to adversarial attacks, Ozark auto-generates the test matrix so you don&apos;t have to guess what might break.</p>
          <div className="scenario-stats">
            <div className="stat">
              <div className="stat-value">7</div>
              <div className="stat-label">Scenario types</div>
            </div>
            <div className="stat">
              <div className="stat-value">1,000+</div>
              <div className="stat-label">Per agent config</div>
            </div>
            <div className="stat">
              <div className="stat-value">&lt;5s</div>
              <div className="stat-label">Generation time</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
