import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterResponse:
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int = 0
    error: str | None = None
    raw_response: dict[str, Any] | None = None


def response_body_from_output(output: str) -> dict[str, Any]:
    if not output.strip().startswith("{"):
        return {"content": output}
    try:
        result = json.loads(output)
    except json.JSONDecodeError:
        return {"content": output}
    return result if isinstance(result, dict) else {"content": output}


def tool_calls_from_response(body: dict[str, Any]) -> list[dict[str, Any]]:
    tool_calls = body.get("tool_calls", body.get("tools", []))
    return tool_calls if isinstance(tool_calls, list) else []


def tool_names_from_calls(tool_calls: list[dict[str, Any]]) -> list[str]:
    return [tool.get("name", tool.get("tool", "")) for tool in tool_calls]


def adapter_result_from_response(scenario: Any, response: AdapterResponse) -> dict[str, Any]:
    return {
        "scenario_name": getattr(scenario, "name", "scenario"),
        "scenario_type": getattr(getattr(scenario, "scenario_type", None), "value", "happy_path"),
        "passed": not response.error,
        "score": 100 if not response.error else 0,
        "called_tools": tool_names_from_calls(response.tool_calls),
        "violations": [],
        "trace": response.tool_calls + [{"kind": "assistant", "content": response.content}],
        "latency_ms": response.latency_ms,
        "total_cost": 0.0,
        "failures": [response.error] if response.error else [],
    }
