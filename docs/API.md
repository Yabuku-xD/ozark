# Ozark API Reference

All endpoints are served from `/api`. The server binds to `127.0.0.1:8787` by default.

## Health

### GET /api/health

```json
{
  "ok": true,
  "name": "Ozark",
  "version": "2.2.0",
  "worker": { "active_jobs": 0 }
}
```

## Agents

### GET /api/agents

List registered agents.

## Runs

### POST /api/runs

Start a run.

```json
{
  "agent_id": "sample-support-agent",
  "scenario_count": 100,
  "async": true,
  "max_workers": 4,
  "gates": { "min_score": 80, "max_critical_violations": 0 }
}
```

* `async` — enqueue a background job and return `202` with a `job_id`.
* `dataset_id` — run scenarios from a saved dataset instead of generating them.
* `evaluators` — list of evaluator ids to run; defaults to configured + built-in evaluators.

### GET /api/runs

Paginated run summary list (no trace blobs).

```json
{
  "runs": [{ "id": "...", "agent_id": "...", "score": 87, "status": "passed" }],
  "next_cursor": "..."
}
```

### GET /api/runs/:id

Full run body including trace.

### POST /api/runs/:id/evaluate

Re-run evaluators on a saved run.

### POST /api/runs/:id/gate

Evaluate the release gate for a saved run.

### GET /api/runs/:id/otel

Export the run as OpenTelemetry GenAI-convention spans.

## Jobs

### GET /api/jobs

List recent jobs.

### GET /api/jobs/:id

Get job status, progress, and result.

## Issues

### GET /api/issues

List issues. Optional `status` query param.

### POST /api/issues/:id/status

Update issue status.

## Datasets

### GET /api/datasets
### GET /api/datasets/:id
### POST /api/datasets/from-run
### POST /api/datasets/from-issue
### POST /api/datasets/import

See examples in `examples/`.

## Evaluators

### POST /api/evaluators

Register a custom evaluator.

```json
{
  "id": "my-rubric",
  "name": "My Rubric",
  "type": "llm_judge",
  "config": {
    "rubric": "Response must include an apology.",
    "threshold": 0.7,
    "severity": "medium"
  }
}
```

## Scenarios

### GET /api/scenarios/generate

Query params: `agent_type`, `count`.

Generate scenarios for an agent type.

## Eval policies

### GET /api/eval-policies
### POST /api/eval-policies

Create and list release gate policies.
