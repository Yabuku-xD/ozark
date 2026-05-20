# Ozark

Ozark is a zero-cost, local-first simulation lab for testing AI agents before production. It runs generated scenarios against sample agents, enforces guardrails, records traces, and produces a deployment confidence score through a browser UI.

## Features

- Local web app with no paid services or API keys required
- Four built-in agent profiles: SupportOps, CodeAssistant, DataAnalyst, and OpsController
- Scenario generation for happy paths, edge cases, error recovery, adversarial prompts, multi-turn conversations, and compliance cases
- Runtime guardrails for PII leaks, prompt injection, dangerous code, destructive SQL, sensitive file access, and exfiltration attempts
- Simulation scoring across task completion, tool safety, guardrail compliance, security posture, error recovery, latency, cost, and consistency
- Front-end test console for running simulations, previewing scenarios, and viewing run history
- **Native macOS SwiftUI runner** for local agent testing with a file picker UI
- **Static display page** deployable to Vercel

## Requirements

- Python 3.11+
- A modern browser
- macOS 13+ with Swift toolchain (for the native runner — optional)

No npm install is required for the current version.

## Quick Start

```bash
./run.sh
```

On macOS with Swift installed, this launches the **native SwiftUI runner** — a dark-themed desktop app where you can:

1. Browse and select your local agent config (JSON file or folder)
2. Configure scenario count and agent type
3. Start the simulation server
4. Open results in your browser

On other platforms (or without Swift), it falls back to the terminal-based Python server at `http://127.0.0.1:8787`.

## Bring Your Own Agent

To test your own agent, create a JSON config file matching this schema:

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

Save it as `config.json` in a folder, then use the SwiftUI runner to select it — or import via the API:

```bash
curl -s -X POST http://127.0.0.1:8787/api/agents/import \
  -H 'Content-Type: application/json' \
  -d '{"path": "/path/to/your/config.json"}'
```

## Using the App

1. Click `RUN` or `Run simulation`.
2. Select an agent.
3. Choose a scenario count.
4. Use `Preview scenarios` to inspect generated tests.
5. Use `Run simulation` to execute the suite.
6. Use `Load history` to review previous local runs.

## API

| Method   | Endpoint                                                         | Description                    |
| -------- | ---------------------------------------------------------------- | ------------------------------ |
| `GET`  | `/api/health`                                                  | Health check                   |
| `GET`  | `/api/agents`                                                  | List built-in and saved agents |
| `POST` | `/api/agents`                                                  | Create an agent config         |
| `POST` | `/api/agents/import`                                           | Import agent from local path   |
| `GET`  | `/api/scenarios/generate?agent_type=customer_support&count=25` | Generate scenario previews     |
| `POST` | `/api/runs`                                                    | Run a simulation suite         |
| `GET`  | `/api/runs?limit=20`                                           | List recent runs               |
| `GET`  | `/api/runs/diff?a=<run_id>&b=<run_id>`                         | Compare two runs               |

## Example API Run

```bash
curl -s -X POST http://127.0.0.1:8787/api/runs \
  -H 'Content-Type: application/json' \
  -d '{"agent_id":"sample-support-agent","scenario_count":10}'
```

## Notes

- Data is stored locally through SQLite when runs are created.
- The app is designed to work without internet access except for the optional Google-hosted Geist font.
- Generated Python caches are not required and can be deleted safely.
- The SwiftUI runner requires macOS 13 (Ventura) or later. On older macOS or Linux, `./run.sh` automatically falls back to terminal mode.
