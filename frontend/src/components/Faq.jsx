import { useState } from 'react'

const faqs = [
  ['Does Ozark require API keys?', 'No. Ozark is local-first and can run without external model APIs, hosted tracing, or paid evaluation services.'],
  ['How does it connect to my agent?', 'Use HTTP for a running service or stdio for command-style agents. Ozark sends scenarios and records the real execution path.'],
  ['What do the colors mean?', 'Green at 80% or higher is ready, yellow at 60% or higher needs review, and red below 60% is blocked.'],
  ['Is it only observability?', 'No. Ozark generates scenarios, executes them, enforces guardrails, analyzes coverage, and produces a deployment confidence score.'],
]

export default function Faq() {
  const [open, setOpen] = useState(0)

  return (
    <section className="section faq-section" id="faq">
      <div className="container faq-grid">
        <div className="section-header reveal">
          <p className="eyebrow">FAQ</p>
          <h2>Designed for local confidence, not cloud dependency.</h2>
        </div>
        <div className="faq-list reveal">
          {faqs.map(([question, answer], index) => (
            <article className={open === index ? 'is-open' : ''} key={question}>
              <button type="button" onClick={() => setOpen(open === index ? -1 : index)} aria-expanded={open === index}>
                {question}
                <span>{open === index ? '−' : '+'}</span>
              </button>
              <div className="faq-panel t-panel-slide" data-open={open === index}>
                <p>{answer}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
