const lines = [
  ['14:02:08.541', 'adv/sys-extract', 'GUARD', 'g0dm0d3_system_prompt_injection'],
  ['14:02:09.580', 'edge/temporal', 'WARN', 'ambiguous_next_friday'],
  ['14:02:10.112', 'fault/timeout', 'OK', 'tool_retry_on_502'],
  ['14:02:11.420', 'happy/reset', 'OK', 'password_reset_flow'],
  ['14:02:12.003', 'privacy/pii', 'BLOCK', 'pii_leak_via_tool_args'],
  ['14:02:14.207', 'run.complete', 'READY', 'passed_42 warned_5 blocked_3 score_87.4'],
]

export default function TerminalTrace() {
  return (
    <section className="section terminal-section" id="terminal">
      <div className="container">
        <div className="section-header reveal">
          <p className="eyebrow">Live trace</p>
          <h2>Readable evidence while the run executes.</h2>
          <p>Inspect the exact scenario, turn outcome, guardrail hit, and final confidence impact without shipping traces to a hosted vendor.</p>
        </div>

        <div className="terminal-card reveal">
          <div className="terminal-top">
            <span>ozark run --suite release</span>
            <span>localhost:8787</span>
          </div>
          {lines.map(([time, scenario, state, detail]) => (
            <div className="terminal-line" key={`${time}-${scenario}`}>
              <span>{time}</span>
              <code>{scenario}</code>
              <b className={`state state-${state.toLowerCase()}`}>{state}</b>
              <em>{detail}</em>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
