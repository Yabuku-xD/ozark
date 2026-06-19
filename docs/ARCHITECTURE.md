# Ozark Architecture

Ozark is intentionally simple: a Python standard-library HTTP server, a SQLite database, and an in-process worker thread. This keeps the project easy to deploy, debug, and extend while still supporting production-grade concurrency.

## HTTP layer

`backend/server.py` is a `ThreadingHTTPServer` with explicit route dispatch. It intentionally avoids heavy frameworks to keep dependencies minimal. Long-running work is delegated to the job queue so request threads never block.

## Job queue

`backend/engine/jobs.py` stores jobs in SQLite and drains them with a single background worker. Jobs report progress so clients can poll. Multiple worker instances could be added later by switching to a broker-backed queue without changing the job schema.

## Simulation engine

`backend/engine/simulator.py` runs scenarios deterministically using a seeded random generator and stable SHA-256 hashing. It supports parallel execution via `ThreadPoolExecutor`.

## Evaluators

`backend/engine/evaluators.py` dispatches by evaluator type:

- `regex` — pattern matching for secrets, PII, output structure.
- `tool_sequence` — checks called vs expected/blocked tools.
- `latency_budget` — wall-clock latency checks.
- `risk_coverage` — high-risk scenario pass-rate checks.
- `llm_judge` — calls a judge provider for semantic scoring.

Judge providers live in `backend/engine/judge_providers.py`. The default is an offline heuristic; users can bring any OpenAI-compatible or Anthropic-compatible endpoint (OpenAI, Azure, Ollama, vLLM, LiteLLM, Groq, Together, etc.) by setting `JUDGE_PROVIDER`, `JUDGE_API_KEY`, `JUDGE_MODEL`, and optionally `JUDGE_BASE_URL` and `JUDGE_CONTEXT_WINDOW`.

## Persistence

`backend/db.py` uses SQLite in WAL mode. Every connection is short-lived and configured with a 5-second busy timeout. Schema migrations are additive and keyed by `schema_version`.

## Frontend

The frontend is a React 19 + Vite application with React Router. It has two separate entry points:

- **Landing page** (`index.html` → `src/main.jsx`) — marketing content, served only by the Vite dev server (`npm run dev`).
- **Dashboard** (`dashboard.html` → `src/dashboard.jsx`) — the operational UI for browsing runs, jobs, issues, scenarios, and agents. This is what the Python backend serves at `/` (and all client-side routes via SPA fallback).

`run.sh` builds the dashboard and opens it at `http://127.0.0.1:8787/`.
