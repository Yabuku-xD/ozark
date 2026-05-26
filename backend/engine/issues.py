import hashlib
import uuid
from typing import Any

from .. import models


def findings_to_issues(run: dict[str, Any], eval_report: dict[str, Any], existing_by_signature) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for finding in eval_report.get("findings", []):
        if finding.get("passed"):
            continue
        signature = issue_signature(finding)
        if signature not in grouped:
            grouped[signature] = {"finding": finding, "count": 0}
        grouped[signature]["count"] += 1
        grouped[signature]["finding"] = finding

    issues: list[dict[str, Any]] = []
    for signature, data in grouped.items():
        finding = data["finding"]
        count = data["count"]
        existing = existing_by_signature(signature)
        now = models.iso_now()
        if existing:
            issue = dict(existing)
            issue["last_seen_run_id"] = run.get("id", "")
            issue["occurrence_count"] = int(issue.get("occurrence_count", 0)) + count
            issue["updated_at"] = now
            metadata = issue.get("metadata", {})
            metadata["last_finding"] = finding
            issue["metadata"] = metadata
        else:
            issue = {
                "id": "issue-" + uuid.uuid4().hex[:10],
                "title": finding.get("message") or finding.get("name") or "Evaluator failure",
                "signature": signature,
                "severity": finding.get("severity", "medium"),
                "status": "open",
                "first_seen_run_id": run.get("id", ""),
                "last_seen_run_id": run.get("id", ""),
                "occurrence_count": count,
                "metadata": {"first_finding": finding, "last_finding": finding},
                "created_at": now,
                "updated_at": now,
            }
        issues.append(issue)
    return issues


def issue_signature(finding: dict[str, Any]) -> str:
    raw = "|".join([
        finding.get("evaluator_id", ""),
        finding.get("severity", ""),
        finding.get("message", ""),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
