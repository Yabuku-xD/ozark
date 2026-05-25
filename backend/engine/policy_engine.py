import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PolicyRule:
    id: str
    description: str
    conditions: dict
    action: str
    priority: int = 0

    def evaluate(self, context: dict) -> bool:
        return self._evaluate_node(self.conditions, context)

    def _evaluate_node(self, node: Any, context: dict) -> bool:
        if isinstance(node, bool):
            return node
        if isinstance(node, dict):
            if "AND" in node:
                return all(self._evaluate_node(c, context) for c in node["AND"])
            if "OR" in node:
                return any(self._evaluate_node(c, context) for c in node["OR"])
            if "NOT" in node:
                return not self._evaluate_node(node["NOT"], context)
            if "field" in node:
                return self._eval_condition(node, context)
        return True

    def _eval_condition(self, cond: dict, context: dict) -> bool:
        field = cond["field"]
        value = context.get(field)
        op = cond.get("op", "equals")
        target = cond.get("value")

        if op == "equals":
            return value == target
        if op == "not_equals":
            return value != target
        if op == "in":
            return value in (target if isinstance(target, list) else [target])
        if op == "not_in":
            return value not in (target if isinstance(target, list) else [target])
        if op == "gt" and isinstance(value, (int, float)) and isinstance(target, (int, float)):
            return value > target
        if op == "gte" and isinstance(value, (int, float)) and isinstance(target, (int, float)):
            return value >= target
        if op == "lt" and isinstance(value, (int, float)) and isinstance(target, (int, float)):
            return value < target
        if op == "lte" and isinstance(value, (int, float)) and isinstance(target, (int, float)):
            return value <= target
        if op == "contains" and isinstance(value, str) and isinstance(target, str):
            return target.lower() in value.lower()
        if op == "matches" and isinstance(value, str) and isinstance(target, str):
            import re
            return bool(re.search(target, value, re.IGNORECASE))
        if op == "any":
            return True
        return False


@dataclass
class PolicySet:
    name: str
    rules: list[PolicyRule] = field(default_factory=list)

    def enforce(self, context: dict) -> list[str]:
        violations: list[str] = []
        for rule in sorted(self.rules, key=lambda r: -r.priority):
            if rule.evaluate(context):
                if rule.action == "block":
                    violations.append(f"BLOCKED by {rule.id}: {rule.description}")
                elif rule.action == "warn":
                    violations.append(f"WARNING from {rule.id}: {rule.description}")
                elif rule.action == "escalate":
                    violations.append(f"ESCALATION from {rule.id}: {rule.description}")
        return violations


class PolicyEngine:

    def __init__(self, policies_dir: str | None = None):
        self.policies: dict[str, PolicySet] = {}
        if policies_dir:
            self.load_directory(policies_dir)
        else:
            self._load_defaults()

    def _load_defaults(self) -> None:
        self.policies["refund_limits"] = PolicySet(
            name="refund_limits",
            rules=[
                PolicyRule(
                    id="refund_over_500", description="Refunds > $500 require manager approval",
                    conditions={"field": "refund_amount", "op": "gt", "value": 500},
                    action="escalate", priority=10,
                ),
                PolicyRule(
                    id="refund_no_verification", description="Cannot refund without identity verification",
                    conditions={"field": "identity_verified", "op": "not_equals", "value": True},
                    action="block", priority=20,
                ),
                PolicyRule(
                    id="refund_old_order", description="Orders older than 90 days cannot be refunded",
                    conditions={
                        "OR": [
                            {"field": "order_age_days", "op": "gt", "value": 90},
                            {"field": "order_age_days", "op": "any"},
                        ],
                    },
                    action="block", priority=15,
                ),
            ],
        )
        self.policies["data_access"] = PolicySet(
            name="data_access",
            rules=[
                PolicyRule(
                    id="pii_export_blocked", description="PII export to external destinations is blocked",
                    conditions={
                        "AND": [
                            {"field": "contains_pii", "op": "equals", "value": True},
                            {"field": "destination_external", "op": "equals", "value": True},
                        ],
                    },
                    action="block", priority=20,
                ),
                PolicyRule(
                    id="unauthorized_health_record", description="Health records require explicit authorization",
                    conditions={
                        "AND": [
                            {"field": "record_type", "op": "in", "value": ["health_record", "medical"]},
                            {"field": "authorized", "op": "not_equals", "value": True},
                        ],
                    },
                    action="block", priority=20,
                ),
            ],
        )
        self.policies["deployment"] = PolicySet(
            name="deployment",
            rules=[
                PolicyRule(
                    id="prod_deploy_no_approval", description="Production deploys require approval",
                    conditions={
                        "AND": [
                            {"field": "environment", "op": "equals", "value": "production"},
                            {"field": "approved", "op": "not_equals", "value": True},
                        ],
                    },
                    action="block", priority=20,
                ),
                PolicyRule(
                    id="single_replica", description="Production must have minimum 2 replicas",
                    conditions={
                        "AND": [
                            {"field": "environment", "op": "equals", "value": "production"},
                            {"field": "replicas", "op": "lt", "value": 2},
                        ],
                    },
                    action="warn", priority=10,
                ),
            ],
        )
        self.policies["payment_rules"] = PolicySet(
            name="payment_rules",
            rules=[
                PolicyRule(
                    id="large_transfer", description="Transfers over $100K require compliance review",
                    conditions={"field": "transfer_amount", "op": "gt", "value": 100000},
                    action="escalate", priority=15,
                ),
                PolicyRule(
                    id="offshore_transfer", description="Offshore transfers blocked without compliance sign-off",
                    conditions={
                        "AND": [
                            {"field": "destination_offshore", "op": "equals", "value": True},
                            {"field": "compliance_approved", "op": "not_equals", "value": True},
                        ],
                    },
                    action="block", priority=20,
                ),
            ],
        )
        self.policies["hr_discrimination"] = PolicySet(
            name="hr_discrimination",
            rules=[
                PolicyRule(
                    id="no_discriminatory_filter", description="Cannot filter candidates by protected characteristics",
                    conditions={
                        "OR": [
                            {"field": "filter_by_race", "op": "equals", "value": True},
                            {"field": "filter_by_gender", "op": "equals", "value": True},
                            {"field": "filter_by_age", "op": "equals", "value": True},
                            {"field": "filter_by_religion", "op": "equals", "value": True},
                        ],
                    },
                    action="block", priority=25,
                ),
            ],
        )

    def load_directory(self, directory: str) -> None:
        path = Path(directory).expanduser().resolve()
        for yaml_file in sorted(path.glob("*.yaml")):
            resolved_file = yaml_file.resolve()
            if path != resolved_file and path not in resolved_file.parents:
                continue
            with resolved_file.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            name = data.get("name", yaml_file.stem)
            rules: list[PolicyRule] = []
            for r in data.get("rules", []):
                rules.append(PolicyRule(
                    id=r.get("id", ""),
                    description=r.get("description", ""),
                    conditions=r.get("conditions", {}),
                    action=r.get("action", "warn"),
                    priority=r.get("priority", 0),
                ))
            self.policies[name] = PolicySet(name=name, rules=rules)

    def evaluate(self, policy_set_name: str, context: dict) -> list[str]:
        ps = self.policies.get(policy_set_name)
        if not ps:
            return []
        return ps.enforce(context)

    def evaluate_all(self, context: dict) -> list[str]:
        violations: list[str] = []
        for ps in self.policies.values():
            violations.extend(ps.enforce(context))
        return violations

    def list_policy_sets(self) -> list[str]:
        return list(self.policies.keys())
