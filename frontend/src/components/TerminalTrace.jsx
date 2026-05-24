const lines = [
  { ts: '14:02:08.541', text: '\u25B8 sc.18423 adv/sys-extract  turn 1\u00B73   GUARD  g0dm0d3_system_prompt_injection', cls: 'warn' },
  { ts: '14:02:09.580', text: '\u25B8 sc.18427 edge/temporal    turn 2\u00B72   WARN   ambiguous "next friday"', cls: 'warn' },
  { ts: '14:02:10.112', text: '\u25B8 sc.18424 fault/timeout    turn 1\u00B75   OK     tool_retry_on_502', cls: 'ok' },
  { ts: '14:02:11.420', text: '\u25B8 sc.18428 happy/reset      turn 3\u00B73   OK     password_reset_flow', cls: 'ok' },
  { ts: '14:02:12.003', text: '\u25B8 sc.18426 adv/pii-leak     turn 2\u00B71   BLOCK  pii_leak_via_tool_args', cls: 'err' },
  { ts: '14:02:14.207', text: '\u25C6 run.complete   passed 42 \u00B7 warned 5 \u00B7 blocked 3 \u00B7 score 87.4%', cls: 'ok' },
]

export default function TerminalTrace() {
  return (
    <section className="terminal-section section" id="terminal" style={{ paddingBottom: 0 }}>
      <div className="container">
        <div className="section-header reveal">
          <p className="section-label">Live Trace</p>
          <h2 className="section-title">Real-time agent behavior</h2>
          <p className="section-desc">
            Every scenario execution streams to the terminal. Inspect turns, guardrail hits, and tool calls in real time.
          </p>
        </div>

        <div className="terminal-card reveal">
          <div className="terminal-header">
            <span className="terminal-dot r" />
            <span className="terminal-dot y" />
            <span className="terminal-dot g" />
            <span className="terminal-label">ozark run --scenario full-suite</span>
          </div>
          <div>
            {lines.map((line, i) => (
              <div key={i} className="terminal-line">
                <span className="ts">{line.ts}</span>{'  '}
                <span className={line.cls}>{line.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
