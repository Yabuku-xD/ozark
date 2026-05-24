const features = [
  {
    label: 'Scenario Generation',
    title: 'Generate thousands of scenarios in seconds',
    desc: 'Auto-generate adversarial, edge-case, happy-path, multi-turn, and fault-injection scenarios from five distinct families.',
    items: [
      'Prompt injection and jailbreak detection',
      'PII extraction and data leakage tests',
      'Multi-turn conversation corruption',
      'Fault tolerance and timeout recovery',
    ],
    visual: 'code',
  },
  {
    label: 'Guardrail Enforcement',
    title: 'Runtime guardrails that block threats',
    desc: 'Pre-built and custom guardrails for prompt injection, toxicity, PII, dangerous code, and more.',
    items: [
      'Content safety: toxic output, dangerous code',
      'Security: sensitive file access, exfiltration',
      'G0DM0D3 jailbreak framework detection',
      'Parameter boundary violation alerts',
    ],
    visual: 'guardrails',
  },
  {
    label: 'Confidence Scoring',
    title: '8-dimensional confidence scoring',
    desc: 'Know when you are ready to ship with quantitative scores across every critical dimension.',
    items: [
      'Task completion (25%) and tool safety (20%)',
      'Guardrail compliance (20%) and security (15%)',
      'Error recovery (10%) and latency (5%)',
      'Cost efficiency (3%) and consistency (2%)',
    ],
    visual: 'metrics',
  },
]

export default function Features() {
  return (
    <section className="features-section section" id="features">
      <div className="container">
        <div className="section-header reveal">
          <p className="section-label">Capabilities</p>
          <h2 className="section-title">Everything you need to ship confident agents</h2>
          <p className="section-desc">
            Scenario generation, guardrail enforcement, confidence scoring, and live tracing. All local-first.
          </p>
        </div>

        {features.map((f, i) => (
          <div key={i} className={`feature-row${i % 2 === 1 ? ' reverse' : ''} reveal`}>
            <div className="feature-text">
              <p className="section-label">{f.label}</p>
              <h3 className="section-title">{f.title}</h3>
              <p className="section-desc">{f.desc}</p>
              <div className="feature-list">
                {f.items.map((item, j) => (
                  <div key={j} className="feature-list-item">
                    <span className="check" aria-hidden="true">&#10003;</span>
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="feature-visual">
              {f.visual === 'code' && (
                <div className="feature-card-visual">
                  <div className="feature-code-block">
                    <span className="code-comment"># Generate scenarios for any agent type</span>{'\n'}
                    <span className="code-kw">curl</span> -s -X POST http://localhost:8787/api/scenarios/generate \<br />
                    {'  '}-H <span className="code-str">'Content-Type: application/json'</span> \<br />
                    {'  '}-d <span className="code-str">{'{"agent_type":"customer_support","count":100}'}</span>{'\n\n'}
                    <span className="code-comment"># 100 scenarios generated in 0.4s</span>{'\n'}
                    <span className="code-kw">{'{'}</span>{'\n'}
                    {'  '}<span className="code-str">"generated"</span>: <span className="code-num">100</span>,{'\n'}
                    {'  '}<span className="code-str">"families"</span>: [<span className="code-str">"adversarial"</span>, <span className="code-str">"edge"</span>, <span className="code-str">"happy"</span>],{'\n'}
                    {'  '}<span className="code-str">"coverage"</span>: <span className="code-num">78</span>%{'\n'}
                    <span className="code-kw">{'}'}</span>
                  </div>
                </div>
              )}
              {f.visual === 'guardrails' && (
                <div className="feature-card-visual">
                  <div className="feature-guardrail-grid">
                    <span className="guardrail-tag"><span className="sev critical" />prompt-injection</span>
                    <span className="guardrail-tag"><span className="sev high" />pii-leak</span>
                    <span className="guardrail-tag"><span className="sev high" />toxicity</span>
                    <span className="guardrail-tag"><span className="sev warn" />dangerous-code</span>
                    <span className="guardrail-tag"><span className="sev critical" />jailbreak</span>
                    <span className="guardrail-tag"><span className="sev high" />file-access</span>
                    <span className="guardrail-tag"><span className="sev warn" />exfiltration</span>
                    <span className="guardrail-tag"><span className="sev critical" />g0dm0d3</span>
                  </div>
                </div>
              )}
              {f.visual === 'metrics' && (
                <div className="feature-card-visual">
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div style={{ textAlign: 'center', padding: '16px', background: 'var(--cream)', borderRadius: '10px' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color: 'var(--ink)', fontVariantNumeric: 'tabular-nums' }}>87.4%</div>
                      <div style={{ fontSize: '12px', color: 'var(--brown-light)', marginTop: '4px' }}>Confidence</div>
                    </div>
                    <div style={{ textAlign: 'center', padding: '16px', background: 'var(--cream)', borderRadius: '10px' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color: 'var(--pass)', fontVariantNumeric: 'tabular-nums' }}>42/50</div>
                      <div style={{ fontSize: '12px', color: 'var(--brown-light)', marginTop: '4px' }}>Passed</div>
                    </div>
                    <div style={{ textAlign: 'center', padding: '16px', background: 'var(--cream)', borderRadius: '10px' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color: 'var(--warn)', fontVariantNumeric: 'tabular-nums' }}>5</div>
                      <div style={{ fontSize: '12px', color: 'var(--brown-light)', marginTop: '4px' }}>Warned</div>
                    </div>
                    <div style={{ textAlign: 'center', padding: '16px', background: 'var(--cream)', borderRadius: '10px' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color: 'var(--fail)', fontVariantNumeric: 'tabular-nums' }}>3</div>
                      <div style={{ fontSize: '12px', color: 'var(--brown-light)', marginTop: '4px' }}>Blocked</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
