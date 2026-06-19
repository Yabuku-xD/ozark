"""Tests for the run pipeline (run_pipeline.py).

Covers finalize_run, record_issues batching, and the async job handler
end-to-end with a real (temp) database.
"""

from __future__ import annotations

import time

from backend import db, models
from backend.engine.run_pipeline import RunPipeline, record_issues


def _minimal_run_body() -> dict:
    return {
        "id": "run-test-1",
        "agent_id": "test-agent",
        "score": 95,
        "status": "passed",
        "summary": "5/5 passed",
        "results": [
            {
                "scenario_name": "s1",
                "passed": True,
                "score": 100,
                "called_tools": ["lookup_user"],
                "violations": [],
                "trace": [],
                "latency_ms": 10,
                "risk_level": "low",
                "user_impact": "low",
            }
        ],
        "scenario_count": 1,
        "passed_count": 1,
        "failed_count": 0,
    }


def test_finalize_run_persists_and_evaluates():
    body = _minimal_run_body()
    result = RunPipeline().finalize_run(run_body=body, agent_id="test-agent")

    assert result.gate["passed"] is True
    assert result.run["score"] == 95
    # The run was saved to the DB.
    fetched = db.get_run_by_id("run-test-1")
    assert fetched is not None
    assert fetched["score"] == 95
    # Evaluation block was merged into the body.
    assert "evaluation" in fetched["trace"]


def test_record_issues_uses_batch_write():
    body = _minimal_run_body()
    eval_report = {
        "passed": False,
        "findings": [
            {
                "evaluator_id": "ev-1",
                "name": "Secret leak",
                "passed": False,
                "score": 0,
                "severity": "high",
                "message": "Secret detected",
            }
        ],
    }
    issues = record_issues(body, eval_report)
    assert len(issues) == 1
    assert issues[0]["severity"] == "high"
    # The issue was persisted.
    from backend.engine.issues import issue_signature

    sig = issue_signature(eval_report["findings"][0])
    fetched = db.get_issue_by_signature(sig)
    assert fetched is not None
    assert fetched["occurrence_count"] == 1


def test_run_simulation_job_handler_completes():
    """Enqueue a run_simulation job with a real builtin agent and let the
    worker execute it, then assert it succeeds."""
    from backend import db as _db
    from backend.engine import jobs as jobs_mod

    # Bootstrap builtin agents so the handler can find sample-support-agent.
    from backend.server import BUILTIN_AGENTS

    now = models.iso_now()
    for ba in BUILTIN_AGENTS:
        _db.upsert_agent(ba["id"], ba["name"], ba["description"], ba["config"], now)

    job_id = jobs_mod.enqueue(
        "run_simulation",
        {
            "agent_id": "sample-support-agent",
            "scenario_count": 8,
            "max_workers": 2,
        },
        total=8,
    )

    # Start the worker and wait for completion.
    jobs_mod.start_worker()
    job = None
    for _ in range(40):
        job = jobs_mod.get_job(job_id)
        if job["status"] in ("succeeded", "failed"):
            break
        time.sleep(0.5)

    assert job is not None
    assert job["status"] == "succeeded", f"job failed: {job.get('error')}"
    assert job["result"]["run"]["scenario_count"] == 8
