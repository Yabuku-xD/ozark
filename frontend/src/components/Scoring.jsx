export default function Scoring() {
  return (
    <section className="s5" data-screen-label="05 Scoring">
      <div className="s5-rule" />
      <div className="s5-grid">
        <div className="s5-left">
          <span className="eyebrow"><span className="pip" />05 · deployment confidence</span>
          <h2>Eight dimensions of <span className="it">trust</span>.</h2>
          <p>Every run resolves into a single weighted score across eight orthogonal dimensions — what the agent did, how safely it did it, how it recovered, and what it cost. A score is a flag, not a verdict.</p>
          <div className="s5-thresholds">
            <div className="th green">
              <div className="label">≥ 80</div>
              <span className="num lining">ready</span>
            </div>
            <div className="th amber">
              <div className="label">≥ 60</div>
              <span className="num lining">review</span>
            </div>
            <div className="th red">
              <div className="label">&lt; 60</div>
              <span className="num lining">blocked</span>
            </div>
          </div>
        </div>

        <div className="s5-chart-col">
          <div className="s5-chart">
            <svg viewBox="-310 -310 620 620">
              <g fill="none" stroke="oklch(0.965 0.012 85 / 0.08)">
                <circle r="280" />
                <circle r="220" />
                <circle r="160" />
                <circle r="100" />
              </g>
              <g fill="none" strokeWidth="44">
                <path d="M 0 -240 A 240 240 0 0 1 240 0"           stroke="oklch(0.66 0.155 48)" />
                <path d="M 240 0 A 240 240 0 0 1 168.6 168.6"      stroke="oklch(0.58 0.14 50)" />
                <path d="M 168.6 168.6 A 240 240 0 0 1 -7 240"     stroke="oklch(0.46 0.12 52)" />
                <path d="M -7 240 A 240 240 0 0 1 -177 162"        stroke="oklch(0.82 0.135 78)" />
                <path d="M -177 162 A 240 240 0 0 1 -237 -36"      stroke="oklch(0.72 0.10 78)" />
                <path d="M -237 -36 A 240 240 0 0 1 -210 -114"     stroke="oklch(0.78 0.10 220)" />
                <path d="M -210 -114 A 240 240 0 0 1 -176 -162"    stroke="oklch(0.66 0.09 220)" />
                <path d="M -176 -162 A 240 240 0 0 1 -114 -210"    stroke="oklch(0.55 0.08 220)" />
              </g>
              <g stroke="oklch(0.965 0.012 85 / 0.12)" strokeWidth="1">
                <line x1="0" y1="-285" x2="0" y2="-265" />
                <line x1="285" y1="0"   x2="265" y2="0" />
                <line x1="0" y1="285"  x2="0" y2="265" />
                <line x1="-285" y1="0" x2="-265" y2="0" />
              </g>
              <circle r="280" fill="none" stroke="oklch(0.66 0.155 48 / 0.4)" strokeDasharray="2 6" />
            </svg>
            <div className="s5-center">
              <div>
                <div className="pct lining">87.4<span className="sm">%</span></div>
                <div className="label">run · 3f9c1e · ready</div>
              </div>
            </div>
          </div>
        </div>

        <div className="s5-legend">
          <div className="row"><span className="sw" style={{background:'oklch(0.66 0.155 48)'}} /><span><span className="nm">Task Completion</span><span className="sub">·01 / primary</span></span><span className="w">25%</span></div>
          <div className="row"><span className="sw" style={{background:'oklch(0.58 0.14 50)'}} /><span><span className="nm">Tool Safety</span><span className="sub">·02 / secondary</span></span><span className="w">20%</span></div>
          <div className="row"><span className="sw" style={{background:'oklch(0.46 0.12 52)'}} /><span><span className="nm">Guardrail Compliance</span><span className="sub">·03 / secondary</span></span><span className="w">20%</span></div>
          <div className="row"><span className="sw" style={{background:'oklch(0.82 0.135 78)'}} /><span><span className="nm">Security Posture</span><span className="sub">·04 / tertiary</span></span><span className="w">15%</span></div>
          <div className="row"><span className="sw" style={{background:'oklch(0.72 0.10 78)'}} /><span><span className="nm">Error Recovery</span><span className="sub">·05 / tertiary</span></span><span className="w">10%</span></div>
          <div className="row"><span className="sw" style={{background:'oklch(0.78 0.10 220)'}} /><span><span className="nm">Latency Performance</span><span className="sub">·06 / minor</span></span><span className="w">5%</span></div>
          <div className="row"><span className="sw" style={{background:'oklch(0.66 0.09 220)'}} /><span><span className="nm">Cost Efficiency</span><span className="sub">·07 / minor</span></span><span className="w">3%</span></div>
          <div className="row"><span className="sw" style={{background:'oklch(0.55 0.08 220)'}} /><span><span className="nm">Behavioral Consistency</span><span className="sub">·08 / minor</span></span><span className="w">2%</span></div>
        </div>
      </div>
    </section>
  )
}
