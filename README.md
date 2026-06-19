<p align="center">
  <img src="frontend/public/assets/favicon.svg" alt="Ozark logo" width="154" />
</p>

<h1 align="center">Ozark</h1>

<p align="center">
  Local-first AI agent simulation lab with runtime guardrails, scenario testing, and release confidence scoring.
</p>

<p align="center">
  <a href="#quick-start"><img alt="Docs" src="https://img.shields.io/badge/docs-quick%20start-69707f?labelColor=555555&style=for-the-badge"></a>
  <a href="backend/scenarios"><img alt="Data" src="https://img.shields.io/badge/data-DOL%20%2B%20community-ffd400?labelColor=555555&style=for-the-badge"></a>
  <a href="https://github.com/Yabuku-xD/ozark/releases"><img alt="Release" src="https://img.shields.io/badge/release-v0.2.0-d43d1a?labelColor=555555&style=for-the-badge"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-2f6f52?labelColor=555555&style=for-the-badge"></a>
  <img alt="Frontend" src="https://img.shields.io/badge/frontend-React%2019%20%2B%20Vite-1f5a99?labelColor=555555&style=for-the-badge">
  <img alt="Backend" src="https://img.shields.io/badge/backend-Python%203.12-2f6f52?labelColor=555555&style=for-the-badge">
  <img alt="Database" src="https://img.shields.io/badge/database-SQLite%20WAL-0f5132?labelColor=555555&style=for-the-badge">
  <img alt="Dashboard" src="https://img.shields.io/badge/dashboard-Lighthouse%20100-2f6f52?labelColor=555555&style=for-the-badge">
</p>

**Ozark** helps teams test AI agents before production. It runs generated and custom scenarios against **simulated or live agents**, records traces, checks guardrails, groups evaluator findings into issues, and fails release gates when confidence drops.

**Key differentiator:** Ozark can run full evaluations **without calling an LLM**. Its deterministic simulator makes CI runs free, reproducible, and fast. When you need semantic judgment, plug in OpenAI, Anthropic, or your own judge provider.

## Features

- **Deterministic simulation engine** — seeded random tool simulation with reproducible results across restarts.
- **Risk-aware scenarios** — low / medium / high / critical / safety-critical metadata flows through scoring, coverage, and release gates.
- **Runtime guardrails** — secrets, blocked tools, PII leakage, prompt injection, dangerous commands, and OWASP LLM Top 10 checks.
- **LLM-as-judge evaluators** — optional semantic rubric scoring via OpenAI or Anthropic, with an offline heuristic fallback.
- **Framework adapters** — plug in LangChain, LangGraph, CrewAI, OpenAI Agents SDK, or AutoGen agents (optional dependencies).
- **Background job queue** — SQLite-backed worker pool; `POST /api/runs` with `"async": true` returns a job id immediately.
- **Parallel scenario execution** — `ThreadPoolExecutor` for both simulated and live HTTP runs.
- **Release gate** — blocks on score, confidence, critical violations, high-risk failures, safety-critical failures, and risk-adjusted pass rate.
- **Issue grouping + dataset promotion** — failed runs become regression datasets so bugs can't recur silently.
- **OpenTelemetry export** — export runs as OTel spans following GenAI semantic conventions.
- **React dashboard** — browse runs, jobs, issues, scenarios, and agents. Landing page is a separate Vite dev entry.
- **CLI + CI** — `ozark.py run`, `ozark.py rubric-eval`, GitHub Actions workflow, Dockerfile, and docker-compose.

## Quick start

```bash
./run.sh
```

This installs deps, builds the dashboard, starts the server, and opens `http://127.0.0.1:8787/` in your browser.

Alternatively, manually:

```bash
npm ci
python3.12 -m pip install -r requirements.txt
npm run build          # build the dashboard
python3.12 -m backend.server   # start the API + dashboard
```

Open the dashboard at `http://127.0.0.1:8787`.

Run a release gate from the CLI:

```bash
python3.12 ozark.py run --agent sample-support-agent --count 25 \
  --gates '{"min_score":80,"max_critical_violations":0,"max_failed_scenarios":0}'
```

Run asynchronously (returns a job id, polls to completion):

```bash
python3.12 ozark.py run --agent sample-support-agent --count 1000 --async
```

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health + active job count |
| POST | `/api/runs` | Start a simulation run (sync or `async`) |
| GET | `/api/runs` | Paginated run list (no trace blobs) |
| GET | `/api/runs/:id` | Full run + trace |
| POST | `/api/runs/:id/evaluate` | Run evaluators on a saved run |
| POST | `/api/runs/:id/gate` | Evaluate release gate |
| GET | `/api/jobs` | List background jobs |
| GET | `/api/jobs/:id` | Job status + result |
| GET | `/api/issues` | Issue list |
| GET | `/api/scenarios/generate` | Generate scenarios for an agent type |
| GET | `/api/agents` | List agents |

See [docs/API.md](docs/API.md) for the full reference.

## Framework adapters

If the framework is installed, Ozark can run your real agent:

```python
from backend.adapters.framework_adapters import framework_runner, list_frameworks

runner = framework_runner(my_langgraph_agent, "langgraph")
# runner(scenario) returns an Ozark result dict
```

Supported frameworks: `langchain`, `langgraph`, `crewai`, `openai_agents`, `autogen`.

## LLM-as-judge rubric

Run a semantic evaluator from the CLI:

```bash
python3.12 ozark.py rubric-eval \
  --run run-abc123 \
  --name "Tone check" \
  --rubric "The response should be polite and empathetic." \
  --threshold 0.7
```

Bring any OpenAI-compatible or Anthropic-compatible endpoint by setting `JUDGE_PROVIDER`, `JUDGE_API_KEY`, and `JUDGE_MODEL` in `.env`. If unset, Ozark falls back to a deterministic offline heuristic.

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `8787` | HTTP port |
| `OZARK_ALLOW_PRIVATE_ENDPOINTS` | `0` | Allow live agents on private IPs (SSRF) |
| `OZARK_ALLOWED_ENDPOINT_HOSTS` | — | Hostname allowlist for live endpoints |
| `OZARK_ALLOWED_TRACE_ROOTS` | project root | Allowed roots for trace ingestion |
| `JUDGE_PROVIDER` | — | `openai` or `anthropic` (selects judge SDK) |
| `JUDGE_API_KEY` | — | API key for the judge provider |
| `JUDGE_BASE_URL` | SDK default | Override for Azure, Ollama, vLLM, Groq, etc. |
| `JUDGE_MODEL` | — | Model name for judging |
| `JUDGE_CONTEXT_WINDOW` | `128000` | Max context tokens (truncates long text) |

## Development

```bash
# Backend tests + lint
python3.12 -m pytest backend/tests/ -q
python3.12 -m ruff check backend/ ozark.py

# Frontend tests + lint + build
cd frontend
npm test
npm run lint
npm run build
```

## Docker

```bash
docker compose up --build
```

The container serves the API and dashboard on `http://localhost:8787` with a persistent `ozark-data` volume.

## Stack

- Frontend: React 19 + Vite + React Router
- Backend: Python 3.12 standard-library HTTP server + PyYAML
- Database: SQLite (WAL mode)
- CI: GitHub Actions (backend lint/test, frontend lint/test/build, release-gate smoke test)

## License

MIT © Shyamalan Kannan
