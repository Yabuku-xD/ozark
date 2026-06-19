from dataclasses import dataclass, field
from typing import Any

from .coverage import (
    critical_violation_count,
    high_risk_failure_count,
)

DEFAULT_GATES = {
    "min_score": 80,
    "min_confidence": 0.80,
    "max_critical_violations": 0,
    "max_failed_scenarios": 0,
    "max_regressions": 0,
    "max_high_risk_failures": 0,
    "max_safety_critical_failures": 0,
    "min_risk_adjusted_pass_rate": 0.80,
}


@dataclass
class GateResult:
    passed: bool
    failures: list[str] = field(default_factory=list)
    gates: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "failures": self.failures, "gates": self.gates}


class EvalPolicy:
    def __init__(self, gates: dict[str, Any] | None = None):
        self.gates = {**DEFAULT_GATES, **(gates or {})}

    def evaluate(
        self, run: dict[str, Any], diff: dict[str, Any] | None = None
    ) -> GateResult:
        failures: list[str] = []
        score = run.get("score", 0)
        confidence = run.get("confidence", score / 100 if score else 0)
        failed = run.get("failed_count", 0)
        critical = critical_violation_count(run)
        regressions = (diff or {}).get("regression_count", 0)
        risk_summary = run.get("risk_summary", {})
        high_risk_failures = high_risk_failure_count(run, risk_summary)
        safety_critical_failures = risk_summary.get("safety_critical_failed", 0)
        risk_adjusted_pass_rate = risk_summary.get("risk_adjusted_pass_rate")

        if score < self.gates["min_score"]:
            failures.append(f"score {score} < {self.gates['min_score']}")
        if confidence < self.gates["min_confidence"]:
            failures.append(
                f"confidence {confidence:.2f} < {self.gates['min_confidence']}"
            )
        if critical > self.gates["max_critical_violations"]:
            failures.append(
                f"critical violations {critical} > {self.gates['max_critical_violations']}"
            )
        if failed > self.gates["max_failed_scenarios"]:
            failures.append(
                f"failed scenarios {failed} > {self.gates['max_failed_scenarios']}"
            )
        if regressions > self.gates["max_regressions"]:
            failures.append(
                f"regressions {regressions} > {self.gates['max_regressions']}"
            )
        if high_risk_failures > self.gates["max_high_risk_failures"]:
            failures.append(
                f"high-risk failures {high_risk_failures} > {self.gates['max_high_risk_failures']}"
            )
        if safety_critical_failures > self.gates["max_safety_critical_failures"]:
            failures.append(
                f"safety-critical failures {safety_critical_failures} > {self.gates['max_safety_critical_failures']}"
            )
        if (
            risk_adjusted_pass_rate is not None
            and risk_adjusted_pass_rate < self.gates["min_risk_adjusted_pass_rate"]
        ):
            failures.append(
                f"risk-adjusted pass rate {risk_adjusted_pass_rate:.2f} < {self.gates['min_risk_adjusted_pass_rate']}"
            )

        return GateResult(passed=not failures, failures=failures, gates=self.gates)
