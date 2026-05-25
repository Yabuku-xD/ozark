const features = [
  {
    title: 'Scenario generation',
    body: 'Create thousands of adversarial, boundary, happy-path, multi-turn, and fault-injection cases from a compact agent profile.',
    proof: '50,000+ permutations',
  },
  {
    title: 'Runtime guardrails',
    body: 'Detect prompt injection, toxicity, PII exposure, dangerous code, jailbreak frameworks, and sensitive file access while the run is happening.',
    proof: 'block / warn / pass',
  },
  {
    title: 'Live agent testing',
    body: 'Connect to running agents over HTTP or stdio. Test the thing you will deploy, not a mock that behaves nicely.',
    proof: 'HTTP + stdio',
  },
  {
    title: 'Coverage analysis',
    body: 'See which tools, turns, paths, and policy branches were exercised before you trust a release.',
    proof: 'path-level evidence',
  },
  {
    title: 'CI-ready output',
    body: 'Fail pull requests when confidence drops below your threshold and keep local traces out of third-party systems.',
    proof: 'green ≥80%',
  },
  {
    title: 'Zero-cost operation',
    body: 'Runs locally without paid SaaS, external APIs, or hosted observability. Useful for security-sensitive teams and solo builders.',
    proof: 'no API keys',
  },
]

export default function Features() {
  return (
    <section className="section" id="features">
      <div className="container">
        <div className="section-header reveal">
          <p className="eyebrow">Capabilities</p>
          <h2>Everything needed to decide if an agent is ready.</h2>
          <p>Ozark keeps the workflow compact: generate hard scenarios, execute locally, enforce guardrails, and score the release.</p>
        </div>

        <div className="feature-grid">
          {features.map((feature) => (
            <article className="feature-card reveal" key={feature.title}>
              <div className="feature-proof">{feature.proof}</div>
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
