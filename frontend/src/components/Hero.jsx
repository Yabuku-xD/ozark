const metrics = [
  ['50,000+', 'generated scenarios'],
  ['0', 'cloud dependencies'],
  ['8', 'score dimensions'],
]

export default function Hero() {
  return (
    <section className="hero" id="top">
      <div className="hero-gradient" aria-hidden="true" />
      <div className="container hero-grid">
        <div className="hero-copy reveal is-visible">
          <p className="eyebrow">Local-first agent simulation lab</p>
          <h1>Ship AI agents after they survive the lake.</h1>
          <p className="hero-lede">
            Ozark runs your agent through adversarial prompts, multi-turn drift, tool failures, and guardrail probes before users ever touch it. No API keys. No hosted traces. No vendor lock-in.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#engine">Understand the engine</a>
            <a className="button button-secondary" href="https://github.com/Yabuku-xD/ozark" target="_blank" rel="noreferrer">View source</a>
          </div>
          <div className="hero-metrics" aria-label="Ozark product metrics">
            {metrics.map(([value, label]) => (
              <div key={label}>
                <strong className="t-digit-group is-animating">
                  {value.split('').map((char, index) => (
                    <span
                      key={`${value}-${index}`}
                      className="t-digit"
                      data-stagger={index >= value.length - 2 ? String(index - value.length + 3) : undefined}
                    >
                      {char}
                    </span>
                  ))}
                </strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="hero-lab reveal is-visible" aria-label="Ozark run summary preview">
          <div className="lab-header">
            <span>ozark / simulation</span>
            <span>local</span>
          </div>
          <div className="lab-score">
            <span>deployment confidence</span>
            <strong className="t-digit-group is-animating">
              {'87.4%'.split('').map((char, index) => (
                <span
                  key={`${char}-${index}`}
                  className="t-digit"
                  data-stagger={index >= 3 ? String(index - 2) : undefined}
                >
                  {char}
                </span>
              ))}
            </strong>
          </div>
          <div className="lab-bars">
            {[
              ['Task completion', '92%', 92],
              ['Tool safety', '88%', 88],
              ['Guardrails', '84%', 84],
              ['Security posture', '79%', 79],
            ].map(([label, value, width]) => (
              <div className="lab-bar" key={label}>
                <div><span>{label}</span><span>{value}</span></div>
                <i style={{ width: `${width}%` }} />
              </div>
            ))}
          </div>
          <div className="lab-events">
            <p><span className="event-ok" />42 passed scenarios</p>
            <p><span className="event-warn" />5 warnings need review</p>
            <p><span className="event-block" />3 blocked guardrail violations</p>
          </div>
        </div>
      </div>
    </section>
  )
}
