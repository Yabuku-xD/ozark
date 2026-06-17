import sqlite3
from collections.abc import Callable
from typing import Any

from .. import models
from .. import db
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
    for issue in issues:
        db.upsert_issue(issue)
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
        simulation_run = engine.run()
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
