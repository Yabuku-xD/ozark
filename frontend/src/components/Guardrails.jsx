const GUARDRAILS = [
  { code: 'PII', text: 'Blocks SSNs, credit cards, API keys, and passwords from leaking in responses or tool calls' },
  { code: 'INJ', text: 'Detects prompt injection, jailbreak attempts, and social engineering with regex + pattern matching' },
  { code: 'CMD', text: 'Blocks dangerous commands — rm -rf, DROP TABLE, chmod 777, and other destructive operations' },
  { code: 'FIL', text: 'Prevents access to /etc/passwd, .env files, SSH keys, and other sensitive system paths' },
  { code: 'EXF', text: 'Catches data exfiltration via curl, wget, and unauthorized external API calls' },
  { code: 'CNF', text: 'Requires explicit confirmation before refunds, deletions, deployments, and prescriptions' },
]

export default function Guardrails() {
  return (
    <section className="section" id="guardrails">
      <div className="section-label rotated">GUARDRAILS</div>
      <div className="section-content split reverse">
        <div className="split-left">
          <div className="guardrail-list">
            {GUARDRAILS.map((g) => (
              <div className="guardrail-item" key={g.code}>
                <div className="guardrail-icon">{g.code}</div>
                <p>{g.text}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="split-right">
          <h2>Guardrails that<br />run in production<br />— not just in<br />theory.</h2>
          <p>Six runtime guardrail categories tested at the scenario level. Ozark validates that your guardrails fire correctly — not just that they exist — so you know your safety net actually works.</p>
        </div>
      </div>
    </section>
  )
}
