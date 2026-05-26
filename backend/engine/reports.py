from typing import Any


def build_release_report(run: dict[str, Any], gate: dict[str, Any] | None = None,
                         eval_report: dict[str, Any] | None = None,
                         issues: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    gate = gate or {}
    eval_report = eval_report or {}
    issues = issues or []
    critical = [issue for issue in issues if issue.get("severity") == "critical"]
    high = [issue for issue in issues if issue.get("severity") == "high"]
    decision = _decision(run, gate, eval_report, critical, high)
    return {
        "decision": decision,
        "run_id": run.get("id"),
        "score": run.get("score", 0),
        "status": run.get("status", ""),
        "summary": run.get("summary", ""),
        "gate": gate,
        "eval_report": {
            "passed": eval_report.get("passed"),
            "score": eval_report.get("score"),
            "finding_count": eval_report.get("finding_count", 0),
            "failed_count": eval_report.get("failed_count", 0),
        },
        "issue_summary": {
            "total": len(issues),
            "critical": len(critical),
            "high": len(high),
            "open": sum(1 for issue in issues if issue.get("status") == "open"),
        },
        "next_actions": _next_actions(decision, gate, eval_report, issues),
    }


def render_markdown_report(report: dict[str, Any], issues: list[dict[str, Any]] | None = None) -> str:
    issues = issues or []
    lines = [
        f"# Ozark Release Report: `{report['run_id']}`",
        "",
        f"**Decision:** {report['decision']}",
        f"**Score:** {report['score']}%",
        f"**Status:** {report['status']}",
        f"**Summary:** {report['summary']}",
        "",
        "## Gates",
    ]
    gate = report.get("gate", {})
    if gate:
        lines.append(f"- Passed: `{gate.get('passed')}`")
        for failure in gate.get("failures", []):
            lines.append(f"- Failure: {failure}")
    else:
        lines.append("- No gate result provided.")

    eval_report = report.get("eval_report", {})
    lines.extend([
        "",
        "## Evaluators",
        f"- Passed: `{eval_report.get('passed')}`",
        f"- Score: `{eval_report.get('score')}`",
        f"- Findings: `{eval_report.get('finding_count', 0)}`",
        f"- Failed findings: `{eval_report.get('failed_count', 0)}`",
        "",
        "## Issues",
    ])
    if issues:
        for issue in issues[:20]:
            lines.append(f"- **{issue.get('severity')}** `{issue.get('status')}` {issue.get('title')} ({issue.get('occurrence_count')}x)")
    else:
        lines.append("- No issues linked to this report.")

    lines.extend(["", "## Next Actions"])
    for action in report.get("next_actions", []):
        lines.append(f"- {action}")
    return "\n".join(lines) + "\n"


def _decision(run: dict[str, Any], gate: dict[str, Any], eval_report: dict[str, Any],
              critical: list[dict[str, Any]], high: list[dict[str, Any]]) -> str:
    if critical or gate.get("passed") is False:
        return "blocked"
    if high or eval_report.get("passed") is False or run.get("score", 0) < 80:
        return "needs_review"
    return "ready"


def _next_actions(decision: str, gate: dict[str, Any], eval_report: dict[str, Any],
                  issues: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []
    if gate.get("failures"):
        actions.extend(f"Fix release gate failure: {failure}" for failure in gate["failures"])
    failed = eval_report.get("failed_count", 0)
    if failed:
        actions.append(f"Review {failed} failed evaluator finding(s) and annotate true positives.")
    open_issues = [issue for issue in issues if issue.get("status") == "open"]
    if open_issues:
        actions.append("Promote confirmed open issues into regression datasets.")
    if decision == "ready":
        actions.append("Ship with monitoring; rerun Ozark on the next prompt/model/tool change.")
    return actions or ["No action required."]
