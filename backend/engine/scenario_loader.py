import os
from pathlib import Path
from typing import Any

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


class ScenarioLoader:
    """Loads scenario templates from YAML files with support for custom packs."""

    INDUSTRY_FILES: dict[str, str] = {
        "customer_support": "customer_support.yaml",
        "code_assistant": "code_assistant.yaml",
        "data_analysis": "data_analysis.yaml",
        "autonomous_ops": "autonomous_ops.yaml",
        "sales_agent": "sales_agent.yaml",
        "finance_agent": "finance_agent.yaml",
        "healthcare_agent": "healthcare_agent.yaml",
        "recruiting_agent": "recruiting_agent.yaml",
    }

    _industry_cache: dict[str, list[dict[str, Any]]] | None = None
    _adversarial_cache: list[dict[str, Any]] | None = None
    _edge_case_cache: list[dict[str, Any]] | None = None

    @classmethod
    def _load_yaml(cls, filename: str) -> dict:
        import yaml
        path = SCENARIOS_DIR / filename
        if not path.exists():
            return {}
        with open(path) as f:
            return yaml.safe_load(f) or {}

    @classmethod
    def load_industry_templates(cls) -> dict[str, list[dict[str, Any]]]:
        if cls._industry_cache is not None:
            return cls._industry_cache
        templates: dict[str, list[dict[str, Any]]] = {}
        for agent_type, filename in cls.INDUSTRY_FILES.items():
            data = cls._load_yaml(filename)
            items = data.get("templates", [])
            cleaned: list[dict[str, Any]] = []
            for item in items:
                entry: dict[str, Any] = {
                    "prompt": item.get("prompt", ""),
                    "type": item.get("type", "happy_path"),
                    "difficulty": item.get("difficulty", "medium"),
                }
                if item.get("expected_tools"):
                    entry["expected_tools"] = item["expected_tools"]
                if item.get("blocked_tools"):
                    entry["blocked_tools"] = item["blocked_tools"]
                if item.get("sensitive_data"):
                    entry["sensitive_data"] = item["sensitive_data"]
                cleaned.append(entry)
            templates[agent_type] = cleaned
        cls._industry_cache = templates
        return templates

    @classmethod
    def load_adversarial_patterns(cls) -> list[dict[str, Any]]:
        if cls._adversarial_cache is not None:
            return cls._adversarial_cache
        data = cls._load_yaml("adversarial.yaml")
        items = data.get("templates", [])
        patterns: list[dict[str, Any]] = []
        for item in items:
            patterns.append({
                "prompt": item.get("prompt", ""),
                "type": item.get("type", "security"),
                "difficulty": item.get("difficulty", "critical"),
                "category": item.get("category", "unknown"),
            })
        cls._adversarial_cache = patterns
        return patterns

    @classmethod
    def load_edge_case_templates(cls) -> list[dict[str, Any]]:
        if cls._edge_case_cache is not None:
            return cls._edge_case_cache
        data = cls._load_yaml("edge_cases.yaml")
        items = data.get("templates", [])
        templates: list[dict[str, Any]] = []
        for item in items:
            templates.append({
                "prompt": item.get("prompt", ""),
                "type": item.get("type", "edge_case"),
                "difficulty": item.get("difficulty", "medium"),
                "category": item.get("category", "unknown"),
            })
        cls._edge_case_cache = templates
        return templates

    @classmethod
    def load_custom_pack(cls, pack_path: str) -> dict[str, list[dict[str, Any]]]:
        import yaml
        path = Path(pack_path)
        if not path.exists():
            raise FileNotFoundError(f"Scenario pack not found: {pack_path}")
        if path.is_dir():
            templates: dict[str, list[dict[str, Any]]] = {}
            for f in sorted(path.glob("*.yaml")):
                with open(f) as fh:
                    data = yaml.safe_load(fh) or {}
                agent_type = data.get("agent_type", f.stem)
                templates.setdefault(agent_type, []).extend(data.get("templates", []))
            return templates
        else:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return {data.get("agent_type", "custom"): data.get("templates", [])}

    @classmethod
    def clear_cache(cls) -> None:
        cls._industry_cache = None
        cls._adversarial_cache = None
        cls._edge_case_cache = None

    @classmethod
    def discover_custom_packs(cls, custom_dir: str | None = None) -> list[str]:
        search_dir = Path(custom_dir) if custom_dir else SCENARIOS_DIR
        if not search_dir.exists():
            return []
        packs: list[str] = []
        for entry in sorted(search_dir.iterdir()):
            if entry.is_dir():
                if any(entry.glob("*.yaml")):
                    packs.append(str(entry))
            elif entry.suffix in (".yaml", ".yml") and entry.stem not in {
                "customer_support", "code_assistant", "data_analysis", "autonomous_ops",
                "sales_agent", "finance_agent", "healthcare_agent", "recruiting_agent",
                "adversarial", "edge_cases",
            }:
                packs.append(str(entry))
        return packs
