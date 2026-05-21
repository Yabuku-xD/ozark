import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BehaviorState:
    name: str
    transitions: dict[str, float] = field(default_factory=dict)
    tool_weights: dict[str, float] = field(default_factory=dict)
    error_rate: float = 0.0
    mean_latency_ms: int = 100
    latency_std_ms: int = 50


DEFAULT_STATES: dict[str, BehaviorState] = {
    "idle": BehaviorState(
        name="idle",
        transitions={"receiving_input": 1.0},
    ),
    "receiving_input": BehaviorState(
        name="receiving_input",
        transitions={"classifying_intent": 0.6, "blocking_input": 0.15, "requesting_clarification": 0.25},
    ),
    "classifying_intent": BehaviorState(
        name="classifying_intent",
        transitions={"planning_tools": 0.7, "requesting_clarification": 0.15, "blocking_input": 0.15},
    ),
    "blocking_input": BehaviorState(
        name="blocking_input",
        transitions={"responding": 1.0},
        error_rate=0.0,
    ),
    "requesting_clarification": BehaviorState(
        name="requesting_clarification",
        transitions={"receiving_input": 1.0},
    ),
    "planning_tools": BehaviorState(
        name="planning_tools",
        transitions={"executing_tool": 0.8, "responding": 0.1, "error_recovery": 0.1},
        tool_weights={"lookup_user": 0.3, "check_order": 0.15, "run_query": 0.15, "search_code": 0.1,
                      "execute_code": 0.1, "deploy_service": 0.05, "issue_refund": 0.05,
                      "send_email": 0.05, "generate_report": 0.03, "create_ticket": 0.02},
    ),
    "executing_tool": BehaviorState(
        name="executing_tool",
        transitions={"observing_result": 0.7, "error_recovery": 0.15, "planning_tools": 0.15},
        error_rate=0.08,
        mean_latency_ms=200,
        latency_std_ms=100,
    ),
    "observing_result": BehaviorState(
        name="observing_result",
        transitions={"planning_tools": 0.4, "responding": 0.5, "error_recovery": 0.1},
    ),
    "error_recovery": BehaviorState(
        name="error_recovery",
        transitions={"planning_tools": 0.5, "responding": 0.3, "blocking_input": 0.2},
        error_rate=0.05,
    ),
    "responding": BehaviorState(
        name="responding",
        transitions={"idle": 1.0},
    ),
}

FAULT_CHAINS: dict[str, list[str]] = {
    "latency_fault": ["timeout", "rate_limit"],
    "timeout": ["error_recovery", "blocking_input"],
    "auth_error": ["error_recovery", "blocking_input"],
    "rate_limit": ["error_recovery", "responding"],
    "data_corruption": ["error_recovery", "observing_result"],
    "refund_failure": ["error_recovery"],
}


class BehaviorModel:

    def __init__(self, seed: int = 42, states: dict[str, BehaviorState] | None = None,
                 fault_chains: dict[str, list[str]] | None = None):
        self.rng = random.Random(seed)
        self.states = states or DEFAULT_STATES
        self.fault_chains = fault_chains or FAULT_CHAINS
        self.current_state: str = "idle"
        self.history: list[str] = []
        self.active_faults: list[str] = []

    def reset(self) -> None:
        self.current_state = "idle"
        self.history = []
        self.active_faults = []

    def advance_state(self) -> str:
        state = self.states.get(self.current_state)
        if not state or not state.transitions:
            return self.current_state
        choices = list(state.transitions.keys())
        weights = list(state.transitions.values())
        self.current_state = self.rng.choices(choices, weights=weights, k=1)[0]
        self.history.append(self.current_state)
        return self.current_state

    def should_execute_tool(self, tool_name: str) -> bool:
        state = self.states.get(self.current_state)
        if not state:
            return False
        if state.name == "blocking_input":
            return False
        base_prob = state.tool_weights.get(tool_name, 0.1)
        if base_prob == 0:
            return False
        return self.rng.random() < base_prob

    def should_error(self) -> bool:
        state = self.states.get(self.current_state)
        if not state:
            return False
        return self.rng.random() < state.error_rate

    def get_latency(self) -> int:
        state = self.states.get(self.current_state)
        if not state:
            return 50
        return max(1, int(self.rng.gauss(state.mean_latency_ms, state.latency_std_ms)))

    def inject_fault(self, fault: str) -> list[str]:
        self.active_faults.append(fault)
        chain = self.fault_chains.get(fault, [])
        result = [fault]
        for cascading in chain:
            if self.rng.random() < 0.3:
                self.active_faults.append(cascading)
                result.append(cascading)
        return result

    def get_tool_probability(self, tool_name: str) -> float:
        state = self.states.get(self.current_state)
        if not state:
            return 0.0
        return state.tool_weights.get(tool_name, 0.0)

    def get_available_states(self) -> list[str]:
        return list(self.states.keys())

    def get_state_coverage(self) -> dict[str, int]:
        coverage: dict[str, int] = {}
        for s in self.history:
            coverage[s] = coverage.get(s, 0) + 1
        return coverage

    def get_transition_coverage(self) -> dict[tuple[str, str], int]:
        coverage: dict[tuple[str, str], int] = {}
        for i in range(len(self.history) - 1):
            pair = (self.history[i], self.history[i + 1])
            coverage[pair] = coverage.get(pair, 0) + 1
        return coverage
