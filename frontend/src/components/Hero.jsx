export default function Hero() {
  return (
    <section className="s1" data-screen-label="01 Hero">
      <div className="s1-topo">
        <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
          <defs>
            <radialGradient id="topo-fade" cx="22%" cy="62%" r="60%">
              <stop offset="0%" stopColor="oklch(0.66 0.155 48 / 0.85)" />
              <stop offset="55%" stopColor="oklch(0.66 0.155 48 / 0.20)" />
              <stop offset="100%" stopColor="oklch(0.66 0.155 48 / 0)" />
            </radialGradient>
            <mask id="topo-mask">
              <rect width="1440" height="900" fill="url(#topo-fade)" />
            </mask>
          </defs>
          <g fill="none" stroke="oklch(0.66 0.155 48)" strokeWidth="0.6" mask="url(#topo-mask)">
            <path d="M 320 560 C 250 480, 220 420, 280 360 S 460 240, 560 280 S 720 380, 700 480 S 580 640, 460 640 S 360 620, 320 560 Z" />
            <path d="M 340 565 C 280 495, 250 440, 300 380 S 470 270, 555 305 S 700 395, 680 480 S 575 625, 470 625 S 375 612, 340 565 Z" />
            <path d="M 360 568 C 305 510, 280 460, 320 405 S 480 305, 550 335 S 680 410, 660 480 S 565 605, 475 605 S 385 595, 360 568 Z" />
            <path d="M 380 565 C 330 520, 308 478, 340 430 S 488 340, 545 360 S 660 425, 645 478 S 555 580, 478 580 S 395 575, 380 565 Z" />
            <path d="M 400 565 C 358 530, 335 495, 360 455 S 495 375, 540 388 S 638 440, 628 478 S 545 558, 480 558 S 412 555, 400 565 Z" />
            <path d="M 422 562 C 388 538, 364 510, 380 478 S 500 410, 538 418 S 615 458, 608 478 S 538 540, 485 540 S 432 540, 422 562 Z" />
            <path d="M 442 555 C 415 540, 395 524, 405 500 S 505 442, 535 448 S 595 472, 590 478 S 535 522, 490 522 S 450 524, 442 555 Z" />
            <path d="M 460 548 C 442 540, 425 532, 430 518 S 510 478, 530 482 S 570 488, 575 488 S 530 506, 495 506 S 470 510, 460 548 Z" />
            <path d="M 880 280 C 820 240, 800 200, 860 170 S 1060 130, 1180 170 S 1320 260, 1290 320 S 1180 400, 1080 380 S 940 340, 880 280 Z" />
            <path d="M 900 275 C 850 245, 830 215, 880 185 S 1060 150, 1175 190 S 1305 270, 1280 320 S 1170 390, 1080 372 S 945 332, 900 275 Z" />
            <path d="M 920 270 C 875 250, 858 225, 900 200 S 1060 170, 1170 205 S 1290 275, 1268 318 S 1162 380, 1082 365 S 952 325, 920 270 Z" />
            <path d="M 940 268 C 900 252, 882 230, 918 215 S 1062 192, 1162 218 S 1272 282, 1254 315 S 1158 372, 1082 358 S 958 322, 940 268 Z" />
            <path d="M 960 265 C 924 255, 908 240, 938 230 S 1062 215, 1152 232 S 1252 285, 1238 312 S 1152 362, 1080 350 S 968 318, 960 265 Z" />
            <path d="M 100 800 C 200 760, 380 740, 540 760 S 880 800, 1080 780 S 1340 760, 1440 760" />
            <path d="M 80 820 C 220 780, 400 762, 560 780 S 900 815, 1100 800 S 1340 785, 1440 785" />
            <path d="M 60 840 C 230 805, 420 790, 580 805 S 920 832, 1110 822 S 1340 810, 1440 810" />
          </g>
          <g fill="none" stroke="oklch(0.965 0.012 85 / 0.18)" strokeWidth="0.5">
            <circle cx="470" cy="498" r="2" fill="oklch(0.66 0.155 48)" />
            <circle cx="1080" cy="280" r="2" fill="oklch(0.66 0.155 48)" />
          </g>
          <g stroke="oklch(0.965 0.012 85 / 0.04)" strokeWidth="1">
            <line x1="0" y1="225" x2="1440" y2="225" />
            <line x1="0" y1="450" x2="1440" y2="450" />
            <line x1="0" y1="675" x2="1440" y2="675" />
            <line x1="360" y1="0" x2="360" y2="900" />
            <line x1="720" y1="0" x2="720" y2="900" />
            <line x1="1080" y1="0" x2="1080" y2="900" />
          </g>
        </svg>
      </div>
      <div className="s1-vignette" />

      <nav className="nav">
        <div className="wordmark">
          <span className="glyph">
            <img src="/assets/favicon.png" alt="Ozark" />
          </span>
          <span>Ozark</span>
        </div>
        <div className="nav-items">
          <a className="is-active">Index</a>
          <a>Scenarios</a>
          <a>Guardrails</a>
          <a>Scoring</a>
          <a>Defense</a>
          <a>Docs</a>
        </div>
        <a className="nav-cta">./run.sh <span className="arr">→</span></a>
      </nav>

      <div className="s1-coords">
        <div>N 38°27′12″ · W 92°51′40″</div>
        <div><span className="c">●</span> ridge.04 / scenario.terrain</div>
      </div>

      <div className="s1-content">
        <div className="s1-eyebrow-row">
          <span className="eyebrow"><span className="pip" />Agent Simulation Lab · Local‑first</span>
          <span className="pill">No API keys · No Cloud · No Telemetry</span>
        </div>

        <div className="s1-headline">
          <h1>
            Map every <span className="it">path</span><br />
            your agent <span className="it">might</span> take.
          </h1>
          <p className="sub">Ozark is the cartographer of agent behavior. Fifty thousand scenarios, eight dimensions of trust, every guardrail enforced at runtime — all on your own machine, before anything ships.</p>
        </div>

        <div className="s1-meta">
          <div className="s1-meta-grid">
            <div>
              Scenarios·indexed
              <span className="v lining">50,000<span className="unit">+</span></span>
            </div>
            <div>
              Score·dims
              <span className="v lining">08</span>
            </div>
            <div>
              Guardrails·active
              <span className="v lining">19</span>
            </div>
            <div>
              Mean·runtime
              <span className="v lining">4.2<span className="unit">s/sc</span></span>
            </div>
          </div>
          <div className="pill"><span style={{color:'var(--rust)'}}>●</span> &nbsp;runner ready &nbsp;·&nbsp; macOS 15.4+</div>
        </div>
      </div>

      <div className="s1-radar">
        <svg viewBox="0 0 320 320">
          <defs>
            <radialGradient id="sweep" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="oklch(0.66 0.155 48 / 0.35)" />
              <stop offset="60%" stopColor="oklch(0.66 0.155 48 / 0)" />
            </radialGradient>
          </defs>
          <g fill="none" stroke="oklch(0.965 0.012 85 / 0.12)">
            <circle cx="160" cy="160" r="148" />
            <circle cx="160" cy="160" r="112" />
            <circle cx="160" cy="160" r="76" />
            <circle cx="160" cy="160" r="40" />
            <line x1="12" y1="160" x2="308" y2="160" />
            <line x1="160" y1="12" x2="160" y2="308" />
          </g>
          <path d="M160 160 L160 12 A148 148 0 0 1 296 220 Z" fill="url(#sweep)" />
          <circle cx="200" cy="100" r="3"   fill="oklch(0.82 0.135 78)" />
          <circle cx="240" cy="180" r="2.5" fill="oklch(0.66 0.155 48)" />
          <circle cx="120" cy="220" r="2.5" fill="oklch(0.66 0.155 48)" />
          <circle cx="90"  cy="120" r="2"   fill="oklch(0.66 0.155 48)" />
          <circle cx="180" cy="250" r="2"   fill="oklch(0.66 0.155 48)" />
          <circle cx="260" cy="240" r="3"   fill="oklch(0.66 0.20 22)" />
          <circle cx="160" cy="160" r="4"   fill="oklch(0.965 0.012 85)" />
          <circle cx="160" cy="160" r="9"   fill="none" stroke="oklch(0.965 0.012 85 / 0.4)" />
        </svg>
        <div style={{fontFamily:'var(--mono)',fontSize:'10px',letterSpacing:'0.14em',color:'var(--ink-3)',textTransform:'uppercase',marginTop:'14px',display:'flex',justifyContent:'space-between'}}>
          <span>scan · live</span>
          <span style={{color:'var(--amber)'}}>▲ edge.case · 244ms</span>
        </div>
      </div>
    </section>
  )
}
