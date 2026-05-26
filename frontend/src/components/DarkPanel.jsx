const steps = [
  ['Generate', 'Build broad scenario families: happy paths, adversarial probes, edge cases, multi-turn drift, and fault injection.'],
  ['Execute', 'Run scenarios against a live agent through HTTP or stdio using the same tools and policies it will use in production.'],
  ['Evaluate', 'Apply configured scorers for regex checks, blocked tool paths, latency budgets, and rubric-compatible judgments.'],
  ['Triage', 'Group failed findings into issues, annotate human decisions, and promote failures into regression datasets.'],
]

export default function DarkPanel() {
  return (
    <section className="engine-panel section" id="engine">
      <div className="container engine-grid">
        <div className="engine-copy reveal">
          <p className="eyebrow light">Execution engine</p>
          <h2>Not another trace viewer. A local lab that breaks agents on purpose.</h2>
          <p>
            Ozark combines a policy engine, Markov behavior model, coverage analyzer, evaluator runner, issue grouper, and live connector so evaluation happens against actual agent behavior instead of static examples.
          </p>
        </div>
        <div className="engine-steps reveal">
          {steps.map(([title, body], index) => (
            <article key={title}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <h3>{title}</h3>
              <p>{body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
