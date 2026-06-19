from __future__ import annotations

import random
from typing import Any

GENAI_SYSTEM = "ozark"


def _new_span_id() -> str:
    """Return a 16-byte hex span id (32 hex chars)."""
    return random.randbytes(8).hex()


def run_to_otel_spans(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Export Ozark traces as OpenTelemetry-shaped spans.

    Follows OpenTelemetry GenAI semantic conventions:
      * https://opentelemetry.io/docs/specs/semconv/gen-ai/
      * root span: ``gen_ai.operation.name = agent.eval``
      * scenario span: ``gen_ai.operation.name = chat``
      * tool spans: ``gen_ai.operation.name = execute_tool`` with
        ``gen_ai.tool.name``
      * timing in ``start_time`` / ``end_time`` ISO timestamps
      * 16-byte hex ``span_id`` values
    """
    spans: list[dict[str, Any]] = []
    trace_id = _trace_id_for(run)
    root_id = _new_span_id()
    created_at = run.get("created_at", "")
    spans.append({
        "trace_id": trace_id,
        "span_id": root_id,
        "parent_span_id": None,
        "name": "agent.eval",
        "kind": "INTERNAL",
        "start_time": created_at,
        "end_time": created_at,
        "attributes": {
            "gen_ai.system": GENAI_SYSTEM,
            "gen_ai.operation.name": "agent.eval",
            "gen_ai.agent.name": run.get("agent_name", run.get("agent_id", "")),
            "ozark.score": run.get("score", 0),
            "ozark.status": run.get("status", ""),
            "ozark.scenario_count": run.get("scenario_count", 0),
        },
    })

    for index, result in enumerate(run.get("results", []), start=1):
        scenario_id = _new_span_id()
        scenario_name = result.get("scenario_name", f"scenario-{index}")
        spans.append({
            "trace_id": trace_id,
            "span_id": scenario_id,
            "parent_span_id": root_id,
            "name": "chat",
            "kind": "INTERNAL",
            "start_time": created_at,
            "end_time": created_at,
            "attributes": {
                "gen_ai.system": GENAI_SYSTEM,
                "gen_ai.operation.name": "chat",
                "gen_ai.user.message": str(result.get("user_prompt", "")),
                "ozark.scenario.name": scenario_name,
                "ozark.scenario.score": result.get("score", 0),
                "ozark.scenario.passed": bool(result.get("passed", False)),
                "ozark.scenario.risk_level": result.get("risk_level", "low"),
            },
        })
        for event in result.get("trace", []):
            kind = event.get("kind", "event")
            spans.append({
                "trace_id": trace_id,
                "span_id": _new_span_id(),
                "parent_span_id": scenario_id,
                "name": _span_name(kind, event),
                "kind": "CLIENT" if kind == "tool_call" else "INTERNAL",
                "start_time": created_at,
                "end_time": created_at,
                "attributes": _event_attributes(event, result),
            })
    return spans


def _trace_id_for(run: dict[str, Any]) -> str:
    rid = str(run.get("id", ""))
    # OTel trace ids are 16 bytes (32 hex chars).  Pad or hash the run id.
    if len(rid) >= 32:
        return rid[:32]
    import hashlib
    return hashlib.sha256(rid.encode("utf-8")).hexdigest()[:32]


def _span_name(kind: str, event: dict[str, Any]) -> str:
    if kind == "tool_call":
        return f"execute_tool {event.get('tool', 'unknown')}"
    if kind == "tool_result":
        return "tool_result"
    if kind == "assistant":
        return "gen_ai.choice"
    if kind == "user":
        return "gen_ai.user.message"
    return f"ozark.trace.{kind}"


def _event_attributes(event: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    attrs: dict[str, Any] = {
        "gen_ai.system": GENAI_SYSTEM,
        "gen_ai.operation.name": "execute_tool" if event.get("kind") == "tool_call" else "chat",
        "ozark.scenario.name": result.get("scenario_name", ""),
        "ozark.event.kind": event.get("kind", ""),
        "ozark.event.step": event.get("step", 0),
    }
    if event.get("kind") == "tool_call":
        attrs["gen_ai.tool.name"] = event.get("tool", "unknown")
        attrs["gen_ai.tool.call.id"] = event.get("call_id", "")
    if event.get("kind") == "tool_result":
        attrs["gen_ai.tool.name"] = event.get("tool", "unknown")
        attrs["gen_ai.tool.result"] = str(event.get("result", ""))[:240]
    if event.get("latency_ms") is not None:
        attrs["gen_ai.usage.duration"] = event["latency_ms"]
    if event.get("content"):
        attrs["gen_ai.prompt"] = str(event["content"])[:240]
    return attrs
