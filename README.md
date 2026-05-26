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

Ozark helps teams test AI agents before production. It runs generated and custom scenarios against simulated or live agents, records traces, checks guardrails, and fails release gates when confidence drops.

## Features

- Local scenario runs for support, coding, data, ops, finance, healthcare, recruiting, sales, and adversarial cases.
- Deterministic guardrail checks for secrets, blocked tools, latency budgets, evaluator findings, and regressions.
- Dataset promotion, issue grouping, OpenTelemetry-style exports, and CI-ready release gates.
- React dashboard plus CLI/API workflow for repeatable agent evaluations.

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
