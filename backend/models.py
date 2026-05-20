"""Data models and schemas for Ozark."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import json
import uuid


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailSeverity(str, Enum):
    AUDIT = "audit"
    WARN = "warn"
    BLOCK = "block"


class ScenarioType(str, Enum):
    HAPPY_PATH = "happy_path"
    EDGE_CASE = "edge_case"
    ERROR_RECOVERY = "error_recovery"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MULTI_TURN = "multi_turn"
    ADVERSARIAL = "adversarial"
    COMPLIANCE = "compliance"


class AgentType(str, Enum):
    SUPPORT = "customer_support"
    CODING = "code_assistant"
    DATA = "data_analysis"
    OPERATIONS = "autonomous_ops"
    SALES = "sales_agent"
    FINANCE = "finance_agent"
    LEGAL = "legal_agent"
    HEALTHCARE = "healthcare_agent"
    RECRUITING = "recruiting_agent"
    CUSTOM = "custom"


@dataclass
class Tool:
    name: str
    description: str
    risk: RiskLevel = RiskLevel.LOW
    parameters: dict = field(default_factory=dict)
    requires_confirmation: bool = False
    rate_limit_per_minute: int = 0
    cost_per_call: float = 0.0


@dataclass
class Guardrail:
    id: str
    rule: str
    severity: GuardrailSeverity = GuardrailSeverity.WARN
    category: str = "safety"
    enabled: bool = True


@dataclass
class AgentConfig:
    name: str
    description: str
    agent_type: AgentType = AgentType.CUSTOM
    framework: str = "langchain"
    system_prompt: str = ""
    tools: list[Tool] = field(default_factory=list)
    guardrails: list[Guardrail] = field(default_factory=list)
    max_turns: int = 10
    temperature: float = 0.0
    model: str = "gpt-4"
    cost_budget: float = 0.0

    def to_dict(self) -> dict:
        result = {
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "framework": self.framework,
            "system_prompt": self.system_prompt,
            "tools": [{"name": t.name, "description": t.description, "risk": t.risk.value,
                       "parameters": t.parameters, "requires_confirmation": t.requires_confirmation,
                       "rate_limit_per_minute": t.rate_limit_per_minute, "cost_per_call": t.cost_per_call}
                      for t in self.tools],
            "guardrails": [{"id": g.id, "rule": g.rule, "severity": g.severity.value,
                            "category": g.category, "enabled": g.enabled}
                           for g in self.guardrails],
            "max_turns": self.max_turns,
            "temperature": self.temperature,
            "model": self.model,
            "cost_budget": self.cost_budget,
        }
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        return cls(
            name=data.get("name", "Untitled Agent"),
            description=data.get("description", ""),
            agent_type=AgentType(data.get("agent_type", "custom")),
            framework=data.get("framework", "langchain"),
            system_prompt=data.get("system_prompt", ""),
            tools=[Tool(name=t["name"], description=t.get("description", ""),
                        risk=RiskLevel(t.get("risk", "low")),
                        parameters=t.get("parameters", {}),
                        requires_confirmation=t.get("requires_confirmation", False),
                        rate_limit_per_minute=t.get("rate_limit_per_minute", 0),
                        cost_per_call=t.get("cost_per_call", 0.0))
                   for t in data.get("tools", [])],
            guardrails=[Guardrail(id=g["id"], rule=g.get("rule", ""),
                                  severity=GuardrailSeverity(g.get("severity", "warn")),
                                  category=g.get("category", "safety"),
                                  enabled=g.get("enabled", True))
                        for g in data.get("guardrails", [])],
            max_turns=data.get("max_turns", 10),
            temperature=data.get("temperature", 0.0),
            model=data.get("model", "gpt-4"),
            cost_budget=data.get("cost_budget", 0.0),
        )


@dataclass
class ScenarioDefinition:
    name: str
    scenario_type: ScenarioType
    description: str
    user_prompt: str
    user_persona: str = "default"
    expected_tools: list[str] = field(default_factory=list)
    blocked_tools: list[str] = field(default_factory=list)
    expected_outcome: str = ""
    turns: int = 1
    injected_faults: list[str] = field(default_factory=list)
    sensitive_data: bool = False
    difficulty: str = "medium"
    agent_type: str = "customer_support"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScenarioDefinition":
        return cls(**{k: v for k, v in data.items()
                      if k in cls.__dataclass_fields__})


@dataclass
class TraceEvent:
    step: int
    kind: str
    content: Any = None
    tool: str = ""
    risk: str = "low"
    args: dict = field(default_factory=dict)
    result: Any = None
    latency_ms: int = 0
    cost: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Violation:
    guardrail: str
    severity: str
    message: str
    category: str = "safety"
    evidence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScenarioResult:
    scenario_name: str
    scenario_type: str
    passed: bool
    score: int
    called_tools: list[str] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
    trace: list[TraceEvent] = field(default_factory=list)
    latency_ms: int = 0
    total_cost: float = 0.0
    turn_count: int = 0
    failures: list[str] = field(default_factory=list)
    actor_behavior: str = ""

    def to_dict(self) -> dict:
        result = asdict(self)
        result["violations"] = [v.to_dict() if isinstance(v, Violation) else v
                                for v in self.violations]
        result["trace"] = [t.to_dict() if isinstance(t, TraceEvent) else t
                           for t in self.trace]
        return result


@dataclass
class SimulationRun:
    id: str
    agent_id: str
    agent_name: str
    score: int
    status: str
    summary: str
    confidence: float
    scenario_count: int
    passed_count: int
    failed_count: int
    total_cost: float
    total_latency_ms: int
    results: list[ScenarioResult] = field(default_factory=list)
    dimension_scores: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "score": self.score,
            "status": self.status,
            "summary": self.summary,
            "confidence": self.confidence,
            "scenario_count": self.scenario_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "total_cost": self.total_cost,
            "total_latency_ms": self.total_latency_ms,
            "results": [r.to_dict() for r in self.results],
            "dimension_scores": self.dimension_scores,
            "recommendations": self.recommendations,
            "created_at": self.created_at,
        }


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
