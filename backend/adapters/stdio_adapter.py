import json
import subprocess
import time
from typing import Any

from .common import (
    AdapterResponse,
    adapter_result_from_response,
    response_body_from_output,
    tool_calls_from_response,
)


def _process_failed(proc: subprocess.CompletedProcess) -> bool:
    return proc.returncode != 0


def _process_error_response(
    proc: subprocess.CompletedProcess,
    latency: int,
) -> AdapterResponse:
    stderr = proc.stderr[:200]
    message = f"Process exited with code {proc.returncode}: {stderr}"
    return AdapterResponse(content="", latency_ms=latency, error=message)


class StdioAdapter:
    def __init__(self, command: list[str], cwd: str | None = None, timeout: int = 30):
        self.command = command
        self.cwd = cwd
        self.timeout = timeout

    def send_prompt(self, prompt: str, context: dict | None = None) -> AdapterResponse:
        payload = json.dumps(
            {
                "prompt": prompt,
                "context": context or {},
            },
        )
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                self.command,
                input=payload,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.cwd,
            )
            latency = int((time.perf_counter() - start) * 1000)
            if _process_failed(proc):
                return _process_error_response(proc, latency)
            result = response_body_from_output(proc.stdout)
            return AdapterResponse(
                content=result.get("content", result.get("response", proc.stdout)),
                tool_calls=tool_calls_from_response(result),
                latency_ms=latency,
            )
        except subprocess.TimeoutExpired:  # tree-sitter-patterns:bare-except false positive; catches TimeoutExpired only.
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(
                content="",
                latency_ms=latency,
                error=f"Command timed out after {self.timeout}s",
            )
        except OSError as exc:  # tree-sitter-patterns:bare-except false positive; catches OSError only.
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(content="", latency_ms=latency, error=str(exc))
        except ValueError as exc:  # tree-sitter-patterns:bare-except false positive; catches ValueError only.
            latency = int((time.perf_counter() - start) * 1000)
            return AdapterResponse(content="", latency_ms=latency, error=str(exc))

    def run_scenario(
        self,
        scenario: Any,
        expected_tools: list[str] | None = None,
    ) -> dict:
        resp = self.send_prompt(scenario.user_prompt, scenario.metadata)
        return adapter_result_from_response(scenario, resp)
