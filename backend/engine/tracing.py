import hashlib
import json

from ..models import TraceEvent


class TraceRecorder:

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.events: list[TraceEvent] = []
        self.checksums: list[str] = []

    def record(self, event: TraceEvent):
        self.events.append(event)
        self._checksum_event(event)

    def _checksum_event(self, event: TraceEvent):
        serialized = json.dumps(event.to_dict(), sort_keys=True, default=str)
        self.checksums.append(hashlib.sha256(serialized.encode()).hexdigest()[:12])

    def get_trace(self) -> list[TraceEvent]:
        return list(self.events)

    def get_fingerprint(self) -> str:
        return hashlib.sha256("".join(self.checksums).encode()).hexdigest()[:16]

    def reset(self):
        self.events = []
        self.checksums = []


class ReplayEngine:

    @staticmethod
    def diff_runs(run_a: dict, run_b: dict) -> dict:
        """Compute regression diff between two simulation runs."""
        results_a = {r.get("scenario_name", r.get("scenario", "")): r for r in run_a.get("results", run_a.get("trace", {}).get("results", []))}
        results_b = {r.get("scenario_name", r.get("scenario", "")): r for r in run_b.get("results", run_b.get("trace", {}).get("results", []))}

        diffs = []
        for name in set(results_a.keys()) | set(results_b.keys()):
            ra = results_a.get(name)
            rb = results_b.get(name)
            if not ra:
                diffs.append({"scenario": name, "change": "removed", "detail": "Scenario was present in run A but missing in run B"})
            elif not rb:
                diffs.append({"scenario": name, "change": "added", "detail": "Scenario was not in run A but appears in run B"})
            else:
                score_delta = rb.get("score", 0) - ra.get("score", 0)
                passed_a = ra.get("passed", True)
                passed_b = rb.get("passed", True)
                if passed_a != passed_b:
                    diffs.append({"scenario": name, "change": "regression" if passed_a and not passed_b else "improvement",
                                  "score_a": ra.get("score"), "score_b": rb.get("score"),
                                  "detail": f"Went from {'pass' if passed_a else 'fail'} to {'pass' if passed_b else 'fail'}"})
                elif abs(score_delta) >= 10:
                    diffs.append({"scenario": name, "change": "score_shift",
                                  "score_a": ra.get("score"), "score_b": rb.get("score"),
                                  "detail": f"Score changed by {score_delta:+d} points"})
                tools_a = set(ra.get("called_tools", []))
                tools_b = set(rb.get("called_tools", []))
                if tools_a != tools_b:
                    added = tools_b - tools_a
                    removed = tools_a - tools_b
                    detail = []
                    if added:
                        detail.append(f"Added tools: {', '.join(sorted(added))}")
                    if removed:
                        detail.append(f"Removed tools: {', '.join(sorted(removed))}")
                    diffs.append({"scenario": name, "change": "tool_change", "detail": "; ".join(detail)})

        overall_a = run_a.get("score", 0)
        overall_b = run_b.get("score", 0)
        return {
            "score_delta": overall_b - overall_a,
            "scenario_diffs": diffs,
            "regression_count": sum(1 for d in diffs if d["change"] == "regression"),
            "improvement_count": sum(1 for d in diffs if d["change"] == "improvement"),
            "total_changes": len(diffs),
            "summary": f"{overall_b - overall_a:+d}pts: {sum(1 for d in diffs if d['change'] == 'regression')} regressions, {sum(1 for d in diffs if d['change'] == 'improvement')} improvements across {len(diffs)} changes",
        }
