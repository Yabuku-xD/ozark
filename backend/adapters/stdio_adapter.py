import json
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StdioResponse:
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    latency_ms: int = 0
    error: str | None = None


class StdioAdapter:
    def __init__(self, command: list[str], cwd: str | None = None, timeout: int = 30):
        self.command = command
        self.cwd = cwd
        self.timeout = timeout

    def send_prompt(self, prompt: str, context: dict | None = None) -> StdioResponse:
        payload = json.dumps({
            "prompt": prompt,
            "context": context or {},
        })
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
            if proc.returncode != 0:
                return StdioResponse(
                    content="",
                    latency_ms=latency,
                    error=f"Process exited with code {proc.returncode}: {proc.stderr[:200]}",
                )
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                result = {"content": proc.stdout}
            return StdioResponse(
                content=result.get("content", result.get("response", proc.stdout)),
                tool_calls=result.get("tool_calls", result.get("tools", [])),
                latency_ms=latency,
            )
        except subprocess.TimeoutExpired:
            latency = int((time.perf_counter() - start) * 1000)
            return StdioResponse(content="", latency_ms=latency, error=f"Command timed out after {self.timeout}s")
        except (OSError, ValueError, json.JSONDecodeError) as e:
            latency = int((time.perf_counter() - start) * 1000)
            return StdioResponse(content="", latency_ms=latency, error=str(e))

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
