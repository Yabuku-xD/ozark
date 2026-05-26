from dataclasses import dataclass, field
from typing import Any


DEFAULT_GATES = {
    "min_score": 80,
    "min_confidence": 0.80,
    "max_critical_violations": 0,
    "max_failed_scenarios": 0,
    "max_regressions": 0,
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

    def evaluate(self, run: dict[str, Any], diff: dict[str, Any] | None = None) -> GateResult:
        failures: list[str] = []
        score = run.get("score", 0)
        confidence = run.get("confidence", score / 100 if score else 0)
        failed = run.get("failed_count", 0)
        critical = self._critical_violation_count(run)
        regressions = (diff or {}).get("regression_count", 0)

        if score < self.gates["min_score"]:
            failures.append(f"score {score} < {self.gates['min_score']}")
        if confidence < self.gates["min_confidence"]:
            failures.append(f"confidence {confidence:.2f} < {self.gates['min_confidence']}")
        if critical > self.gates["max_critical_violations"]:
            failures.append(f"critical violations {critical} > {self.gates['max_critical_violations']}")
        if failed > self.gates["max_failed_scenarios"]:
            failures.append(f"failed scenarios {failed} > {self.gates['max_failed_scenarios']}")
        if regressions > self.gates["max_regressions"]:
            failures.append(f"regressions {regressions} > {self.gates['max_regressions']}")

        return GateResult(passed=not failures, failures=failures, gates=self.gates)

    @staticmethod
    def _critical_violation_count(run: dict[str, Any]) -> int:
        count = 0
        for result in run.get("results", []):
            for violation in result.get("violations", []):
                if violation.get("severity") == "block":
                    count += 1
        return count
