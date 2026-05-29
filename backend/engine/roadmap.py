from typing import Any


ROADMAP_ITEMS: list[dict[str, Any]] = [
    {
        "id": "risk-first-evaluation",
        "title": "Risk-first evaluation model",
        "priority": "P0",
        "status": "implemented",
        "why": "Separate harmless failures from high-impact and safety-critical failures.",
        "keeps_optimal": "Uses deterministic metadata and weighted summaries; no model call required.",
    },
    {
        "id": "coverage-gaps",
        "title": "Coverage and gap analysis",
        "priority": "P0",
        "status": "implemented",
        "why": "Expose untested tools, guardrails, and critical-risk scenario gaps.",
        "keeps_optimal": "Summarizes coverage from existing traces during the run.",
    },
    {
        "id": "risk-gates",
        "title": "Risk-aware release gates",
        "priority": "P0",
        "status": "implemented",
        "why": "Block releases on high-risk, critical-risk, or safety-critical failures even when aggregate score looks good.",
        "keeps_optimal": "Extends existing gate checks with O(n) summary counters.",
    },
    {
        "id": "deterministic-evaluators",
        "title": "Deterministic evaluator expansion",
        "priority": "P1",
        "status": "implemented",
        "why": "Add an auditable risk evaluator alongside regex, tool, latency, and rubric evaluators.",
        "keeps_optimal": "Runs locally and deterministically for CI reliability.",
    },
    {
        "id": "accessible-dashboard",
        "title": "Accessible risk dashboard",
        "priority": "P1",
        "status": "implemented",
        "why": "Show risk-adjusted pass rate, safety-critical failures, gates, and next actions without relying on color alone.",
        "keeps_optimal": "Static, semantic React sections with no heavy runtime dependency.",
    },
]


def product_roadmap() -> dict[str, Any]:
    return {
        "principles": [
            "Prefer deterministic checks before probabilistic judges.",
            "Treat non-functional requirements as release requirements.",
            "Make high-risk failures visible even when aggregate scores pass.",
            "Keep local-first workflows usable in CI without external services.",
            "Expose accessible, text-first status summaries in the UI and reports.",
        ],
        "items": ROADMAP_ITEMS,
    }
