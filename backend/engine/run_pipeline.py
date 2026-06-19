import sqlite3
import uuid
from collections.abc import Callable
from typing import Any

from .. import db, models
from . import jobs as jobs_mod
from .coverage import build_coverage_report
from .eval_policy import EvalPolicy
from .evaluators import EvaluatorRunner, builtin_evaluators
from .issues import findings_to_issues
from .scenario_gen import ScenarioGenerator
from .simulator import SimulationEngine


class RunPipelineResult:
    def __init__(
        self,
        run: dict[str, Any],
        gate: dict[str, Any],
        eval_report: dict[str, Any],
        issues: list[dict[str, Any]] | None = None,
    ) -> None:
        self.run = run
        self.gate = gate
        self.eval_report = eval_report
        self.issues = issues or []

    def response_body(self) -> dict[str, Any]:
        return {
            "run": self.run,
            "gate": self.gate,
            "eval_report": self.eval_report,
        }


def evaluate_with_configured_evaluators(
    body: dict[str, Any],
    requested: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evaluators = requested or _configured_evaluators() or builtin_evaluators()
    evaluator = EvaluatorRunner(evaluators)
    return evaluator.evaluate_run(body)


def _configured_evaluators() -> list[dict[str, Any]]:
    """Return persisted evaluators, falling back to builtins when the store is unavailable.

    Lets the pipeline run (and be unit-tested) without a bootstrapped database —
    a missing ``evaluators`` table is treated the same as "no custom evaluators
    configured" rather than a fatal error.
    """
    try:
        return db.list_evaluators()
    except sqlite3.OperationalError:
        # Store not bootstrapped (e.g. unit tests calling finalize_run directly);
        # fall through to builtins so evaluation still works.
        return builtin_evaluators()


def record_issues(
    body: dict[str, Any], eval_report: dict[str, Any]
) -> list[dict[str, Any]]:
    issues = findings_to_issues(body, eval_report, db.get_issue_by_signature)
    db.upsert_issues_batch(issues)
    return issues


class RunPipeline:
    def __init__(
        self,
        *,
        now: Callable[[], str] = models.iso_now,
        scenario_generator: ScenarioGenerator | None = None,
    ) -> None:
        self.now = now
        self.scenario_generator = scenario_generator or ScenarioGenerator()

    def run_simulation(
        self,
        *,
        agent_id: str,
        agent_config: models.AgentConfig,
        scenarios: list[models.ScenarioDefinition] | None = None,
        agent_type: str = "customer_support",
        scenario_count: int = 100,
        seed: int = 42,
        evaluators: list[dict[str, Any]] | None = None,
        gates: dict[str, Any] | None = None,
        max_workers: int | None = None,
        progress_fn: "Callable[[int, int], None] | None" = None,
    ) -> RunPipelineResult:
        scenario_defs = (
            scenarios
            if scenarios is not None
            else self.scenario_generator.generate_all(
                agent_type=agent_type,
                count=scenario_count,
            )
        )
        engine = SimulationEngine(
            agent_config,
            scenario_defs,
            seed=seed,
        )
        simulation_run = engine.run(
            max_workers=max_workers, progress_fn=progress_fn
        )
        run_body = simulation_run.to_dict()
        self._save_coverage(agent_id, agent_config, simulation_run.results)
        return self.finalize_run(
            run_body=run_body,
            agent_id=agent_id,
            evaluators=evaluators,
            gates=gates,
        )

    def finalize_run(
        self,
        *,
        run_body: dict[str, Any],
        agent_id: str,
        evaluators: list[dict[str, Any]] | None = None,
        gates: dict[str, Any] | None = None,
    ) -> RunPipelineResult:
        eval_report = evaluate_with_configured_evaluators(run_body, evaluators)
        issues = record_issues(run_body, eval_report)
        gate = EvalPolicy(gates).evaluate(run_body).to_dict()
        finalized_body = {
            **run_body,
            "evaluation": {
                "eval_report": eval_report,
                "gate": gate,
                "issue_signatures": [issue["signature"] for issue in issues],
            },
        }
        db.save_run(
            finalized_body["id"],
            agent_id,
            finalized_body["score"],
            finalized_body["status"],
            finalized_body["summary"],
            finalized_body,
            self.now(),
        )
        return RunPipelineResult(
            run=finalized_body,
            gate=gate,
            eval_report=eval_report,
            issues=issues,
        )

    def _save_coverage(
        self,
        agent_id: str,
        agent_config: models.AgentConfig,
        results: list[models.ScenarioResult],
    ) -> None:
        report = build_coverage_report(agent_config, results)
        db.save_coverage(agent_id, report.to_dict(), self.now())


# ---------------------------------------------------------------------------
# Async job handlers (registered with the job queue on import)
# ---------------------------------------------------------------------------

@jobs_mod.register_handler("run_simulation")
def _handle_run_simulation(
    payload: dict[str, Any], progress_fn: Callable[[int, int], None]
) -> dict[str, Any]:
    """Execute a simulation run in the background.

    Enqueued by ``POST /api/runs`` when ``async=true`` is requested.
    Returns a ``RunPipelineResult.response_body()``-shaped dict.
    """
    from .. import models as _models

    agent_id = payload["agent_id"]
    agent_data = db.get_agent(agent_id)
    if not agent_data:
        raise ValueError(f"Agent not found: {agent_id}")
    agent_config = _models.AgentConfig.from_dict(agent_data["config"])
    agent_type = payload.get(
        "agent_type", agent_data["config"].get("agent_type", "customer_support")
    )

    dataset_id = payload.get("dataset_id")
    if dataset_id:
        from .datasets import scenario_dict_to_definition

        dataset = db.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset not found: {dataset_id}")
        scenarios = [
            scenario_dict_to_definition(item["scenario"])
            for item in dataset["items"]
        ]
    else:
        gen = ScenarioGenerator()
        scenarios = gen.generate_all(
            agent_type=agent_type,
            count=int(payload.get("scenario_count", 100)),
        )

    result = RunPipeline().run_simulation(
        agent_id=agent_id,
        agent_config=agent_config,
        scenarios=scenarios,
        agent_type=agent_type,
        scenario_count=int(payload.get("scenario_count", 100)),
        seed=int(payload.get("seed", 42)),
        evaluators=payload.get("evaluators"),
        gates=payload.get("gates"),
        max_workers=int(payload.get("max_workers", 4)),
        progress_fn=progress_fn,
    )
    return result.response_body()


@jobs_mod.register_handler("run_live")
def _handle_run_live(
    payload: dict[str, Any], progress_fn: Callable[[int, int], None]
) -> dict[str, Any]:
    """Execute a live-agent run in the background."""
    from concurrent.futures import ThreadPoolExecutor

    from ..adapters.http_adapter import HttpAdapter
    from .scenario_gen import ScenarioGenerator

    agent_id = payload["agent_id"]
    endpoint = payload["endpoint"]
    scenario_count = int(payload.get("scenario_count", 10))
    agent_type = payload.get("agent_type", "customer_support")

    gen = ScenarioGenerator()
    scenarios = gen.generate_all(agent_type=agent_type, count=scenario_count)
    adapter = HttpAdapter(endpoint=endpoint)
    max_workers = int(payload.get("max_workers", 4))

    results: list[dict] = [None] * len(scenarios)  # type: ignore[list-item]
    if max_workers > 1 and len(scenarios) > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(adapter.run_scenario, sc): i for i, sc in enumerate(scenarios)}
            for n, future in enumerate(futures, start=1):
                idx = futures[future]
                results[idx] = future.result()
                progress_fn(n, len(scenarios))
    else:
        for i, sc in enumerate(scenarios):
            results[i] = adapter.run_scenario(sc)
            progress_fn(i + 1, len(scenarios))

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    run_id = "live-" + uuid.uuid4().hex[:10]
    live_run = {
        "id": run_id,
        "agent_id": agent_id,
        "score": round(passed / max(total, 1) * 100),
        "score_method": "binary_error",
        "status": "passed" if passed / max(total, 1) >= 0.8 else "needs_review",
        "summary": f"Live test: {passed}/{total} scenarios passed",
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
    return result.response_body()
