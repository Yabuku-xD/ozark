import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterResponse:
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    latency_ms: int = 0
    error: str | None = None
    raw_response: dict | None = None


class HttpAdapter:
    def __init__(self, endpoint: str, headers: dict | None = None, timeout: int = 30):
        self.endpoint = endpoint.rstrip("/")
        self.headers = headers or {"Content-Type": "application/json"}
        self.timeout = timeout

    def send_prompt(self, prompt: str, context: dict | None = None) -> AdapterResponse:
        payload = {
            "prompt": prompt,
            "context": context or {},
            "stream": False,
        }
        start = time.perf_counter()
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint, data=data, headers=self.headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(
                content=body.get("content", body.get("response", "")),
                tool_calls=body.get("tool_calls", body.get("tools", [])),
                latency_ms=latency,
                raw_response=body,
            )
        except urllib.error.URLError as e:
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(
                content="",
                latency_ms=latency,
                error=f"Connection error: {e.reason}",
            )
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(
                content="",
                latency_ms=latency,
                error=str(e),
            )

    def run_scenario(self, scenario: Any, expected_tools: list[str] | None = None) -> dict:
        resp = self.send_prompt(scenario.user_prompt, scenario.metadata)
        tool_names = [t.get("name", t.get("tool", "")) for t in resp.tool_calls]
        return {
            "scenario_name": scenario.name,
            "scenario_type": scenario.scenario_type.value,
            "passed": not resp.error,
            "score": 100 if not resp.error else 0,
            "called_tools": tool_names,
            "violations": [],
            "trace": [],
            "latency_ms": resp.latency_ms,
            "total_cost": 0.0,
            "failures": [resp.error] if resp.error else [],
        }
