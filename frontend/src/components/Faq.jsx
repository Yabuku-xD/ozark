import { useState } from 'react'

const faqs = [
  {
    q: 'What is Ozark and who is it for?',
    a: 'Ozark is a local-first AI agent simulation lab for engineers building production agents. It generates thousands of testing scenarios, enforces runtime guardrails, and produces a deployment confidence score. No cloud, no API keys, no cost.',
  },
  {
    q: 'Do I need an API key or internet connection?',
    a: 'No. Ozark runs entirely on your machine. Zero API keys, zero cloud dependencies, zero data leaves your computer. Everything is local by default.',
  },
  {
    q: 'How does the confidence scoring work?',
    a: 'Ozark evaluates agents across 8 weighted dimensions: Task Completion (25%), Tool Safety (20%), Guardrail Compliance (20%), Security Posture (15%), Error Recovery (10%), Latency (5%), Cost Efficiency (3%), and Consistency (2%). Results above 80% are green, above 60% yellow, below 60% red.',
  },
  {
    q: 'Can I test my own agent?',
    a: 'Yes. Ozark supports agents running via HTTP endpoint or stdio. Create a JSON config describing your agent tools and guardrails, import it through the SwiftUI runner or API, and start running scenarios immediately.',
  },
  {
    q: 'What scenarios come built-in?',
    a: 'Ozark includes 50,000+ scenarios across six families: adversarial (prompt injection, jailbreaks), edge cases, multi-turn conversations, fault tolerance, data extraction, and security (including G0DM0D3 defense). You can also add custom YAML scenario packs.',
  },
  {
    q: 'How is this different from LangSmith or AgentOps?',
    a: 'Ozark is the only tool that is fully local-first, free, and requires no API keys. LangSmith is a paid SaaS, AgentOps is freemium cloud, and Braintrust charges per usage. Ozark gives you enterprise-grade simulation without vendor lock-in or data leaving your machine.',
  },
]

export default function Faq() {
  const [openIndex, setOpenIndex] = useState(null)

  return (
    <section className="faq-section section" id="faq">
      <div className="container">
        <div className="section-header-center reveal">
          <p className="section-label">FAQ</p>
          <h2 className="section-title">Frequently asked questions</h2>
        </div>

        <div className="faq-list stagger reveal">
          {faqs.map((faq, i) => (
            <div key={i} className={`faq-item${openIndex === i ? ' open' : ''}`}>
              <button
                className="faq-question"
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                aria-expanded={openIndex === i}
              >
                <span>{faq.q}</span>
                <svg className="faq-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>
              <div className="faq-answer">
                <div className="faq-answer-inner">
                  <div className="faq-answer-text">{faq.a}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
