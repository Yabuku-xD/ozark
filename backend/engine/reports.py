from typing import Any


def build_release_report(
    run_body: dict[str, Any],
    gate: dict[str, Any] | None = None,
    eval_report: dict[str, Any] | None = None,
    issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    gate = gate or {}
    eval_report = eval_report or {}
    issues = issues or []
    issue_counts = _issue_counts(issues)
    decision = _decision(run_body, gate, eval_report, issue_counts)
    return {
        "decision": decision,
        "run_id": _value(run_body, "id", None),
        "score": _value(run_body, "score", 0),
        "status": _value(run_body, "status", ""),
        "summary": _value(run_body, "summary", ""),
        "gate": gate,
        "eval_report": {
            "passed": _value(eval_report, "passed", None),
            "score": _value(eval_report, "score", None),
            "finding_count": _value(eval_report, "finding_count", 0),
            "failed_count": _value(eval_report, "failed_count", 0),
        },
        "risk_summary": _value(run_body, "risk_summary", {}),
        "issue_summary": {
            "total": len(issues),
            "critical": issue_counts["critical"],
            "high": issue_counts["high"],
            "open": issue_counts["open"],
        },
        "next_actions": _next_actions(decision, gate, eval_report, issues),
    }


def render_markdown_report(
    report: dict[str, Any],
    issues: list[dict[str, Any]] | None = None,
) -> str:
    return (
        "\n".join(
            (
                f"# Ozark Release Report: `{report['run_id']}`",
                "",
                f"**Decision:** {report['decision']}",
                f"**Score:** {report['score']}%",
                f"**Status:** {report['status']}",
                f"**Summary:** {report['summary']}",
                "",
                "## Risk Summary",
                _risk_section(report),
                "",
                "## Gates",
                _gate_section(report.get("gate", {})),
                "",
                "## Evaluators",
                _eval_section(report.get("eval_report", {})),
                "",
                "## Issues",
                _issue_section(issues or []),
                "",
                "## Next Actions",
                _actions_section(report),
            )
        )
        + "\n"
    )


def _risk_section(report: dict[str, Any]) -> str:
    risk_summary = report.get("risk_summary", {})
    if not risk_summary:
        return "- No risk summary provided."
    return "\n".join(risk_report_lines(risk_summary))


def _gate_section(gate: dict[str, Any]) -> str:
    if not gate:
        return "- No gate result provided."
    failures = "\n".join(
        f"- Failure: {failure}" for failure in gate.get("failures", [])
    )
    passed = f"- Passed: `{gate.get('passed')}`"
    return f"{passed}\n{failures}" if failures else passed


def _eval_section(eval_report: dict[str, Any]) -> str:
    return "\n".join(
        (
            f"- Passed: `{eval_report.get('passed')}`",
            f"- Score: `{eval_report.get('score')}`",
            f"- Findings: `{eval_report.get('finding_count', 0)}`",
            f"- Failed findings: `{eval_report.get('failed_count', 0)}`",
        )
    )


def _issue_section(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "- No issues linked to this report."
    return "\n".join(
        f"- **{issue.get('severity')}** `{issue.get('status')}` {issue.get('title')} ({issue.get('occurrence_count')}x)"
        for issue in issues[:20]
    )


def _actions_section(report: dict[str, Any]) -> str:
    return "\n".join(f"- {action}" for action in report.get("next_actions", []))


def _value(mapping: dict[str, Any], key: str, default: Any) -> Any:
    return mapping.get(key, default)


def risk_report_lines(risk_summary: dict[str, Any]) -> list[str]:
    failures_by_level = risk_summary.get("failures_by_level", {})
    by_level = risk_summary.get("by_level", {})
    return [
        f"- Risk-adjusted pass rate: `{risk_summary.get('risk_adjusted_pass_rate')}`",
        f"- Safety-critical failures: `{risk_summary.get('safety_critical_failed', 0)}` / `{risk_summary.get('safety_critical_total', 0)}`",
        f"- High-risk failures: `{failures_by_level.get('high', 0)}` / `{by_level.get('high', 0)}`",
        f"- Critical-risk failures: `{failures_by_level.get('critical', 0)}` / `{by_level.get('critical', 0)}`",
    ]


def _issue_counts(issues: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "open": 0}
    for issue in issues:
        severity = issue.get("severity")
        if severity in {"critical", "high"}:
            counts[severity] += 1
        if issue.get("status") == "open":
            counts["open"] += 1
    return counts


def _decision(
    run_body: dict[str, Any],
    gate: dict[str, Any],
    eval_report: dict[str, Any],
    issue_counts: dict[str, int],
) -> str:
    if issue_counts["critical"] > 0 or gate.get("passed") is False:
        return "blocked"
    if (
        issue_counts["high"] > 0
        or eval_report.get("passed") is False
        or _value(run_body, "score", 0) < 80
    ):
        return "needs_review"
    return "ready"


def _next_actions(
    decision: str,
    gate: dict[str, Any],
    eval_report: dict[str, Any],
    issues: list[dict[str, Any]],
) -> list[str]:
    actions: list[str] = []
    if gate.get("failures"):
        actions.extend(
            f"Fix release gate failure: {failure}" for failure in gate["failures"]
        )
    failed = eval_report.get("failed_count", 0)
    if failed:
        actions.append(
            f"Review {failed} failed evaluator finding(s) and annotate true positives.",
        )
    open_issues = [issue for issue in issues if issue.get("status") == "open"]
    if open_issues:
        actions.append("Promote confirmed open issues into regression datasets.")
    if decision == "ready":
        actions.append(
            "Ship with monitoring; rerun Ozark on the next prompt/model/tool change.",
        )
    return actions or ["No action required."]
