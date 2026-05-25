import json
import logging
import os
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import models
from .db import init_db, upsert_agent, list_agents, get_agent, list_runs, save_run
from .db import get_run_by_id, save_coverage, get_coverage
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
                send_json(self, {"scenarios": [s.to_dict() for s in scenarios], "count": len(scenarios)})
            elif path == "/api/runs":
                limit = int(params.get("limit", ["20"])[0])
                send_json(self, {"runs": list_runs(limit)})
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
                send_json(self, {"agent": {"id": agent_id, "name": name, "description": description, "config": config}}, 201)
            elif path == "/api/agents/import":
                payload = read_json(self)
                file_path = payload.get("path", "")
                if not file_path:
                    send_json(self, {"error": "Missing 'path' field"}, 400)
                    return
                agent_id, name, description, config = _import_agent_from_path(file_path)
                upsert_agent(agent_id, name, description, config, models.iso_now())
                send_json(self, {"agent": {"id": agent_id, "name": name, "description": description, "config": config}}, 201)
            elif path == "/api/runs":
                payload = read_json(self)
                agent_id = payload.get("agent_id", self._get_default_agent_id())
                scenario_count = int(payload.get("scenario_count", 100))
                agent_data = get_agent(agent_id)
                if not agent_data:
                    send_json(self, {"error": "Agent not found"}, 404)
                    return
                agent_config = models.AgentConfig.from_dict(agent_data["config"])
                gen = ScenarioGenerator()
                agent_type = payload.get("agent_type", agent_data["config"].get("agent_type", "customer_support"))
                scenarios = gen.generate_all(agent_type=agent_type, count=scenario_count)
                engine = SimulationEngine(agent_config, scenarios, seed=42)
                run = engine.run()
                save_run(run.id, agent_id, run.score, run.status, run.summary, run.to_dict(), models.iso_now())

                from .engine.coverage import CoverageAnalyzer
                tools = [t.name for t in agent_config.tools]
                guardrails = [g.id for g in agent_config.guardrails]
                cov = CoverageAnalyzer(all_tools=tools, all_guardrails=guardrails)
                for r in run.results:
                    for t in r.called_tools:
                        cov.record_tool_call(t)
                    for v in r.violations:
                        cov.record_guardrail(v.guardrail)
                    cov.record_tool_combination(r.called_tools)
                    cov.record_run()
                report = cov.generate_report()
                save_coverage(agent_id, report.to_dict(), models.iso_now())
                send_json(self, {"run": run.to_dict()}, 201)
            elif path == "/api/runs/live":
                payload = read_json(self)
                agent_id = payload.get("agent_id", self._get_default_agent_id())
                endpoint = payload.get("endpoint", "")
                if not endpoint:
                    send_json(self, {"error": "Missing 'endpoint' field for live agent connection"}, 400)
                    return
                scenario_count = int(payload.get("scenario_count", 10))
                agent_type = payload.get("agent_type", "customer_support")
                gen = ScenarioGenerator()
                scenarios = gen.generate_all(agent_type=agent_type, count=scenario_count)

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
                    "status": "passed" if passed / max(total, 1) >= 0.8 else "needs_review",
                    "summary": f"Live test: {passed}/{total} scenarios passed",
                    "total_cost": 0.0,
                    "results": results,
                    "scenario_count": total,
                    "passed_count": passed,
                    "failed_count": total - passed,
                }
                save_run(run_id, agent_id, live_run["score"], live_run["status"],
                         live_run["summary"], live_run, models.iso_now())
                send_json(self, {"run": live_run}, 201)
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
                    scenario_defs.append(models.ScenarioDefinition(
                        name=name,
                        scenario_type=models.ScenarioType(stype),
                        description=desc,
                        user_prompt=name,
                    ))
                engine = SimulationEngine(agent_config, scenario_defs, seed=42)
                new_run = engine.run()
                save_run(new_run.id, agent_id, new_run.score, new_run.status,
                         new_run.summary, new_run.to_dict(), models.iso_now())
                diff = ReplayEngine.diff_runs(run["trace"], new_run.to_dict())
                send_json(self, {"replay": new_run.to_dict(), "diff": diff}, 201)
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
                            all_scenarios.append(models.ScenarioDefinition(
                                name=tmpl.get("prompt", "")[:60].strip(),
                                scenario_type=models.ScenarioType(tmpl.get("type", "happy_path")),
                                description=tmpl.get("prompt", "")[:200],
                                user_prompt=tmpl.get("prompt", ""),
                                expected_tools=tmpl.get("expected_tools", []),
                                blocked_tools=tmpl.get("blocked_tools", []),
                                sensitive_data=tmpl.get("sensitive_data", False),
                                difficulty=tmpl.get("difficulty", "medium"),
                            ))
                    send_json(self, {"scenarios": [s.to_dict() for s in all_scenarios], "count": len(all_scenarios)}, 201)
                else:
                    all_scenarios: list = []
                    for tmpl in templates:
                        all_scenarios.append(models.ScenarioDefinition(
                            name=tmpl.get("prompt", "")[:60].strip(),
                            scenario_type=models.ScenarioType(tmpl.get("type", "happy_path")),
                            description=tmpl.get("prompt", "")[:200],
                            user_prompt=tmpl.get("prompt", ""),
                            expected_tools=tmpl.get("expected_tools", []),
                            blocked_tools=tmpl.get("blocked_tools", []),
                            sensitive_data=tmpl.get("sensitive_data", False),
                            difficulty=tmpl.get("difficulty", "medium"),
                        ))
                    send_json(self, {"scenarios": [s.to_dict() for s in all_scenarios], "count": len(all_scenarios)}, 201)
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
