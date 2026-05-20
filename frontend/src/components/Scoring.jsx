const DIMENSIONS = [
  { value: 94, label: 'Safety' },
  { value: 89, label: 'Accuracy' },
  { value: 92, label: 'Latency' },
  { value: 78, label: 'Cost' },
  { value: 85, label: 'Consistency' },
  { value: 91, label: 'Guardrail\nCoverage' },
  { value: 87, label: 'Tool\nCorrectness' },
  { value: 81, label: 'Error\nRecovery' },
]

export default function Scoring() {
  return (
    <section className="section" id="scoring">
      <div className="section-label rotated">SCORING</div>
      <div className="section-content split">
        <div className="split-left">
          <h2>Confidence is<br />measurable.<br />Here&apos;s how<br />we score it.</h2>
          <p>Eight dimensions evaluated across every scenario run. Each dimension gets a percentile score weighted by severity. Gate deployments on thresholds you define.</p>
        </div>
        <div className="split-right">
          <div className="dimension-grid">
            {DIMENSIONS.map((d) => (
              <div className="dim" key={d.label}>
                <div className="dim-value">{d.value}%</div>
                <div className="dim-label">{d.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
