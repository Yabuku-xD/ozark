import re
import uuid
from typing import Any

from ..models import ScenarioDefinition, ScenarioType


def scenario_from_result(result: dict[str, Any], source_run_id: str) -> dict[str, Any]:
    """Create a stable regression scenario from a failed production/simulation result."""
    trace = result.get("trace") or []
    first_user = next((event for event in trace if event.get("kind") == "user"), {})
    prompt = first_user.get("content") or result.get("user_prompt") or result.get("input") or result.get("prompt") or result.get("scenario_name", "Replay failed scenario")
    scenario_type = result.get("scenario_type", "custom")
    try:
        ScenarioType(scenario_type)
    except ValueError:
        scenario_type = ScenarioType.EDGE_CASE.value

    failures = result.get("failures") or []
    violations = result.get("violations") or []
    called_tools = result.get("called_tools") or []
    blocked_tools = [
        tool for tool in called_tools
        if any(v.get("severity") == "block" for v in violations)
    ]

    return ScenarioDefinition(
        name=f"regression/{_slug(result.get('scenario_name', 'scenario'))}-{uuid.uuid4().hex[:6]}",
        scenario_type=ScenarioType(scenario_type),
        description=f"Regression captured from run {source_run_id}: {result.get('scenario_name', 'unnamed')}",
        user_prompt=str(prompt),
        expected_tools=[] if failures or violations else called_tools,
        blocked_tools=blocked_tools,
        expected_outcome="Preserve prior fix: pass without critical violations or unsafe tool calls.",
        turns=max(1, int(result.get("turn_count") or 1)),
        sensitive_data=any(v.get("category") in {"privacy", "security", "content_safety"} for v in violations),
        difficulty=_difficulty(result),
        agent_type="custom",
        metadata={
            "source": "trace_to_dataset",
            "source_run_id": source_run_id,
            "source_result_name": result.get("scenario_name", ""),
            "source_score": result.get("score", 0),
            "source_failures": failures,
            "source_violations": violations,
        },
    ).to_dict()


def scenario_dict_to_definition(scenario: dict[str, Any]) -> ScenarioDefinition:
    data = dict(scenario)
    try:
        data["scenario_type"] = ScenarioType(data.get("scenario_type", "edge_case"))
    except ValueError:
        data["scenario_type"] = ScenarioType.EDGE_CASE
    return ScenarioDefinition.from_dict(data)


def _difficulty(result: dict[str, Any]) -> str:
    violations = result.get("violations") or []
    if any(v.get("severity") == "block" for v in violations):
        return "critical"
    if result.get("passed") is False or result.get("score", 100) < 60:
        return "hard"
    return "medium"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "scenario"
