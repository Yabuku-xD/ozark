export default function Run() {
  return (
    <section className="s8" data-screen-label="08 Run">
      <div className="s8-rings">
        <svg viewBox="0 0 1440 760" preserveAspectRatio="xMidYMid slice">
          <g fill="none" stroke="oklch(0.965 0.012 85 / 0.06)">
            <ellipse cx="720" cy="900" rx="900" ry="220" />
            <ellipse cx="720" cy="900" rx="700" ry="160" />
            <ellipse cx="720" cy="900" rx="500" ry="110" />
            <ellipse cx="720" cy="900" rx="340" ry="70" />
            <ellipse cx="720" cy="900" rx="200" ry="42" />
          </g>
          <g fill="oklch(0.66 0.155 48 / 0.6)">
            <circle cx="160"  cy="80"  r="2" />
            <circle cx="380"  cy="40"  r="1.5" />
            <circle cx="640"  cy="120" r="1.5" />
            <circle cx="980"  cy="50"  r="2" />
            <circle cx="1280" cy="110" r="1.5" />
            <circle cx="220"  cy="220" r="1" />
            <circle cx="1180" cy="240" r="1" />
          </g>
        </svg>
      </div>

      <div className="s8-content">
        <div className="s8-eye">
          <span className="eyebrow"><span className="pip"/>08 · one command</span>
        </div>
        <h2>./run.sh<span className="cursor" /></h2>
        <div className="sub">Everywhere, Everytime. <br></br> No keys. No cloud. No bills.</div>

        <div className="s8-stats">
          <div className="s">
            <div className="lbl">runtime</div>
            <span className="v lining"><span className="em">0</span>ms</span>
            <div className="ds">cold-start to first scenario</div>
          </div>
          <div className="s">
            <div className="lbl">api keys</div>
            <span className="v lining"><span className="em">0</span></span>
            <div className="ds">required. ever.</div>
          </div>
          <div className="s">
            <div className="lbl">monthly cost</div>
            <span className="v lining"><span className="em">$</span>0.00</span>
            <div className="ds">forever, by design</div>
          </div>
          <div className="s">
            <div className="lbl">platforms</div>
            <span className="v small">macOS · linux</span>
            <div className="ds">SwiftUI runner · python 3.10+</div>
          </div>
        </div>

        <div className="s8-foot">
          <div>OZARK · 2026</div>
          <div>BUILT IN A ROOM · OPEN SOURCE · MIT</div>
          <div className="right">FOR THE AGENTS OF<br />RECORD &amp; RUIN</div>
        </div>
      </div>
    </section>
  )
}
