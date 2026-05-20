import { BorderBeam } from 'border-beam'

const AGENT_BEAM_PARAMS = [
  { duration: 1.52, strength: 0.82 },
  { duration: 2.18, strength: 0.72 },
  { duration: 1.84, strength: 0.78 },
  { duration: 2.41, strength: 0.65 },
]

const AGENTS = [
  {
    id: 'support',
    name: 'SupportOps',
    desc: 'Customer support agent handling refunds, order lookups, and account management with safety guardrails.',
    tools: ['lookup_user', 'check_order', 'issue_refund', 'send_email'],
  },
  {
    id: 'coding',
    name: 'CodeAssistant',
    desc: 'AI coding assistant that writes code, creates PRs, runs tests, and deploys services with safety gates.',
    tools: ['read_file', 'write_file', 'create_pr', 'deploy'],
  },
  {
    id: 'data',
    name: 'DataAnalyst',
    desc: 'Data analysis agent that queries databases, generates reports, and flags anomalies while protecting PII.',
    tools: ['run_query', 'analyze_data', 'generate_report'],
  },
  {
    id: 'ops',
    name: 'OpsController',
    desc: 'Autonomous operations agent for deployments, scaling, monitoring, and disaster recovery with approval gates.',
    tools: ['deploy', 'rollback', 'scale', 'update_config'],
  },
]

export default function Agents() {
  return (
    <section className="section agents" id="agents">
      <div className="section-label rotated">AGENTS</div>
      <div className="section-content split">
        <div className="split-left">
          <h2>Know your<br />agent before<br />anyone else<br />does.</h2>
          <p>Every agent runs through the same scenario suite. See exactly where they fail, what tools they misuse, and which guardrails they trip.</p>
        </div>
        <div className="split-right">
          <div className="agent-grid">
            {AGENTS.map((agent, i) => {
              const params = AGENT_BEAM_PARAMS[i % AGENT_BEAM_PARAMS.length]
              return (
                <BorderBeam
                  key={agent.id}
                  className="agent-beam"
                  size="md"
                  colorVariant="sunset"
                  theme="dark"
                  staticColors
                  borderRadius={12}
                  duration={params.duration}
                  strength={params.strength}
                >
                  <div className="agent-card">
                    <div className={`agent-icon ${agent.id}`} aria-hidden="true">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        {agent.id === 'support' && <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" />}
                        {agent.id === 'coding' && <path d="M16 18l6-6-6-6M8 6l-6 6 6 6" />}
                        {agent.id === 'data' && <><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" /><path d="M7 14l3-3 3 3 4-4" /></>}
                        {agent.id === 'ops' && <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />}
                      </svg>
                    </div>
                    <h3>{agent.name}</h3>
                    <p>{agent.desc}</p>
                    <div className="agent-tools">
                      {agent.tools.map((t) => (
                        <span key={t}>{t}</span>
                      ))}
                    </div>
                  </div>
                </BorderBeam>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
