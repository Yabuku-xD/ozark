import json
import uuid
from typing import Any

from .. import models
from ..engine.evaluators import EvaluatorRunner
from ..security import validate_trace_path


def load_trace_payload(path: str) -> dict[str, Any]:
    source = validate_trace_path(path)
    text = source.read_text(encoding="utf-8")
    if source.suffix == ".jsonl":
        return {"events": [json.loads(line) for line in text.splitlines() if line.strip()]}
    return json.loads(text)


def normalize_payload(payload: dict[str, Any], agent_id: str, agent_name: str = "Production Agent") -> dict[str, Any]:
    if "results" in payload and "score" in payload:
        run = dict(payload)
        run.setdefault("id", "import-" + uuid.uuid4().hex[:10])
        run.setdefault("agent_id", agent_id)
        run.setdefault("agent_name", agent_name)
        run.setdefault("created_at", models.iso_now())
        return run

    if "spans" in payload:
        results = _results_from_spans(payload["spans"])
    elif "events" in payload:
        results = _results_from_events(payload["events"])
    elif "traces" in payload:
        results = []
        for trace in payload["traces"]:
            if isinstance(trace, dict) and "spans" in trace:
                results.extend(_results_from_spans(trace["spans"]))
            elif isinstance(trace, dict) and "events" in trace:
                results.extend(_results_from_events(trace["events"]))
    else:
        results = [_result_from_record(payload, 1)]

    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    score = round(sum(result.get("score", 0) for result in results) / max(total, 1))
    return {
        "id": payload.get("id") or "import-" + uuid.uuid4().hex[:10],
        "agent_id": agent_id,
        "agent_name": agent_name,
        "score": score,
        "status": "passed" if total and passed / total >= 0.8 else "needs_review",
        "summary": f"Imported production trace: {passed}/{total} scenarios passed",
        "confidence": score / 100,
        "scenario_count": total,
        "passed_count": passed,
        "failed_count": total - passed,
        "total_cost": round(sum(r.get("total_cost", 0) or 0 for r in results), 6) or None,
        "total_latency_ms": sum(result.get("latency_ms", 0) for result in results),
        "results": results,
        "dimension_scores": {},
        "recommendations": [],
        "created_at": payload.get("created_at") or models.iso_now(),
        "metadata": {"source": "production_ingest", "format": _format_name(payload)},
    }


def evaluate_imported_run(run: dict[str, Any], evaluators: list[dict[str, Any]]) -> dict[str, Any]:
    return EvaluatorRunner(evaluators).evaluate_run(run)


def _results_from_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for span in spans:
        trace_id = span.get("trace_id") or span.get("traceId") or span.get("context", {}).get("trace_id") or "default"
        grouped.setdefault(trace_id, []).append(span)
    return [_result_from_spans(trace_id, trace_spans, index) for index, (trace_id, trace_spans) in enumerate(grouped.items(), start=1)]


def _result_from_spans(trace_id: str, spans: list[dict[str, Any]], index: int) -> dict[str, Any]:
    events = []
    tools = []
    latency = 0
    cost = 0.0
    failures = []
    for step, span in enumerate(spans, start=1):
        attrs = span.get("attributes", {}) or {}
        name = span.get("name", "span")
        kind = _event_kind(name, attrs)
        tool = attrs.get("gen_ai.tool.name") or attrs.get("tool.name") or (name.split(".")[-1] if kind == "tool" else "")
        if tool:
            tools.append(tool)
        latency += int(attrs.get("ozark.event.latency_ms") or attrs.get("duration_ms") or span.get("duration_ms") or 0)
        cost += float(attrs.get("ozark.event.cost") or attrs.get("gen_ai.usage.cost") or 0)
        if span.get("status", {}).get("code") in {"ERROR", 2} or attrs.get("error"):
            failures.append(str(span.get("status", {}).get("message") or attrs.get("error") or name))
        events.append({
            "step": step,
            "kind": kind,
            "content": attrs.get("gen_ai.prompt") or attrs.get("input.value") or attrs.get("output.value") or name,
            "tool": tool,
            "risk": attrs.get("ozark.tool.risk", "low"),
            "args": attrs.get("tool.args", {}) if isinstance(attrs.get("tool.args", {}), dict) else {},
            "result": attrs.get("tool.result"),
            "latency_ms": int(attrs.get("ozark.event.latency_ms") or attrs.get("duration_ms") or 0),
            "cost": float(attrs.get("ozark.event.cost") or 0),
            "timestamp": span.get("start_time") or span.get("startTime") or "",
        })
    score = 100 if not failures else 50
    return {
        "scenario_name": f"prod/{trace_id}",
        "scenario_type": "multi_turn" if len(events) > 2 else "happy_path",
        "passed": not failures,
        "score": score,
        "score_method": "ingest_heuristic",
        "called_tools": sorted(set(tools)),
        "violations": [],
        "trace": events,
        "latency_ms": latency,
        "total_cost": cost if cost else None,
        "turn_count": len([event for event in events if event["kind"] in {"user", "assistant"}]),
        "failures": failures,
        "actor_behavior": "production_import",
    }


def _results_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        trace_id = event.get("trace_id") or event.get("run_id") or event.get("session_id") or "default"
        grouped.setdefault(trace_id, []).append(event)
    return [_result_from_events(trace_id, trace_events, index) for index, (trace_id, trace_events) in enumerate(grouped.items(), start=1)]


def _result_from_events(trace_id: str, events: list[dict[str, Any]], index: int) -> dict[str, Any]:
    trace = []
    tools = []
    failures = []
    for step, event in enumerate(events, start=1):
        kind = event.get("kind") or event.get("role") or event.get("type") or "event"
        if kind in {"tool_call", "tool"}:
            kind = "tool"
        if kind in {"assistant_message", "completion"}:
            kind = "assistant"
        if kind in {"user_message", "prompt"}:
            kind = "user"
        tool = event.get("tool") or event.get("tool_name") or ""
        if tool:
            tools.append(tool)
        if event.get("error"):
            failures.append(str(event["error"]))
        trace.append({
            "step": step,
            "kind": kind,
            "content": event.get("content") or event.get("message") or event.get("input") or event.get("output") or "",
            "tool": tool,
            "risk": event.get("risk", "low"),
            "args": event.get("args", {}),
            "result": event.get("result"),
            "latency_ms": int(event.get("latency_ms", 0) or 0),
            "cost": float(event.get("cost", 0.0) or 0.0),
            "timestamp": event.get("timestamp", ""),
        })
    return {
        "scenario_name": f"prod/{trace_id}",
        "scenario_type": "multi_turn" if len(trace) > 2 else "happy_path",
        "passed": not failures,
        "score": 100 if not failures else 50,
        "score_method": "ingest_heuristic",
        "called_tools": sorted(set(tools)),
        "violations": [],
        "trace": trace,
        "latency_ms": sum(event.get("latency_ms", 0) for event in trace),
        "total_cost": sum(event.get("cost", 0.0) for event in trace) or None,
        "turn_count": len([event for event in trace if event["kind"] in {"user", "assistant"}]),
        "failures": failures,
        "actor_behavior": "production_import",
    }


def _result_from_record(record: dict[str, Any], index: int) -> dict[str, Any]:
    return _result_from_events(record.get("id", f"record-{index}"), [record], index)


def _event_kind(name: str, attrs: dict[str, Any]) -> str:
    operation = attrs.get("gen_ai.operation.name", "")
    if "tool" in name or operation == "execute_tool":
        return "tool"
    if "user" in name:
        return "user"
    if "completion" in name or "assistant" in name:
        return "assistant"
    return "event"


def _format_name(payload: dict[str, Any]) -> str:
    if "spans" in payload:
        return "otel_spans"
    if "events" in payload:
        return "jsonl_events"
    if "traces" in payload:
        return "trace_bundle"
    return "single_record"
