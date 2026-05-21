from dataclasses import dataclass, field
from typing import Any


@dataclass
class CoverageReport:
    tool_coverage: dict[str, bool] = field(default_factory=dict)
    tool_combinations: dict[str, int] = field(default_factory=dict)
    path_coverage: dict[str, bool] = field(default_factory=dict)
    guardrail_coverage: dict[str, int] = field(default_factory=dict)
    state_coverage: dict[str, bool] = field(default_factory=dict)
    transition_coverage: dict[str, bool] = field(default_factory=dict)
    missing_scenarios: list[str] = field(default_factory=list)
    heatmap_data: dict[str, list[dict]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tool_coverage": self.tool_coverage,
            "tool_combinations": self.tool_combinations,
            "path_coverage": self.path_coverage,
            "guardrail_coverage": self.guardrail_coverage,
            "state_coverage": self.state_coverage,
            "transition_coverage": self.transition_coverage,
            "missing_scenarios": self.missing_scenarios,
            "heatmap_data": self.heatmap_data,
        }

    def coverage_percentage(self) -> dict[str, float]:
        result: dict[str, float] = {}
        if self.tool_coverage:
            result["tools"] = sum(1 for v in self.tool_coverage.values() if v) / max(len(self.tool_coverage), 1) * 100
        if self.path_coverage:
            result["paths"] = sum(1 for v in self.path_coverage.values() if v) / max(len(self.path_coverage), 1) * 100
        if self.state_coverage:
            result["states"] = sum(1 for v in self.state_coverage.values() if v) / max(len(self.state_coverage), 1) * 100
        if self.transition_coverage:
            result["transitions"] = sum(1 for v in self.transition_coverage.values() if v) / max(len(self.transition_coverage), 1) * 100
        return result


class CoverageAnalyzer:

    def __init__(self, all_tools: list[str] | None = None, all_states: list[str] | None = None,
                 all_transitions: list[str] | None = None, all_guardrails: list[str] | None = None):
        self.all_tools = all_tools or []
        self.all_states = all_states or []
        self.all_transitions = all_transitions or []
        self.all_guardrails = all_guardrails or []
        self.tool_hits: dict[str, int] = {}
        self.tool_combos: dict[str, int] = {}
        self.path_hits: dict[str, int] = {}
        self.guardrail_hits: dict[str, int] = {}
        self.state_hits: dict[str, int] = {}
        self.transition_hits: dict[str, int] = {}
        self.total_runs: int = 0

    def record_tool_call(self, tool: str) -> None:
        self.tool_hits[tool] = self.tool_hits.get(tool, 0) + 1

    def record_tool_combination(self, tools: list[str]) -> None:
        key = "+".join(sorted(tools))
        self.tool_combos[key] = self.tool_combos.get(key, 0) + 1

    def record_path(self, path: str) -> None:
        self.path_hits[path] = self.path_hits.get(path, 0) + 1

    def record_guardrail(self, guardrail: str) -> None:
        self.guardrail_hits[guardrail] = self.guardrail_hits.get(guardrail, 0) + 1

    def record_state(self, state: str) -> None:
        self.state_hits[state] = self.state_hits.get(state, 0) + 1

    def record_transition(self, from_state: str, to_state: str) -> None:
        key = f"{from_state}->{to_state}"
        self.transition_hits[key] = self.transition_hits.get(key, 0) + 1

    def record_run(self) -> None:
        self.total_runs += 1

    def generate_report(self) -> CoverageReport:
        tool_coverage: dict[str, bool] = {}
        for t in self.all_tools:
            tool_coverage[t] = self.tool_hits.get(t, 0) > 0

        path_coverage: dict[str, bool] = {}
        for p in self.all_guardrails:
            path_coverage[p] = self.guardrail_hits.get(p, 0) > 0

        guardrail_coverage: dict[str, int] = {}
        for g in self.all_guardrails:
            guardrail_coverage[g] = self.guardrail_hits.get(g, 0)

        state_coverage: dict[str, bool] = {}
        for s in self.all_states:
            state_coverage[s] = self.state_hits.get(s, 0) > 0

        transition_coverage: dict[str, bool] = {}
        for t in self.all_transitions:
            transition_coverage[t] = self.transition_hits.get(t, 0) > 0

        missing = self._identify_gaps()

        heatmap = self._build_heatmap(tool_coverage, guardrail_coverage)

        return CoverageReport(
            tool_coverage=tool_coverage,
            tool_combinations=dict(sorted(self.tool_combos.items())),
            path_coverage=path_coverage,
            guardrail_coverage=guardrail_coverage,
            state_coverage=state_coverage,
            transition_coverage=transition_coverage,
            missing_scenarios=missing,
            heatmap_data=heatmap,
        )

    def _identify_gaps(self) -> list[str]:
        gaps: list[str] = []
        untested_tools = [t for t in self.all_tools if self.tool_hits.get(t, 0) == 0]
        if untested_tools:
            gaps.append(f"Untested tools: {', '.join(sorted(untested_tools))}")
        uncovered_states = [s for s in self.all_states if self.state_hits.get(s, 0) == 0]
        if uncovered_states:
            gaps.append(f"Unvisited states: {', '.join(sorted(uncovered_states))}")
        uncovered_transitions = [t for t in self.all_transitions if self.transition_hits.get(t, 0) == 0]
        if uncovered_transitions:
            gaps.append(f"Untested transitions: {', '.join(sorted(uncovered_transitions))[:100]}")
        return gaps

    def _build_heatmap(self, tool_cov: dict[str, bool], guard_cov: dict[str, int]) -> dict[str, list[dict]]:
        heatmap: dict[str, list[dict]] = {}
        tool_entries: list[dict] = []
        for tool, covered in tool_cov.items():
            count = self.tool_hits.get(tool, 0)
            tool_entries.append({
                "name": tool,
                "covered": covered,
                "count": count,
                "intensity": min(1.0, count / max(self.total_runs, 1)),
            })
        heatmap["tools"] = tool_entries

        guard_entries: list[dict] = []
        max_guard = max(guard_cov.values()) if guard_cov.values() else 1
        for guard, count in guard_cov.items():
            guard_entries.append({
                "name": guard,
                "count": count,
                "intensity": count / max(max_guard, 1),
            })
        heatmap["guardrails"] = guard_entries
        return heatmap
