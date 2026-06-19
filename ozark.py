#!/usr/bin/env python3
import argparse
import json
import sys
import time
import urllib.request


# tree-sitter-patterns:python-print-statement ignored by using sys.stdout.write for intentional CLI output.
def write_output(value: object) -> None:
    sys.stdout.write(str(value) + "\n")


def write_json(value: object) -> None:
    write_output(json.dumps(value, indent=2))

BASE_URL = "http://127.0.0.1:8787"
# Polling interval (seconds) when following async jobs.
JOB_POLL_INTERVAL = 1.0


def request(method: str, path: str, payload: dict | None = None) -> dict:
    """Call the local Ozark API and return parsed JSON."""
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def cmd_dashboard(args: argparse.Namespace) -> int:
    url = BASE_URL + "/"
    if args.no_browser:
        write_output(url)
        return 0
    write_output(f"Opening Ozark dashboard at {url}")
    try:
        import webbrowser

        webbrowser.open(url)
    except Exception as exc:
        write_output(f"Could not open browser: {exc}. Visit {url}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    payload = {"agent_id": args.agent, "scenario_count": args.count}
    if args.dataset:
        payload["dataset_id"] = args.dataset
    if args.gates:
        payload["gates"] = json.loads(args.gates)
    if args.async_run:
        payload["async"] = True
        body = request("POST", "/api/runs", payload)
        # Async path: server returns 202 + job_id; poll to completion.
        run_id, run_score, run_status, gate = _follow_job(body["job_id"])
        write_json({"run_id": run_id, "score": run_score, "status": run_status, "gate": gate})
        return 0 if gate.get("passed") else 2

    body = request("POST", "/api/runs", payload)
    run = body["run"]
    gate = body.get("gate", {"passed": True, "failures": []})
    write_json({"run_id": run["id"], "score": run["score"], "status": run["status"], "gate": gate})
    return 0 if gate.get("passed") else 2


def _follow_job(job_id: str) -> tuple:
    """Poll a job until it terminates. Returns (run_id, score, status, gate)."""
    while True:
        body = request("GET", f"/api/jobs/{job_id}")
        job = body["job"]
        status = job["status"]
        if status == "succeeded":
            result = job["result"] or {}
            run = result.get("run", {})
            gate = result.get("gate", {"passed": True, "failures": []})
            return run.get("id", ""), run.get("score", 0), run.get("status", ""), gate
        if status == "failed":
            raise RuntimeError(f"Job {job_id} failed: {job.get('error')}")
        # pending / running — print progress and keep waiting.
        progress = job.get("progress", 0)
        total = job.get("total", 0)
        write_output(f"... {status}: {progress}/{total} scenarios")
        time.sleep(JOB_POLL_INTERVAL)


def cmd_promote(args: argparse.Namespace) -> int:
    body = request("POST", "/api/datasets/from-run", {
        "run_id": args.run,
        "name": args.name,
        "only_failed": not args.include_passed,
        "max_score": args.max_score,
    })
    write_json({"dataset_id": body["dataset"]["id"], "added": body["added"]})
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    payload = {}
    if args.policy:
        payload["policy_id"] = args.policy
    if args.gates:
        payload["gates"] = json.loads(args.gates)
    body = request("POST", f"/api/runs/{args.run}/gate", payload)
    write_json(body["gate"])
    return 0 if body["gate"].get("passed") else 2


def cmd_otel(args: argparse.Namespace) -> int:
    body = request("GET", f"/api/runs/{args.run}/otel")
    write_json(body)
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    payload = {}
    if args.evaluator_id:
        payload["evaluators"] = [{"id": args.evaluator_id}]
    body = request("POST", f"/api/runs/{args.run}/evaluate", payload)
    write_json(body)
    return 0 if body["eval_report"].get("passed") else 2


def cmd_rubric_eval(args: argparse.Namespace) -> int:
    """Register an LLM-as-judge evaluator and run it against a saved run."""
    evaluator_id = "rubric-" + args.name.lower().replace(" ", "-")[:20]
    request("POST", "/api/evaluators", {
        "id": evaluator_id,
        "name": args.name,
        "type": "llm_judge",
        "config": {
            "rubric": args.rubric,
            "prompt": args.prompt,
            "target": args.target,
            "threshold": args.threshold,
            "severity": args.severity,
        },
    })
    body = request("POST", f"/api/runs/{args.run}/evaluate", {
        "evaluators": [{"id": evaluator_id}],
    })
    write_json(body)
    return 0 if body["eval_report"].get("passed") else 2


def cmd_issues(args: argparse.Namespace) -> int:
    suffix = f"?status={args.status}" if args.status else ""
    body = request("GET", "/api/issues" + suffix)
    write_json(body)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    payload = {"path": args.path, "agent_id": args.agent_id, "agent_name": args.agent_name}
    body = request("POST", "/api/ingest/traces", payload)
    run = body["run"]
    write_json({
        "run_id": run["id"],
        "score": run["score"],
        "status": run["status"],
        "issues": len(body.get("issues", [])),
        "eval_passed": body.get("eval_report", {}).get("passed"),
    })
    return 0 if body.get("eval_report", {}).get("passed") else 2


def cmd_job(args: argparse.Namespace) -> int:
    body = request("GET", f"/api/jobs/{args.id}")
    job = body["job"]
    write_json({
        "job_id": job["id"],
        "kind": job["kind"],
        "status": job["status"],
        "progress": job["progress"],
        "total": job["total"],
        "error": job.get("error"),
    })
    if job["status"] == "failed":
        return 2
    if job["status"] == "succeeded":
        return 0
    return 0


def cmd_dataset_export(args: argparse.Namespace) -> int:
    body = request("GET", f"/api/datasets/{args.dataset}/export")
    write_json(body["dataset"])
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    suffix = "?format=md" if args.format == "md" else ""
    body = request("GET", f"/api/reports/{args.run}{suffix}")
    write_output(body["markdown"] if args.format == "md" else json.dumps(body["report"], indent=2))
    return 0 if body["report"].get("decision") == "ready" else 2


def cmd_experiment(args: argparse.Namespace) -> int:
    payload = {"agent_ids": args.agents.split(","), "scenario_count": args.count}
    if args.dataset:
        payload["dataset_id"] = args.dataset
    body = request("POST", "/api/experiments", payload)
    write_json(body["experiment"]["comparison"])
    return 0 if all(row.get("gate_passed") for row in body["experiment"]["comparison"]) else 2


def cmd_dataset_import(args: argparse.Namespace) -> int:
    body = request("POST", "/api/datasets/import", {"path": args.path, "dataset_id": args.dataset_id})
    write_json({"dataset_id": body["dataset"]["id"], "added": body["added"]})
    return 0


def cmd_issue_promote(args: argparse.Namespace) -> int:
    body = request("POST", "/api/datasets/from-issue", {"issue_id": args.issue, "name": args.name})
    write_json({"dataset_id": body["dataset"]["id"], "added": body["added"]})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ozark local agent eval CLI")
    sub = parser.add_subparsers(required=True)

    run = sub.add_parser("run", help="Run generated or dataset-backed evals")
    run.add_argument("--agent", required=True)
    run.add_argument("--count", type=int, default=100)
    run.add_argument("--dataset")
    run.add_argument("--gates", help="JSON gate overrides")
    run.add_argument("--async", dest="async_run", action="store_true",
                     help="Run asynchronously and poll the job queue")
    run.set_defaults(func=cmd_run)

    job_status = sub.add_parser("job", help="Show job status")
    job_status.add_argument("--id", required=True)
    job_status.set_defaults(func=cmd_job)

    promote = sub.add_parser("promote", help="Promote failed run results to a regression dataset")
    promote.add_argument("--run", required=True)
    promote.add_argument("--name", default="Regression dataset")
    promote.add_argument("--max-score", type=int, default=99)
    promote.add_argument("--include-passed", action="store_true")
    promote.set_defaults(func=cmd_promote)

    gate = sub.add_parser("gate", help="Evaluate a saved run against release gates")
    gate.add_argument("--run", required=True)
    gate.add_argument("--policy")
    gate.add_argument("--gates", help="JSON gate overrides")
    gate.set_defaults(func=cmd_gate)

    otel = sub.add_parser("otel", help="Export run as OpenTelemetry-shaped spans")
    otel.add_argument("--run", required=True)
    otel.set_defaults(func=cmd_otel)

    evaluate = sub.add_parser("evaluate", help="Run configured evaluators against a saved run")
    evaluate.add_argument("--run", required=True)
    evaluate.add_argument("--evaluator-id", help="Only run a specific evaluator by id")
    evaluate.set_defaults(func=cmd_evaluate)

    rubric_eval = sub.add_parser("rubric-eval", help="Run an LLM-as-judge rubric against a saved run")
    rubric_eval.add_argument("--run", required=True)
    rubric_eval.add_argument("--name", required=True, help="Evaluator name")
    rubric_eval.add_argument("--rubric", required=True, help="Rubric/criteria text")
    rubric_eval.add_argument("--prompt", default="Score this response against the rubric.", help="Judge prompt")
    rubric_eval.add_argument("--target", default="assistant_output", choices=["assistant_output", "full_trace", "user_input"])
    rubric_eval.add_argument("--threshold", type=float, default=0.7)
    rubric_eval.add_argument("--severity", default="medium", choices=["low", "medium", "high", "critical"])
    rubric_eval.set_defaults(func=cmd_rubric_eval)

    issues = sub.add_parser("issues", help="List grouped evaluator issues")
    issues.add_argument("--status")
    issues.set_defaults(func=cmd_issues)

    ingest = sub.add_parser("ingest", help="Import production traces from JSON or JSONL")
    ingest.add_argument("--path", required=True)
    ingest.add_argument("--agent-id", default="production-import")
    ingest.add_argument("--agent-name", default="Production Agent")
    ingest.set_defaults(func=cmd_ingest)

    report = sub.add_parser("report", help="Generate a release report")
    report.add_argument("--run", required=True)
    report.add_argument("--format", choices=["json", "md"], default="json")
    report.set_defaults(func=cmd_report)

    dashboard = sub.add_parser("dashboard", help="Open the local web dashboard")
    dashboard.add_argument("--no-browser", action="store_true", help="Print URL instead of opening browser")
    dashboard.set_defaults(func=cmd_dashboard)

    experiment = sub.add_parser("experiment", help="Compare agent variants on the same eval set")
    experiment.add_argument("--agents", required=True, help="Comma-separated agent IDs; first is baseline")
    experiment.add_argument("--dataset")
    experiment.add_argument("--count", type=int, default=25)
    experiment.set_defaults(func=cmd_experiment)

    export_ds = sub.add_parser("dataset-export", help="Export a dataset pack")
    export_ds.add_argument("--dataset", required=True)
    export_ds.set_defaults(func=cmd_dataset_export)

    import_ds = sub.add_parser("dataset-import", help="Import a dataset pack")
    import_ds.add_argument("--path", required=True)
    import_ds.add_argument("--dataset-id")
    import_ds.set_defaults(func=cmd_dataset_import)

    issue_promote = sub.add_parser("issue-promote", help="Promote an issue into a regression dataset")
    issue_promote.add_argument("--issue", required=True)
    issue_promote.add_argument("--name", default="Issue regression")
    issue_promote.set_defaults(func=cmd_issue_promote)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
