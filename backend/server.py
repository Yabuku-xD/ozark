import json
import logging
import os
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import models
from .db import (
    add_annotation,
    add_dataset_item,
    create_dataset,
    get_agent,
    get_coverage,
    get_dataset,
    get_eval_policy,
    get_evaluator,
    get_issue,
    get_run_by_id,
    init_db,
    list_agents,
    list_annotations,
    list_datasets,
    list_eval_policies,
    list_evaluators,
    list_issues,
    list_runs,
    save_run,
    update_issue_status,
    upsert_agent,
    upsert_eval_policy,
    upsert_evaluator,
)
from .engine.dataset_io import export_dataset, load_dataset_pack
from .engine.datasets import scenario_dict_to_definition, scenario_from_result
from .engine.eval_policy import DEFAULT_GATES, EvalPolicy
from .engine.evaluators import builtin_evaluators
from .engine.experiments import run_experiment_matrix
from .engine.ingest import load_trace_payload, normalize_payload
from .engine.otel_export import run_to_otel_spans
from .engine.reports import build_release_report, render_markdown_report
from .engine.roadmap import product_roadmap
from .engine.run_pipeline import (
    RunPipeline,
    evaluate_with_configured_evaluators,
    record_issues,
)
from .engine.scenario_gen import ScenarioGenerator
from .engine.simulator import SimulationEngine
from .engine.tracing import ReplayEngine

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend" / "dist"
AGENTS_FILE = ROOT / "backend" / "agents.json"
LOGGER = logging.getLogger(__name__)


def _load_builtin_agents() -> list[dict]:
    if AGENTS_FILE.exists():
        with AGENTS_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    return []


BUILTIN_AGENTS = _load_builtin_agents()


def _import_agent_from_path(file_path: str) -> tuple[str, str, str, dict]:
    path = Path(file_path).expanduser().resolve()

    if path.is_dir():
        candidates = ["config.json", "agent.json", "ozark.json", "agent_config.json"]
        found = None
        for candidate in candidates:
            candidate_path = path / candidate
            if candidate_path.exists():
                found = candidate_path
                break
        if not found:
            json_files = list(path.glob("*.json"))
            if json_files:
                found = json_files[0]
        if not found:
            raise FileNotFoundError(f"No agent config found in {file_path}")
        path = found

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    config = data.get("config", data)
    name = config.get("name", "Imported Agent")
    description = config.get("description", "")
    agent_id = name.lower().replace(" ", "-") + "-" + uuid.uuid4().hex[:6]
    return agent_id, name, description, config


def bootstrap() -> None:
    init_db()
    now = models.iso_now()
    for ba in BUILTIN_AGENTS:
        upsert_agent(ba["id"], ba["name"], ba["description"], ba["config"], now)
    for evaluator in builtin_evaluators():
        upsert_evaluator(
            evaluator["id"],
            evaluator["name"],
            evaluator["type"],
            evaluator["config"],
            now,
        )

    agent_path = os.environ.get("OZARK_AGENT_PATH")
    if agent_path:
        try:
            agent_id, name, description, config = _import_agent_from_path(agent_path)
            upsert_agent(agent_id, name, description, config, now)
            LOGGER.info("Imported agent %r from %s", name, agent_path)
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError) as exc:
            LOGGER.warning("Failed to import agent from %s: %s", agent_path, exc)


def read_json(handler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def _scenario_from_template(
    tmpl: dict,
    agent_type: str = "custom",
) -> models.ScenarioDefinition:
    return models.ScenarioDefinition(
        name=tmpl.get("prompt", "")[:60].strip(),
        scenario_type=models.ScenarioType(tmpl.get("type", "happy_path")),
        description=tmpl.get("prompt", "")[:200],
        user_prompt=tmpl.get("prompt", ""),
        expected_tools=tmpl.get("expected_tools", []),
        blocked_tools=tmpl.get("blocked_tools", []),
        sensitive_data=tmpl.get("sensitive_data", False),
        difficulty=tmpl.get("difficulty", "medium"),
        agent_type=agent_type,
        risk_level=tmpl.get("risk_level", "medium"),
        user_impact=tmpl.get("user_impact", "moderate"),
        risk_tags=tmpl.get("risk_tags", []),
    )


def _dataset_issue_tags(issue: dict, scenario: dict) -> list[str]:
    return [
        "issue",
        issue["severity"],
        issue["id"],
        scenario.get("difficulty", "medium"),
    ]


def _load_dataset_scenarios(
    dataset_id: str,
) -> tuple[list[models.ScenarioDefinition], dict | None]:
    dataset = get_dataset(dataset_id)
    if not dataset:
        return [], None
    scenarios = []
    for item in dataset["items"]:
        scenarios.append(scenario_dict_to_definition(item["scenario"]))
    return scenarios, dataset


def send_json(handler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "*")
    handler.send_header("Access-Control-Allow-Headers", "*")
    handler.end_headers()
    handler.wfile.write(body)


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path)
        clean = unquote(parsed.path)
        if clean == "/" or clean == "":
            clean = "/index.html"

        frontend_root = FRONTEND.resolve()
        requested = (frontend_root / clean.lstrip("/")).resolve()
        if requested == frontend_root or frontend_root not in requested.parents:
            return str(frontend_root / "__not_found__")
        return str(requested)

    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        send_json(self, {})

    def _get_default_agent_id(self) -> str:
        agents = BUILTIN_AGENTS
        return agents[0]["id"] if agents else ""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        try:
            if path == "/api/health":
                send_json(self, {"ok": True, "name": "Ozark", "version": "2.1.0"})
            elif path == "/api/agents":
                send_json(self, {"agents": list_agents()})
            elif path == "/api/scenarios/generate":
                agent_type = params.get("agent_type", ["customer_support"])[0]
                count = int(params.get("count", ["100"])[0])
                gen = ScenarioGenerator()
                scenarios = gen.generate_all(agent_type=agent_type, count=count)
                send_json(
                    self,
                    {
                        "scenarios": [s.to_dict() for s in scenarios],
                        "count": len(scenarios),
                    },
                )
            elif path == "/api/runs":
                limit = int(params.get("limit", ["20"])[0])
                send_json(self, {"runs": list_runs(limit)})
            elif path == "/api/datasets":
                send_json(self, {"datasets": list_datasets()})
            elif path.startswith("/api/datasets/") and path.endswith("/export"):
                dataset_id = path.split("/api/datasets/")[1].split("/export")[0]
                dataset = get_dataset(dataset_id)
                if not dataset:
                    send_json(self, {"error": "Dataset not found"}, 404)
                    return
                send_json(self, {"dataset": export_dataset(dataset)})
            elif path.startswith("/api/datasets/"):
                dataset_id = path.split("/api/datasets/")[1]
                dataset = get_dataset(dataset_id)
                if not dataset:
                    send_json(self, {"error": "Dataset not found"}, 404)
                    return
                send_json(self, {"dataset": dataset})
            elif path == "/api/eval-policies":
                send_json(
                    self,
                    {"policies": list_eval_policies(), "defaults": DEFAULT_GATES},
                )
            elif path == "/api/evaluators":
                send_json(
                    self,
                    {"evaluators": list_evaluators(), "builtins": builtin_evaluators()},
                )
            elif path == "/api/issues":
                status = params.get("status", [None])[0]
                send_json(self, {"issues": list_issues(status)})
            elif path.startswith("/api/issues/"):
                issue_id = path.split("/api/issues/")[1]
                issue = get_issue(issue_id)
                if not issue:
                    send_json(self, {"error": "Issue not found"}, 404)
                    return
                send_json(self, {"issue": issue})
            elif path == "/api/annotations":
                send_json(
                    self,
                    {
                        "annotations": list_annotations(
                            params.get("target_type", [None])[0],
                            params.get("target_id", [None])[0],
                        ),
                    },
                )
            elif path == "/api/product-roadmap":
                send_json(self, product_roadmap())
            elif path.startswith("/api/reports/"):
                run_id = path.split("/api/reports/")[1]
                run = get_run_by_id(run_id)
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                run_body = run["trace"]
                stored = run_body.get("evaluation", {})
                eval_report = stored.get(
                    "eval_report",
                ) or evaluate_with_configured_evaluators(run_body)
                gate = stored.get("gate") or EvalPolicy().evaluate(run_body).to_dict()
                report_issue_signatures = {
                    finding.get("signature")
                    for finding in eval_report.get("findings", [])
                    if not finding.get("passed") and finding.get("signature")
                }
                issues = [
                    issue
                    for issue in list_issues()
                    if issue.get("signature") in report_issue_signatures
                ]
                report = build_release_report(run_body, gate, eval_report, issues)
                if params.get("format", ["json"])[0] == "md":
                    send_json(
                        self,
                        {
                            "markdown": render_markdown_report(report, issues),
                            "report": report,
                        },
                    )
                else:
                    send_json(self, {"report": report, "issues": issues})
            elif path == "/api/runs/diff":
                run_a_id = params.get("a", [None])[0]
                run_b_id = params.get("b", [None])[0]
                if not run_a_id or not run_b_id:
                    send_json(self, {"error": "Need both a and b"}, 400)
                    return
                runs = list_runs(100)
                run_a = next((r for r in runs if r["id"] == run_a_id), None)
                run_b = next((r for r in runs if r["id"] == run_b_id), None)
                if not run_a or not run_b:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                diff = ReplayEngine.diff_runs(run_a["trace"], run_b["trace"])
                send_json(self, {"diff": diff})
            elif path.startswith("/api/runs/") and path.endswith("/otel"):
                run_id = path.split("/api/runs/")[1].split("/otel")[0]
                run = get_run_by_id(run_id)
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                send_json(self, {"spans": run_to_otel_spans(run["trace"])})
            elif path.startswith("/api/runs/") and not path.endswith("/diff"):
                run_id = path.split("/api/runs/")[1].split("/")[0]
                run = get_run_by_id(run_id)
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                send_json(self, {"run": run})
            elif path.startswith("/api/coverage/"):
                agent_id = path.split("/api/coverage/")[1]
                cov = get_coverage(agent_id)
                if not cov:
                    send_json(self, {"error": "No coverage data for this agent"}, 404)
                    return
                send_json(self, {"coverage": cov})
            else:
                super().do_GET()
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
            send_json(self, {"error": str(exc)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/agents":
                payload = read_json(self)
                config = payload.get("config") or payload
                name = config.get("name", "Untitled Agent")
                description = config.get("description", "")
                agent_id = name.lower().replace(" ", "-") + "-" + uuid.uuid4().hex[:6]
                upsert_agent(agent_id, name, description, config, models.iso_now())
                send_json(
                    self,
                    {
                        "agent": {
                            "id": agent_id,
                            "name": name,
                            "description": description,
                            "config": config,
                        },
                    },
                    201,
                )
            elif path == "/api/agents/import":
                payload = read_json(self)
                file_path = payload.get("path", "")
                if not file_path:
                    send_json(self, {"error": "Missing 'path' field"}, 400)
                    return
                agent_id, name, description, config = _import_agent_from_path(file_path)
                upsert_agent(agent_id, name, description, config, models.iso_now())
                send_json(
                    self,
                    {
                        "agent": {
                            "id": agent_id,
                            "name": name,
                            "description": description,
                            "config": config,
                        },
                    },
                    201,
                )
            elif path == "/api/runs":
                payload = read_json(self)
                agent_id = payload.get("agent_id", self._get_default_agent_id())
                scenario_count = int(payload.get("scenario_count", 100))
                agent_data = get_agent(agent_id)
                if not agent_data:
                    send_json(self, {"error": "Agent not found"}, 404)
                    return
                agent_config = models.AgentConfig.from_dict(agent_data["config"])
                agent_type = payload.get(
                    "agent_type",
                    agent_data["config"].get("agent_type", "customer_support"),
                )
                dataset_id = payload.get("dataset_id")
                if dataset_id:
                    scenarios, dataset = _load_dataset_scenarios(dataset_id)
                    if not dataset:
                        send_json(self, {"error": "Dataset not found"}, 404)
                        return
                else:
                    gen = ScenarioGenerator()
                    scenarios = gen.generate_all(
                        agent_type=agent_type,
                        count=scenario_count,
                    )
                result = RunPipeline().run_simulation(
                    agent_id=agent_id,
                    agent_config=agent_config,
                    scenarios=scenarios,
                    agent_type=agent_type,
                    scenario_count=scenario_count,
                    seed=int(payload.get("seed", 42)),
                    evaluators=payload.get("evaluators"),
                    gates=payload.get("gates"),
                )
                send_json(self, result.response_body(), 201)
            elif path == "/api/runs/live":
                payload = read_json(self)
                agent_id = payload.get("agent_id", self._get_default_agent_id())
                endpoint = payload.get("endpoint", "")
                if not endpoint:
                    send_json(
                        self,
                        {"error": "Missing 'endpoint' field for live agent connection"},
                        400,
                    )
                    return
                scenario_count = int(payload.get("scenario_count", 10))
                agent_type = payload.get("agent_type", "customer_support")
                gen = ScenarioGenerator()
                scenarios = gen.generate_all(
                    agent_type=agent_type,
                    count=scenario_count,
                )

                from .adapters.http_adapter import HttpAdapter

                adapter = HttpAdapter(endpoint=endpoint)
                results: list[dict] = []
                for sc in scenarios:
                    result = adapter.run_scenario(sc)
                    results.append(result)

                passed = sum(1 for r in results if r["passed"])
                total = len(results)
                run_id = "live-" + uuid.uuid4().hex[:10]
                live_run = {
                    "id": run_id,
                    "agent_id": agent_id,
                    "score": round(passed / max(total, 1) * 100),
                    "status": "passed"
                    if passed / max(total, 1) >= 0.8
                    else "needs_review",
                    "summary": f"Live test: {passed}/{total} scenarios passed",
                    "total_cost": 0.0,
                    "results": results,
                    "scenario_count": total,
                    "passed_count": passed,
                    "failed_count": total - passed,
                }
                result = RunPipeline().finalize_run(
                    run_body=live_run,
                    agent_id=agent_id,
                    evaluators=payload.get("evaluators"),
                    gates=payload.get("gates"),
                )
                send_json(self, result.response_body(), 201)
            elif path.startswith("/api/runs/") and path.endswith("/replay"):
                run_id = path.split("/api/runs/")[1].split("/replay")[0]
                run = get_run_by_id(run_id)
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                agent_id = run.get("agent_id", "")
                agent_data = get_agent(agent_id)
                if not agent_data:
                    send_json(self, {"error": "Agent not found"}, 404)
                    return
                agent_config = models.AgentConfig.from_dict(agent_data["config"])
                results = run["trace"].get("results", [])
                scenario_defs: list = []
                for r in results:
                    name = r.get("scenario_name", "")
                    stype = r.get("scenario_type", "happy_path")
                    desc = r.get("scenario_name", "")
                    scenario_defs.append(
                        models.ScenarioDefinition(
                            name=name,
                            scenario_type=models.ScenarioType(stype),
                            description=desc,
                            user_prompt=name,
                        ),
                    )
                engine = SimulationEngine(agent_config, scenario_defs, seed=42)
                new_run = engine.run()
                save_run(
                    new_run.id,
                    agent_id,
                    new_run.score,
                    new_run.status,
                    new_run.summary,
                    new_run.to_dict(),
                    models.iso_now(),
                )
                diff = ReplayEngine.diff_runs(run["trace"], new_run.to_dict())
                send_json(self, {"replay": new_run.to_dict(), "diff": diff}, 201)
            elif path == "/api/datasets/from-run":
                payload = read_json(self)
                run_id = payload.get("run_id", "")
                run = get_run_by_id(run_id)
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                dataset_id = payload.get("dataset_id") or "ds-" + uuid.uuid4().hex[:10]
                now = models.iso_now()
                create_dataset(
                    dataset_id,
                    payload.get("name", f"Regression dataset from {run_id}"),
                    payload.get("description", "Failures promoted from Ozark traces."),
                    "trace_to_dataset",
                    {"source_run_id": run_id},
                    now,
                )
                min_score = int(payload.get("max_score", 99))
                only_failed = bool(payload.get("only_failed", True))
                added = 0
                for result in run["trace"].get("results", []):
                    if only_failed and result.get("passed"):
                        continue
                    if result.get("score", 100) > min_score:
                        continue
                    scenario = scenario_from_result(result, run_id)
                    tags = [
                        "regression",
                        result.get("scenario_type", "custom"),
                        scenario.get("difficulty", "medium"),
                    ]
                    add_dataset_item(
                        "item-" + uuid.uuid4().hex[:10],
                        dataset_id,
                        scenario,
                        run_id,
                        result.get("scenario_name", ""),
                        tags,
                        now,
                    )
                    added += 1
                send_json(
                    self,
                    {"dataset": get_dataset(dataset_id), "added": added},
                    201,
                )
            elif path == "/api/datasets/from-issue":
                payload = read_json(self)
                issue = get_issue(payload.get("issue_id", ""))
                if not issue:
                    send_json(self, {"error": "Issue not found"}, 404)
                    return
                run = get_run_by_id(issue["last_seen_run_id"])
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                dataset_id = payload.get("dataset_id") or "ds-" + uuid.uuid4().hex[:10]
                now = models.iso_now()
                create_dataset(
                    dataset_id,
                    payload.get("name", f"Issue regression: {issue['title']}"),
                    payload.get(
                        "description",
                        "Regression dataset promoted from a grouped issue.",
                    ),
                    "issue_to_dataset",
                    {"issue_id": issue["id"], "source_run_id": run["id"]},
                    now,
                )
                added = 0
                finding = issue.get("metadata", {}).get("last_finding", {})
                target_scenario = finding.get("metadata", {}).get("scenario_name", "")
                for result in run["trace"].get("results", []):
                    if target_scenario:
                        if result.get("scenario_name") != target_scenario:
                            continue
                    elif result.get("passed"):
                        continue
                    scenario = scenario_from_result(result, run["id"])
                    tags = _dataset_issue_tags(issue, scenario)
                    add_dataset_item(
                        "item-" + uuid.uuid4().hex[:10],
                        dataset_id,
                        scenario,
                        run["id"],
                        result.get("scenario_name", ""),
                        tags,
                        now,
                    )
                    added += 1
                if added == 0:
                    failed_result = next(
                        (
                            result
                            for result in run["trace"].get("results", [])
                            if not result.get("passed")
                        ),
                        None,
                    )
                    if failed_result:
                        scenario = scenario_from_result(failed_result, run["id"])
                        tags = _dataset_issue_tags(issue, scenario)
                        add_dataset_item(
                            "item-" + uuid.uuid4().hex[:10],
                            dataset_id,
                            scenario,
                            run["id"],
                            failed_result.get("scenario_name", ""),
                            tags,
                            now,
                        )
                        added = 1
                send_json(
                    self,
                    {"dataset": get_dataset(dataset_id), "added": added},
                    201,
                )
            elif path == "/api/datasets/import":
                payload = read_json(self)
                pack = (
                    load_dataset_pack(payload["path"])
                    if payload.get("path")
                    else payload.get("dataset", {})
                )
                dataset_id = (
                    payload.get("dataset_id")
                    or pack.get("id")
                    or "ds-" + uuid.uuid4().hex[:10]
                )
                now = models.iso_now()
                create_dataset(
                    dataset_id,
                    pack.get("name", "Imported dataset"),
                    pack.get("description", ""),
                    pack.get("source", "dataset_import"),
                    pack.get("metadata", {}),
                    now,
                )
                added = 0
                for item in pack.get("items", []):
                    add_dataset_item(
                        "item-" + uuid.uuid4().hex[:10],
                        dataset_id,
                        item["scenario"],
                        item.get("source_run_id", ""),
                        item.get("source_result_name", ""),
                        item.get("tags", ["imported"]),
                        now,
                    )
                    added += 1
                send_json(
                    self,
                    {"dataset": get_dataset(dataset_id), "added": added},
                    201,
                )
            elif path == "/api/eval-policies":
                payload = read_json(self)
                policy_id = payload.get("id") or "policy-" + uuid.uuid4().hex[:8]
                upsert_eval_policy(
                    policy_id,
                    payload.get("name", "Release gate"),
                    payload.get("gates", DEFAULT_GATES),
                    models.iso_now(),
                )
                send_json(self, {"policy": get_eval_policy(policy_id)}, 201)
            elif path == "/api/evaluators":
                payload = read_json(self)
                evaluator_id = payload.get("id") or "eval-" + uuid.uuid4().hex[:8]
                upsert_evaluator(
                    evaluator_id,
                    payload.get("name", "Custom evaluator"),
                    payload.get("type", "regex"),
                    payload.get("config", {}),
                    models.iso_now(),
                )
                send_json(self, {"evaluator": get_evaluator(evaluator_id)}, 201)
            elif path == "/api/experiments":
                payload = read_json(self)
                agent_ids = payload.get("agent_ids", [])
                if not agent_ids:
                    send_json(self, {"error": "Missing agent_ids"}, 400)
                    return
                agents = []
                for agent_id in agent_ids:
                    agent_data = get_agent(agent_id)
                    if not agent_data:
                        send_json(self, {"error": f"Agent not found: {agent_id}"}, 404)
                        return
                    agents.append(
                        {
                            "id": agent_id,
                            "config": models.AgentConfig.from_dict(
                                agent_data["config"],
                            ),
                        },
                    )
                dataset_id = payload.get("dataset_id")
                if dataset_id:
                    scenarios, dataset = _load_dataset_scenarios(dataset_id)
                    if not dataset:
                        send_json(self, {"error": "Dataset not found"}, 404)
                        return
                else:
                    gen = ScenarioGenerator()
                    scenarios = gen.generate_all(
                        agent_type=payload.get("agent_type", "customer_support"),
                        count=int(payload.get("scenario_count", 25)),
                    )
                experiment = run_experiment_matrix(
                    agents,
                    scenarios,
                    list_evaluators() or builtin_evaluators(),
                    payload.get("gates"),
                    int(payload.get("seed", 42)),
                )
                for variant in experiment["variants"]:
                    run = variant["run"]
                    run["experiment"] = {
                        "variant_id": variant["variant_id"],
                        "gate": variant["gate"],
                        "eval_report": variant["eval_report"],
                    }
                    save_run(
                        run["id"],
                        variant["variant_id"],
                        run["score"],
                        run["status"],
                        run["summary"],
                        run,
                        models.iso_now(),
                    )
                send_json(self, {"experiment": experiment}, 201)
            elif path == "/api/ingest/traces":
                payload = read_json(self)
                trace_payload = (
                    load_trace_payload(payload["path"])
                    if payload.get("path")
                    else payload.get("trace", payload)
                )
                agent_id = payload.get("agent_id", "production-import")
                run_body = normalize_payload(
                    trace_payload,
                    agent_id,
                    payload.get("agent_name", "Production Agent"),
                )
                result = RunPipeline().finalize_run(
                    run_body=run_body,
                    agent_id=agent_id,
                    evaluators=payload.get("evaluators"),
                    gates=payload.get("gates"),
                )
                send_json(
                    self,
                    {
                        "run": result.run,
                        "eval_report": result.eval_report,
                        "issues": result.issues,
                    },
                    201,
                )
            elif path.startswith("/api/runs/") and path.endswith("/evaluate"):
                payload = read_json(self)
                run_id = path.split("/api/runs/")[1].split("/evaluate")[0]
                run = get_run_by_id(run_id)
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                eval_report = evaluate_with_configured_evaluators(
                    run["trace"],
                    payload.get("evaluators"),
                )
                issues = record_issues(run["trace"], eval_report)
                send_json(self, {"eval_report": eval_report, "issues": issues})
            elif path.startswith("/api/issues/") and path.endswith("/status"):
                payload = read_json(self)
                issue_id = path.split("/api/issues/")[1].split("/status")[0]
                update_issue_status(
                    issue_id,
                    payload.get("status", "open"),
                    models.iso_now(),
                )
                send_json(self, {"issue": get_issue(issue_id)})
            elif path == "/api/annotations":
                payload = read_json(self)
                annotation_id = payload.get("id") or "ann-" + uuid.uuid4().hex[:10]
                add_annotation(
                    annotation_id,
                    payload.get("target_type", "run"),
                    payload.get("target_id", ""),
                    payload.get("label", "reviewed"),
                    payload.get("score"),
                    payload.get("comment", ""),
                    models.iso_now(),
                )
                send_json(
                    self,
                    {
                        "annotations": list_annotations(
                            payload.get("target_type"),
                            payload.get("target_id"),
                        ),
                    },
                    201,
                )
            elif path.startswith("/api/runs/") and path.endswith("/gate"):
                payload = read_json(self)
                run_id = path.split("/api/runs/")[1].split("/gate")[0]
                run = get_run_by_id(run_id)
                if not run:
                    send_json(self, {"error": "Run not found"}, 404)
                    return
                policy = get_eval_policy(payload.get("policy_id", ""))
                gates = payload.get("gates") or (policy or {}).get("gates")
                gate_result = EvalPolicy(gates).evaluate(run["trace"])
                send_json(self, {"gate": gate_result.to_dict()})
            elif path == "/api/scenarios/custom":
                payload = read_json(self)
                templates = payload.get("templates", [])
                pack_path = payload.get("pack_path", "")
                gen = ScenarioGenerator()
                if pack_path:
                    from .engine.scenario_loader import ScenarioLoader

                    custom = ScenarioLoader.load_custom_pack(pack_path)
                    all_scenarios: list = []
                    for agent_type, tmpl_list in custom.items():
                        for tmpl in tmpl_list:
                            all_scenarios.append(
                                _scenario_from_template(tmpl, agent_type),
                            )
                    send_json(
                        self,
                        {
                            "scenarios": [s.to_dict() for s in all_scenarios],
                            "count": len(all_scenarios),
                        },
                        201,
                    )
                else:
                    all_scenarios: list = []
                    for tmpl in templates:
                        all_scenarios.append(_scenario_from_template(tmpl))
                    send_json(
                        self,
                        {
                            "scenarios": [s.to_dict() for s in all_scenarios],
                            "count": len(all_scenarios),
                        },
                        201,
                    )
            else:
                send_json(self, {"error": "Not found"}, 404)
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
            LOGGER.exception("Request failed")
            send_json(self, {"error": str(exc)}, 500)


def main() -> None:
    bootstrap()
    port = int(os.environ.get("PORT", "8787"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    LOGGER.info("Ozark v2.0 running at http://127.0.0.1:%s", port)
    server.serve_forever()


if __name__ == "__main__":
    main()
