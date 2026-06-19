"""Tests for the simulation engine (simulator.py).

Covers reproducibility (stable hashing), parallel execution, and
deterministic scoring across restarts of the same seed.
"""

from __future__ import annotations

from backend.engine.simulator import SimulationEngine, stable_hash_int
from backend.models import AgentConfig, ScenarioDefinition, ScenarioType


def _minimal_agent() -> AgentConfig:
    return AgentConfig.from_dict({
        "name": "Test Agent",
        "agent_type": "customer_support",
        "system_prompt": "You are a helpful support agent.",
        "tools": [{"name": "lookup_user", "risk": "low"}],
        "guardrails": [{"id": "gr-1", "name": "default", "type": "block", "severity": "block"}],
        "max_turns": 5,
    })


def _scenarios(n: int = 10) -> list[ScenarioDefinition]:
    return [
        ScenarioDefinition(
            name=f"scenario-{i}",
            scenario_type=ScenarioType.HAPPY_PATH,
            description=f"scenario {i}",
            user_prompt=f"Do something useful #{i}",
            expected_tools=["lookup_user"],
        )
        for i in range(n)
    ]


def test_stable_hash_int_is_deterministic():
    a = stable_hash_int("test-scenario")
    b = stable_hash_int("test-scenario")
    assert a == b
    # Different inputs should (almost certainly) produce different hashes.
    assert stable_hash_int("other") != a


def test_same_seed_produces_same_score():
    agent = _minimal_agent()
    scenarios = _scenarios(15)
    r1 = SimulationEngine(agent, scenarios, seed=42).run()
    r2 = SimulationEngine(agent, scenarios, seed=42).run()
    assert r1.score == r2.score
    assert r1.results[0].scenario_name == r2.results[0].scenario_name


def test_parallel_run_matches_sequential_run():
    agent = _minimal_agent()
    scenarios = _scenarios(20)
    # Parallel results may arrive in a different order internally, but the
    # SimulationEngine preserves input order via index mapping.
    seq = SimulationEngine(agent, scenarios, seed=7).run(max_workers=1)
    par = SimulationEngine(agent, scenarios, seed=7).run(max_workers=4)
    # Scores match because each scenario's seed is derived from its name
    # (stable hash), not from execution order.
    assert seq.score == par.score
    assert [r.scenario_name for r in seq.results] == [r.scenario_name for r in par.results]


def test_progress_callback_invoked():
    agent = _minimal_agent()
    scenarios = _scenarios(8)
    seen: list[tuple[int, int]] = []
    SimulationEngine(agent, scenarios, seed=1).run(
        progress_fn=lambda done, total: seen.append((done, total))
    )
    assert len(seen) == 8
    assert seen[-1] == (8, 8)


def test_run_produces_results_with_risk_summary():
    agent = _minimal_agent()
    scenarios = _scenarios(5)
    run = SimulationEngine(agent, scenarios, seed=99).run()
    assert run.scenario_count == 5
    assert "by_level" in run.risk_summary
    assert run.total_cost >= 0
