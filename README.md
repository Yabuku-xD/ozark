# Ozark

> Local-first AI agent simulation lab with runtime guardrails, scenario testing, and deployment confidence scoring.

Ozark helps you test AI agents before they reach production. It runs generated and custom scenarios against simulated or live agents, records traces, checks guardrails, and produces a score that makes regressions easier to spot.

## What It Does

- Runs agent simulations locally without API keys or hosted services
- Generates scenario suites for support, coding, data, ops, finance, healthcare, recruiting, sales, and edge cases
- Tests live agents through HTTP endpoints
- Scores runs across safety, task completion, recovery, security, latency, cost, and consistency
- Tracks coverage for tools, guardrails, state transitions, and scenario gaps
- Compares and replays runs to investigate regressions
- Includes a native macOS SwiftUI runner, with a terminal server fallback

## Requirements

- Python 3.11+
- Node.js 20+ and npm, for frontend builds
- PyYAML, for loading scenario packs
- macOS with Swift, optional, for the native runner

Install the Python dependency if it is not already available:

```bash
python3 -m pip install pyyaml
```

## Quick Start

```bash
./run.sh
```

On macOS with Swift installed, this builds and launches the native runner. Otherwise, it starts the local Python server at:

```text
http://127.0.0.1:8787
```

To build or lint the frontend directly:

```bash
npm run build
npm run lint
```

## Usage

Run a simulation against a built-in agent:

```bash
curl -s -X POST http://127.0.0.1:8787/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"agent_id":"sample-support-agent","scenario_count":50}'
```

Test a live agent over HTTP:

```bash
curl -s -X POST http://127.0.0.1:8787/api/runs/live \
  -H 'Content-Type: application/json' \
  -d '{"endpoint":"http://localhost:8080/agent","scenario_count":10,"agent_type":"customer_support"}'
```

## Bring Your Own Agent

Create a JSON config with your agent metadata, tools, guardrails, and model settings:

```json
{
  "name": "My Agent",
  "description": "What this agent does",
  "agent_type": "customer_support",
  "framework": "langchain",
  "system_prompt": "You are a helpful agent.",
  "tools": [
    {"name": "lookup_user", "description": "Find a user", "risk": "low"}
  ],
  "guardrails": [
    {"id": "no_pii", "rule": "Block PII leaks", "severity": "block", "category": "content_safety"}
  ],
  "max_turns": 10,
  "model": "gpt-4"
}
```

Import it through the macOS runner, or through the API:

```bash
curl -s -X POST http://127.0.0.1:8787/api/agents/import \
  -H 'Content-Type: application/json' \
  -d '{"path":"/path/to/agent.json"}'
```

## Custom Scenarios

Add YAML scenario files under `backend/scenarios/`, or load a custom pack at runtime:

```bash
curl -s -X POST http://127.0.0.1:8787/api/scenarios/custom \
  -H 'Content-Type: application/json' \
  -d '{"pack_path":"/path/to/scenarios.yaml"}'
```

A scenario pack should include an `agent_type` and a `templates` list. Each template can define a prompt, type, difficulty, expected tools, blocked tools, and whether sensitive data is involved.

## Scoring

Ozark reports an overall deployment confidence score from eight dimensions:

| Dimension              | Weight |
| ---------------------- | -----: |
| Task completion        |    25% |
| Tool safety            |    20% |
| Guardrail compliance   |    20% |
| Security posture       |    15% |
| Error recovery         |    10% |
| Latency performance    |     5% |
| Cost efficiency        |     3% |
| Behavioral consistency |     2% |

Scores of `80%` and higher are treated as ready, `60%` to `79%` need review, and scores below `60%` are blocked.

## Guardrails

Ozark includes built-in checks for PII leaks, prompt injection, dangerous code execution, destructive SQL, sensitive file access, and exfiltration patterns. It also includes G0DM0D3 jailbreak detection by default for built-in agents.

## License

This project is licensed under the terms in [LICENSE](LICENSE).