<p align="center">
  <img src="frontend/public/assets/favicon.svg" alt="Ozark logo" width="154" />
</p>

<h1 align="center">Ozark</h1>

<p align="center">
  Local-first AI agent simulation lab with runtime guardrails, scenario testing, and release confidence scoring.
</p>

<p align="center">
  <a href="https://github.com/Yabuku-xD/ozark"><img alt="Docs" src="https://img.shields.io/badge/docs-repository%20guide-69707f?labelColor=555555&style=for-the-badge"></a>
  <a href="backend/scenarios"><img alt="Data" src="https://img.shields.io/badge/data-DOL%20%2B%20community-ffd400?labelColor=555555&style=for-the-badge"></a>
  <a href="https://github.com/Yabuku-xD/ozark/releases"><img alt="Release" src="https://img.shields.io/github/v/release/Yabuku-xD/ozark?include_prereleases&label=release&labelColor=555555&color=d43d1a&style=for-the-badge"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-2f6f52?labelColor=555555&style=for-the-badge"></a>
  <img alt="Frontend" src="https://img.shields.io/badge/frontend-React%2019-1f5a99?labelColor=555555&style=for-the-badge">
  <img alt="Backend" src="https://img.shields.io/badge/backend-Python-2f6f52?labelColor=555555&style=for-the-badge">
</p>

Ozark helps teams test AI agents before production. It runs generated and custom scenarios against simulated or live agents, records traces, checks guardrails, groups evaluator findings, and fails release gates when confidence drops.

## Features

- Local scenario runs for support, coding, data, ops, finance, healthcare, recruiting, sales, and adversarial cases.
- Risk-aware scenario metadata for low, medium, high, critical, and safety-critical evaluation paths.
- Deterministic guardrail checks for secrets, blocked tools, latency budgets, evaluator findings, and regressions.
- Release policies that block on score, confidence, critical violations, high-risk failures, safety-critical failures, and risk-adjusted pass rate.
- Dataset promotion, issue grouping, OpenTelemetry-style exports, coverage reports, and CI-ready release gates.
- React dashboard plus CLI/API workflow for repeatable agent evaluations.

## Architecture

Ozark keeps the HTTP layer thin and moves evaluation orchestration into backend modules:

- `backend/engine/run_pipeline.py` owns simulation, coverage, evaluator execution, issue recording, release-gate evaluation, and run persistence.
- `backend/adapters/common.py` defines the shared adapter response shape used by HTTP and stdio agent adapters.
- `backend/db.py` exposes focused store interfaces for agents, runs, datasets, policies, and evaluators while retaining SQLite as the default adapter.
- `backend/engine/coverage.py`, `eval_policy.py`, `scoring.py`, and `reports.py` share risk vocabulary for summaries, recommendations, release reports, and gates.

## Quick start

```bash
npm ci
python3 -m pip install -r requirements.txt
./run.sh
```

Run a release gate:

```bash
python3 ozark.py run --agent sample-support-agent --count 25 \
  --gates '{"min_score":80,"max_critical_violations":0,"max_failed_scenarios":0}'
```

## Stack

- Frontend: React 19 + Vite
- Backend: Python standard-library HTTP server + PyYAML
- CI: GitHub Actions eval workflow

## License

MIT © Shyamalan Kannan
