const STEPS = [
  {
    number: '01',
    title: 'Configure your agent',
    body: 'Define tools, guardrails, and system prompts. Ozark ingests LangChain, CrewAI, AutoGen, and OpenAI SDK configs.',
  },
  {
    number: '02',
    title: 'Generate scenarios',
    body: 'Auto-generate 1,000+ scenarios across 7 types — happy paths, edge cases, adversarials, compliance checks, multi-turn conversations, and fault injections.',
  },
  {
    number: '03',
    title: 'Score and ship',
    body: 'Get an 8-dimension confidence score. Replay failures deterministically. Diff runs to catch regressions. Gate deployments on confidence thresholds.',
  },
]

export default function Intro() {
  return (
    <section className="section" id="intro">
      <div className="section-label rotated">HOW IT WORKS</div>
      <div className="section-content split">
        <div className="split-left">
          <h2>From config to<br />confidence in<br />three steps.</h2>
        </div>
        <div className="split-right">
          <div className="step-list">
            {STEPS.map((step) => (
              <div className="step" key={step.number}>
                <div className="step-number">{step.number}</div>
                <div className="step-body">
                  <h3>{step.title}</h3>
                  <p>{step.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
