const chips = [
  { id: 'sc.18420', label: 'refund · order#A11',        tag: 'happy' },
  { id: 'sc.18421', label: 'double-charge dispute',      tag: 'edge'  },
  { id: 'sc.18422', label: 'account locked, no email',   tag: 'edge'  },
  { id: 'sc.18423', label: 'system_prompt extraction',   tag: 'adv'   },
  { id: 'sc.18424', label: 'tool retry on 502',          tag: 'fault' },
  { id: 'sc.18425', label: '7‑turn negotiation',         tag: 'multi' },
  { id: 'sc.18426', label: 'PII leak via tool args',     tag: 'adv'   },
  { id: 'sc.18427', label: 'ambiguous date "next fri"',  tag: 'edge'  },
  { id: 'sc.18428', label: 'happy path · password reset',tag: 'happy' },
  { id: 'sc.18429', label: 'network timeout · 3000ms',   tag: 'fault' },
  { id: 'sc.18430', label: 'sql destructive · DROP',     tag: 'adv'   },
]

const doubled = [...chips, ...chips]

export default function Scenarios() {
  return (
    <section className="s2" data-screen-label="02 Scenarios">
      <div className="s2-grid">
        <div className="s2-big">
          <span className="eyebrow"><span className="pip" />02 · the scenario terrain</span>
          <div className="number lining">50,000<span className="plus">+</span></div>
          <span className="underline" />
          <div className="caption">paths generated · <span className="em">happy · edge · adversarial · multi-turn · fault</span></div>
        </div>

        <div className="s2-right">
          <h2>Every world your agent <span className="it">will ever</span> see — already <span className="it">explored.</span></h2>
          <p className="lede">Ozark composes scenario terrain from five generative families. Each family branches into thousands of variations, fed by a Markov behavior model that drifts inputs the way real users do.</p>

          <div className="s2-list">
            <div className="s2-list-row row">
              <span className="ix">FAM·01</span>
              <span className="name"><span className="it">happy</span>paths</span>
              <span className="count">18,420 sc</span>
              <span className="meter" style={{'--w': '92%'}} />
            </div>
            <div className="s2-list-row row">
              <span className="ix">FAM·02</span>
              <span className="name"><span className="it">edge</span>cases</span>
              <span className="count">14,201 sc</span>
              <span className="meter" style={{'--w': '71%'}} />
            </div>
            <div className="s2-list-row row">
              <span className="ix">FAM·03</span>
              <span className="name"><span className="it">adversarial</span></span>
              <span className="count">9,840 sc</span>
              <span className="meter" style={{'--w': '49%'}} />
            </div>
            <div className="s2-list-row row">
              <span className="ix">FAM·04</span>
              <span className="name"><span className="it">multi</span>turn</span>
              <span className="count">6,112 sc</span>
              <span className="meter" style={{'--w': '31%'}} />
            </div>
            <div className="s2-list-row row">
              <span className="ix">FAM·05</span>
              <span className="name"><span className="it">fault</span>injection</span>
              <span className="count">3,388 sc</span>
              <span className="meter" style={{'--w': '18%'}} />
            </div>
          </div>
        </div>
      </div>

      <div className="s2-scroller">
        <div className="s2-track live">
          {doubled.map((chip, i) => (
            <span key={i} className="s2-chip">
              <span className="id">{chip.id}</span>
              {chip.label}
              <span className={`tag ${chip.tag}`}>{chip.tag}</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
