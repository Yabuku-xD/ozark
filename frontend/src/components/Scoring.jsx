const dimensions = [
  ['Task completion', '25%', 92],
  ['Tool safety', '20%', 88],
  ['Guardrail compliance', '20%', 84],
  ['Security posture', '15%', 79],
  ['Error recovery', '10%', 86],
  ['Latency', '5%', 91],
  ['Cost efficiency', '3%', 100],
  ['Consistency', '2%', 83],
]

export default function Scoring() {
  return (
    <section className="section scoring-section" id="scoring">
      <div className="container scoring-grid">
        <div className="section-header reveal">
          <p className="eyebrow">Confidence scoring</p>
          <h2>One release signal, backed by eight dimensions.</h2>
          <p>Green means ready at 80% or higher. Yellow means review. Red means blocked. Every score stays inspectable down to individual scenarios.</p>
        </div>

        <div className="score-card reveal">
          <div className="score-summary">
            <p className="score-label">deployment confidence</p>
            <div className="score-ring" aria-label="Overall confidence score 87.4 percent">
              <strong>87.4</strong>
              <span>green / ready</span>
            </div>
          </div>
          <div className="score-dimensions">
            {dimensions.map(([name, weight, score]) => (
              <div className="score-row" key={name} style={{ '--score': score }}>
                <div className="score-name"><span>{name}</span><small>{weight}</small></div>
                <div className="score-track" aria-hidden="true"><span /></div>
                <b>{score}</b>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
