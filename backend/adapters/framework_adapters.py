"""Framework adapters for popular Python agent frameworks.

These are *optional* adapters.  They let users point Ozark at a real
agent built with LangChain, LangGraph, CrewAI, OpenAI Agents SDK, or
AutoGen without writing a custom HTTP endpoint.  Each adapter turns a
scenario into a tool-call trace in Ozark's format.

All dependencies are soft: if a framework isn't installed, its adapter
is not registered.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from ..models import ScenarioDefinition
from .common import AdapterResponse, adapter_result_from_response


class FrameworkRegistry:
    """Registers framework-specific adapter functions lazily."""

    def __init__(self) -> None:
        self._adapters: dict[str, Callable[[Any, ScenarioDefinition], dict]] = {}

    def register(
        self, name: str
    ) -> Callable[[Callable[[Any, ScenarioDefinition], dict]], Callable[[Any, ScenarioDefinition], dict]]:
        def deco(fn: Callable[[Any, ScenarioDefinition], dict]) -> Callable[[Any, ScenarioDefinition], dict]:
            self._adapters[name] = fn
            return fn

        return deco

    def get(self, name: str) -> Callable[[Any, ScenarioDefinition], dict] | None:
        return self._adapters.get(name)

    def list_frameworks(self) -> list[str]:
        return list(self._adapters.keys())


_registry = FrameworkRegistry()


def _build_trace(tool_calls: list[dict], assistant_text: str) -> list[dict]:
    trace: list[dict] = []
    step = 1
    for tc in tool_calls:
        trace.append(
            {
                "step": step,
                "kind": "tool_call",
                "tool": tc.get("name", ""),
                "args": tc.get("args", {}),
                "result": tc.get("result"),
                "latency_ms": tc.get("latency_ms", 0),
            }
        )
        step += 1
    if assistant_text:
        trace.append(
            {"step": step, "kind": "assistant", "content": assistant_text}
        )
    return trace


# ---------------------------------------------------------------------------
# LangChain / LangGraph adapter
# ---------------------------------------------------------------------------

def _langchain_adapter(agent: Any, scenario: ScenarioDefinition) -> dict:
    """Run a LangChain/LangGraph agent against a scenario.

    ``agent`` can be a LangChain runnable (``invoke`` method) or a callable.
    """
    import time

    start = time.perf_counter()
    if hasattr(agent, "invoke"):
        response = agent.invoke({"input": scenario.user_prompt})
        text = response.get("output") if isinstance(response, dict) else str(response)
    else:
        text = str(agent(scenario.user_prompt))
    latency = int((time.perf_counter() - start) * 1000)

    # LangGraph / tool-agent responses may include intermediate_steps.
    tool_calls: list[dict] = []
    if isinstance(response, dict):
        steps = response.get("intermediate_steps", [])
        for action, observation in steps:
            tool_calls.append(
                {
                    "name": getattr(action, "tool", getattr(action, "name", "")),
                    "args": dict(getattr(action, "tool_input", {})),
                    "result": observation,
                    "latency_ms": 0,
                }
            )

    return adapter_result_from_response(
        scenario,
        AdapterResponse(
            content=text,
            tool_calls=tool_calls,
            latency_ms=latency,
            raw_response=response if isinstance(response, dict) else {"output": text},
        ),
    )


# Register only if LangChain is installed.
try:
    import langchain  # noqa: F401

    _registry.register("langchain")(_langchain_adapter)
    _registry.register("langgraph")(_langchain_adapter)
except ImportError:
    pass


# ---------------------------------------------------------------------------
# CrewAI adapter
# ---------------------------------------------------------------------------

def _crewai_adapter(crew: Any, scenario: ScenarioDefinition) -> dict:
    """Run a CrewAI crew against a scenario.

    ``crew`` should be an instance of ``crewai.Crew`` that exposes
    ``kickoff(inputs=...)``.
    """
    import time

    start = time.perf_counter()
    result = crew.kickoff(inputs={"prompt": scenario.user_prompt})
    latency = int((time.perf_counter() - start) * 1000)
    text = str(getattr(result, "raw", result))

    tool_calls: list[dict] = []
    if hasattr(result, "tasks_output"):
        for task in result.tasks_output:
            for tool in getattr(task, "tools", []):
                tool_calls.append(
                    {
                        "name": getattr(tool, "name", ""),
                        "args": getattr(tool, "args", {}),
                        "result": getattr(tool, "result", None),
                        "latency_ms": 0,
                    }
                )

    return adapter_result_from_response(
        scenario,
        AdapterResponse(
            content=text,
            tool_calls=tool_calls,
            latency_ms=latency,
            raw_response={"output": text, "result": repr(result)},
        ),
    )


try:
    import crewai  # noqa: F401

    _registry.register("crewai")(_crewai_adapter)
except ImportError:
    pass


# ---------------------------------------------------------------------------
# OpenAI Agents SDK adapter
# ---------------------------------------------------------------------------

def _openai_agents_adapter(agent: Any, scenario: ScenarioDefinition) -> dict:
    """Run an OpenAI Agents SDK agent.

    ``agent`` is expected to be a runner or a callable returned by the
    SDK.  The OpenAI Agents SDK API was in flux at the time of writing; this
    adapter accepts either ``agent.run`` or a direct callable.
    """
    import asyncio
    import time

    async def _run() -> tuple[str, list[dict], Any]:
        if hasattr(agent, "run"):
            result = await agent.run(scenario.user_prompt)
        else:
            result = await agent(scenario.user_prompt)
        text = str(getattr(result, "final_output", result))
        calls: list[dict] = []
        raw = result
        if hasattr(result, "new_items"):
            for item in result.new_items:
                if getattr(item, "type", None) == "tool_call":
                    calls.append(
                        {
                            "name": getattr(item, "name", ""),
                            "args": getattr(item, "arguments", {}),
                            "result": getattr(item, "output", None),
                            "latency_ms": 0,
                        }
                    )
        return text, calls, raw

    start = time.perf_counter()
    try:
        text, calls, raw = asyncio.run(_run())
    except RuntimeError:
        # If we're already in an event loop, schedule on it.
        loop = asyncio.get_running_loop()
        text, calls, raw = loop.run_until_complete(_run())
    latency = int((time.perf_counter() - start) * 1000)

    return adapter_result_from_response(
        scenario,
        AdapterResponse(
            content=text,
            tool_calls=calls,
            latency_ms=latency,
            raw_response={"output": text, "raw": repr(raw)},
        ),
    )


try:
    import agents  # noqa: F401 — OpenAI Agents SDK package name

    _registry.register("openai_agents")(_openai_agents_adapter)
except ImportError:
    pass


# ---------------------------------------------------------------------------
# AutoGen adapter
# ---------------------------------------------------------------------------

def _autogen_adapter(agent: Any, scenario: ScenarioDefinition) -> dict:
    """Run an AutoGen conversable agent.

    ``agent`` should be a ``ConversableAgent`` or a team runner exposing
    `` initiate_chat``.
    """
    import time

    start = time.perf_counter()
    if hasattr(agent, "initiate_chat"):
        chat_result = agent.initiate_chat(
            recipient=agent,
            message=scenario.user_prompt,
            max_turns=5,
        )
        text = str(getattr(chat_result, "summary", chat_result))
        raw = chat_result
    else:
        text = str(agent(scenario.user_prompt))
        raw = {"output": text}
    latency = int((time.perf_counter() - start) * 1000)

    tool_calls: list[dict] = []
    if hasattr(raw, "chat_history"):
        for msg in raw.chat_history:
            if msg.get("role") == "tool" or msg.get("tool_responses"):
                tool_calls.append(
                    {
                        "name": msg.get("tool", msg.get("name", "")),
                        "args": msg.get("tool_input", {}),
                        "result": msg.get("content"),
                        "latency_ms": 0,
                    }
                )

    return adapter_result_from_response(
        scenario,
        AdapterResponse(
            content=text,
            tool_calls=tool_calls,
            latency_ms=latency,
            raw_response=raw if isinstance(raw, dict) else {"output": text},
        ),
    )


try:
    import autogen  # noqa: F401

    _registry.register("autogen")(_autogen_adapter)
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_framework_agent(agent: Any, framework: str, scenario: ScenarioDefinition) -> dict:
    """Dispatch to a registered framework adapter.

    Raises ``ValueError`` if the framework is unknown or its dependency
    is not installed.
    """
    adapter = _registry.get(framework)
    if adapter is None:
        raise ValueError(
            f"Framework adapter not available: {framework}. "
            f"Available: {', '.join(_registry.list_frameworks())}"
        )
    return adapter(agent, scenario)


def list_frameworks() -> list[str]:
    return _registry.list_frameworks()


# Convenience callable that can be passed as a ``scenario_fn`` to the HTTP/stdio
# adapters if a framework-specific endpoint is added later.
FrameworkRunner = Callable[[ScenarioDefinition], dict]


def framework_runner(agent: Any, framework: str) -> FrameworkRunner:
    return functools.partial(run_framework_agent, agent, framework)
