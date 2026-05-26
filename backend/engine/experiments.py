from typing import Any

from .eval_policy import EvalPolicy
from .evaluators import EvaluatorRunner
from .simulator import SimulationEngine


def run_experiment_matrix(agent_configs: list[dict[str, Any]], scenarios: list,
                          evaluators: list[dict[str, Any]], gates: dict[str, Any] | None = None,
                          seed: int = 42) -> dict[str, Any]:
    variants = []
    for item in agent_configs:
        variant_id = item["id"]
        agent = item["config"]
        run = SimulationEngine(agent, scenarios, seed=seed).run().to_dict()
        eval_report = EvaluatorRunner(evaluators).evaluate_run(run)
        gate = EvalPolicy(gates).evaluate(run).to_dict()
        variants.append({
            "variant_id": variant_id,
            "agent_name": agent.name,
            "run": run,
            "gate": gate,
            "eval_report": eval_report,
        })
    baseline = variants[0] if variants else None
    return {
        "baseline_variant_id": baseline["variant_id"] if baseline else None,
        "variants": variants,
        "comparison": [_compare_variant(baseline, variant) for variant in variants] if baseline else [],
    }


def _compare_variant(baseline: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    base_run = baseline["run"]
    run = variant["run"]
    return {
        "variant_id": variant["variant_id"],
        "score": run.get("score", 0),
        "score_delta": run.get("score", 0) - base_run.get("score", 0),
        "failed_count": run.get("failed_count", 0),
        "failed_delta": run.get("failed_count", 0) - base_run.get("failed_count", 0),
        "eval_failed_count": variant["eval_report"].get("failed_count", 0),
        "gate_passed": variant["gate"].get("passed", False),
        "decision": "winner" if variant["gate"].get("passed") and run.get("score", 0) >= base_run.get("score", 0) else "review",
    }
