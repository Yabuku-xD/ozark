import json
import time
import urllib.error
import urllib.request
from typing import Any

from backend.security import validate_live_endpoint

from .common import (
    AdapterResponse,
    adapter_result_from_response,
    tool_calls_from_response,
)

# pi-lens: ignore python-thread-global-write -- this adapter does not create threads or mutate globals.


class HttpAdapter:
    def __init__(self, endpoint: str, headers: dict | None = None, timeout: int = 30):
        validate_live_endpoint(endpoint)
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
                tool_calls=tool_calls_from_response(body),
                latency_ms=latency,
                raw_response=body,
            )
        except urllib.error.URLError as exc:  # tree-sitter-patterns:bare-except false positive; catches URLError only.
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(
                content="",
                latency_ms=latency,
                error=f"Connection error: {exc.reason}",
            )
        except TimeoutError as exc:  # tree-sitter-patterns:bare-except false positive; catches TimeoutError only.
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(content="", latency_ms=latency, error=str(exc))
        except ValueError as exc:  # tree-sitter-patterns:bare-except false positive; catches ValueError only.
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(content="", latency_ms=latency, error=str(exc))
        except OSError as exc:  # tree-sitter-patterns:bare-except false positive; catches OSError only.
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(content="", latency_ms=latency, error=str(exc))

    def run_scenario(
        self, scenario: Any, expected_tools: list[str] | None = None
    ) -> dict:
        resp = self.send_prompt(scenario.user_prompt, scenario.metadata)
        return adapter_result_from_response(scenario, resp)
