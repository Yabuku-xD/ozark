const lanes = [
  {
    label: 'Datasets',
    value: 'trace → eval',
    detail: 'Promote failed runs into regression suites with stable scenario IDs, tags, source run links, and replayable prompts.',
  },
  {
    label: 'Evaluators',
    value: 'custom scorers',
    detail: 'Register deterministic regex, tool-sequence, latency, and rubric-compatible evaluators without changing run code.',
  },
  {
    label: 'Issues',
    value: 'grouped failures',
    detail: 'Collapse repeated evaluator failures into issue signatures with severity, status, occurrence count, and last-seen run.',
  },
  {
    label: 'Annotations',
    value: 'human signal',
    detail: 'Attach labels, scores, and reviewer comments to runs, issues, or dataset items for judge calibration later.',
  },
]

const issues = [
  ['critical', 'blocked tool called: process_payment', '3 runs', 'open'],
  ['high', 'regex expectation failed', '7 traces', 'triage'],
  ['medium', 'latency 39218ms > 30000ms', '2 runs', 'open'],
]

const apiCalls = [
  ['POST', '/api/datasets/from-run', 'turn failures into regression data'],
  ['POST', '/api/runs/:id/evaluate', 'run configured evaluators'],
  ['GET', '/api/issues?status=open', 'review grouped failures'],
  ['POST', '/api/annotations', 'capture human judgment'],
]

export default function WorkflowDashboard() {
  return (
    <section className="section workflow-section" id="workflow">
      <div className="container">
        <div className="section-header reveal">
          <p className="eyebrow">Reliability workflow</p>
          <h2>The production loop missing from most local eval tools.</h2>
          <p>
            Ozark now connects traces, regression datasets, configurable evaluators, grouped issues, and human review into one local-first workflow.
          </p>
        </div>

        <div className="workflow-grid">
          <div className="workflow-lanes reveal" aria-label="Ozark reliability workflow capabilities">
            {lanes.map((lane, index) => (
              <article key={lane.label}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <div>
                  <h3>{lane.label}</h3>
                  <strong>{lane.value}</strong>
                  <p>{lane.detail}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="issue-board reveal" aria-label="Issue lifecycle preview">
            <div className="issue-board-top">
              <span>issues / grouped by signature</span>
              <b>local</b>
            </div>
            {issues.map(([severity, title, count, status]) => (
              <article className={`issue-row issue-${severity}`} key={title}>
                <span>{severity}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{count} · {status}</p>
                </div>
              </article>
            ))}
            <div className="annotation-card">
              <span>human annotation</span>
              <p>valid_failure · score 1.0 · “Reproduced locally; add to release gate.”</p>
            </div>
          </div>
        </div>

        <div className="api-strip reveal" aria-label="Workflow API examples">
          {apiCalls.map(([method, path, detail]) => (
            <article key={path}>
              <code>{method}</code>
              <strong>{path}</strong>
              <span>{detail}</span>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
