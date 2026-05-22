# Ozark

The **only local-first, zero-cost, zero-API-key** AI agent simulation lab with a real execution engine. Test your agents against thousands of scenarios, enforce guardrails at runtime, and get a deployment confidence score before going to production.

## Why Ozark

| Tool | Pricing | Ozark Advantage |
|------|---------|----------------|
| LangSmith | Paid SaaS, cloud-only | Local-first, no vendor lock-in |
| AgentOps | Freemium, cloud | No API keys, fully offline |
| Braintrust | SaaS, usage-based | Zero setup, instant start |
| Patronus AI | Enterprise SaaS | Free, no enterprise contract |
| Arize Phoenix | Open source | Simulation + scoring, not just observability |

## Features

- **Local-first** — no internet, no API keys, no paid services
- **Real execution engine** — Policy engine, Markov behavior model, coverage analyzer
- **Live agent testing** — Connect to your running agent via HTTP or stdio
- **50,000+ scenarios** — Happy paths, edge cases, adversarial, multi-turn, fault injection
- **Runtime guardrails** — PII leaks, prompt injection, dangerous code, destructive SQL, sensitive file access, exfiltration
- **8-dimensional scoring** — Task completion, tool safety, guardrail compliance, security posture, error recovery, latency, cost, consistency
- **Coverage analysis** — Tool coverage, state/transition coverage, coverage gaps, heatmap data
- **Trace diffing** — Compare runs to detect regressions
- **Native macOS runner** — SwiftUI desktop app with file picker and live test mode
- **Custom scenario packs** — Add your own YAML files to extend the scenario library

## Quick Start

```bash
./run.sh
```

On macOS with Swift installed, this launches the native SwiftUI runner. On other platforms, it starts the terminal-based Python server at `http://127.0.0.1:8787`.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/agents` | List all agents |
| `POST` | `/api/agents` | Create an agent config |
| `POST` | `/api/agents/import` | Import agent from local path |
| `GET` | `/api/scenarios/generate?agent_type=X&count=N` | Preview generated scenarios |
| `POST` | `/api/scenarios/custom` | Add custom scenario templates or load a YAML pack |
| `POST` | `/api/runs` | Run a simulation suite |
| `POST` | `/api/runs/live` | Run scenarios against a live agent via HTTP |
| `GET` | `/api/runs/:id` | Get a specific run by ID |
| `POST` | `/api/runs/:id/replay` | Replay a specific run |
| `GET` | `/api/runs?limit=20` | List recent runs |
| `GET` | `/api/runs/diff?a=X&b=Y` | Diff two runs |
| `GET` | `/api/coverage/:agent_id` | Get coverage data for an agent |

## Example: Run a Simulation

```bash
curl -s -X POST http://127.0.0.1:8787/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"agent_id":"sample-support-agent","scenario_count":50}'
```

## Example: Test a Live Agent

```bash
curl -s -X POST http://127.0.0.1:8787/api/runs/live \
  -H 'Content-Type: application/json' \
  -d '{"endpoint":"http://localhost:8080/agent","scenario_count":10,"agent_type":"customer_support"}'
```

## Bring Your Own Agent

Create a JSON config matching this schema:

```json
{
  "name": "My Agent",
  "description": "What this agent does",
  "agent_type": "customer_support",
  "framework": "langchain",
  "system_prompt": "You are a helpful agent.",
  "tools": [
    {"name": "my_tool", "description": "Does something", "risk": "low"}
  ],
  "guardrails": [
    {"id": "no_pii", "rule": "Block PII leaks", "severity": "block", "category": "content_safety"}
  ],
  "max_turns": 10,
  "model": "gpt-4"
}
```

Import via the SwiftUI runner's Browse button, or via API:

```bash
curl -s -X POST http://127.0.0.1:8787/api/agents/import \
  -H 'Content-Type: application/json' \
  -d '{"path": "/path/to/your/config.json"}'
```

## Adding Custom Scenarios

Create a YAML file in `backend/scenarios/` or load a custom pack:

```bash
curl -s -X POST http://127.0.0.1:8787/api/scenarios/custom \
  -H 'Content-Type: application/json' \
  -d '{"pack_path": "/path/to/your/scenarios.yaml"}'
```

## Scoring

Ozark evaluates agents across 8 weighted dimensions:

| Dimension | Weight |
|-----------|--------|
| Task Completion | 25% |
| Tool Safety | 20% |
| Guardrail Compliance | 20% |
| Security Posture | 15% |
| Error Recovery | 10% |
| Latency Performance | 5% |
| Cost Efficiency | 3% |
| Behavioral Consistency | 2% |

Results: `>= 80%` green (ready), `>= 60%` yellow (needs review), `< 60%` red (blocked).
