from typing import Any


GENAI_SYSTEM = "ozark"


def run_to_otel_spans(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Export Ozark traces as OpenTelemetry-shaped spans with GenAI attributes.

    The schema follows the production pattern used by modern LLM observability tools:
    one root agent run span, child scenario spans, then child tool/LLM spans.
    """
    spans: list[dict[str, Any]] = []
    trace_id = run.get("id", "")
    root_id = f"{trace_id}:root"
    spans.append({
        "trace_id": trace_id,
        "span_id": root_id,
        "parent_span_id": None,
        "name": "ozark.simulation_run",
        "kind": "INTERNAL",
        "attributes": {
            "gen_ai.system": GENAI_SYSTEM,
            "gen_ai.operation.name": "agent.eval",
            "gen_ai.agent.name": run.get("agent_name", ""),
            "ozark.score": run.get("score", 0),
            "ozark.status": run.get("status", ""),
            "ozark.scenario_count": run.get("scenario_count", 0),
        },
    })

    for index, result in enumerate(run.get("results", []), start=1):
        scenario_id = f"{trace_id}:scenario:{index}"
        spans.append({
            "trace_id": trace_id,
            "span_id": scenario_id,
            "parent_span_id": root_id,
            "name": f"ozark.scenario.{result.get('scenario_type', 'custom')}",
            "kind": "INTERNAL",
            "attributes": {
                "gen_ai.system": GENAI_SYSTEM,
                "gen_ai.operation.name": "agent.scenario",
                "ozark.scenario.name": result.get("scenario_name", ""),
                "ozark.scenario.score": result.get("score", 0),
                "ozark.scenario.passed": result.get("passed", False),
            },
        })
        for event_index, event in enumerate(result.get("trace", []), start=1):
            kind = event.get("kind", "event")
            spans.append({
                "trace_id": trace_id,
                "span_id": f"{scenario_id}:event:{event_index}",
                "parent_span_id": scenario_id,
                "name": _span_name(kind, event),
                "kind": "CLIENT" if kind == "tool" else "INTERNAL",
                "attributes": _event_attributes(event, result),
            })
    return spans


def _span_name(kind: str, event: dict[str, Any]) -> str:
    if kind == "tool":
        return f"gen_ai.tool.{event.get('tool', 'unknown')}"
    if kind == "assistant":
        return "gen_ai.chat.completion"
    if kind == "user":
        return "gen_ai.user.message"
    return f"ozark.trace.{kind}"


def _event_attributes(event: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    attrs = {
        "gen_ai.system": GENAI_SYSTEM,
        "gen_ai.operation.name": "execute_tool" if event.get("kind") == "tool" else "chat",
        "ozark.scenario.name": result.get("scenario_name", ""),
        "ozark.event.kind": event.get("kind", ""),
        "ozark.event.step": event.get("step", 0),
        "ozark.event.latency_ms": event.get("latency_ms", 0),
        "ozark.event.cost": event.get("cost", 0.0),
    }
    if event.get("tool"):
        attrs["gen_ai.tool.name"] = event["tool"]
        attrs["ozark.tool.risk"] = event.get("risk", "low")
    if event.get("content"):
        attrs["gen_ai.prompt"] = str(event["content"])
    return attrs
