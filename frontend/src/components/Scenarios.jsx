const scenarios = [
  ['adv/sys-extract', 'Prompt injection', 'System prompt extraction and role override attempts.', 'critical'],
  ['edge/temporal', 'Ambiguous input', 'Dates, partial intent, malformed parameters, and boundary values.', 'high'],
  ['turn/drift', 'Multi-turn drift', 'Memory contamination, context leakage, and role decay across long sessions.', 'high'],
  ['fault/timeout', 'Tool failure', 'Timeouts, 502 retries, partial responses, and degraded dependencies.', 'medium'],
  ['privacy/pii', 'Data leakage', 'PII harvesting, schema inference, and sensitive file exposure.', 'critical'],
  ['happy/reset', 'Core workflow', 'Baseline task completion for expected user paths.', 'ready'],
]

export default function Scenarios() {
  return (
    <section className="section scenario-section" id="scenarios">
      <div className="container">
        <div className="section-header reveal">
          <p className="eyebrow">Scenario library</p>
          <h2>Six families. Thousands of ways to fail before production.</h2>
          <p>Each scenario keeps readable evidence: category, severity, turn count, tool calls, guardrail result, and final score impact.</p>
        </div>

        <div className="scenario-table reveal">
          {scenarios.map(([id, title, body, severity]) => (
            <article key={id}>
              <code>{id}</code>
              <div>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
              <span className={`severity severity-${severity}`}>{severity}</span>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
