"""Tests for the background job queue (jobs.py).

Covers enqueue/claim lifecycle, progress reporting, and failure handling.
"""

from __future__ import annotations

from backend.engine import jobs


def test_enqueue_and_get_job():
    job_id = jobs.enqueue("run_simulation", {"agent_id": "x"}, total=10, start=False)
    job = jobs.get_job(job_id)
    assert job is not None
    assert job["status"] == jobs.PENDING
    assert job["total"] == 10
    assert job["payload"]["agent_id"] == "x"


def test_get_job_not_found():
    assert jobs.get_job("does-not-exist") is None


def test_list_jobs_filters_by_status():
    j1 = jobs.enqueue("run_simulation", {"agent_id": "a"}, start=False)
    j2 = jobs.enqueue("run_simulation", {"agent_id": "b"}, start=False)
    pending = jobs.list_jobs(status=jobs.PENDING)
    ids = {j["id"] for j in pending}
    assert j1 in ids
    assert j2 in ids


def test_claim_next_job_advances_to_running():
    job_id = jobs.enqueue("run_simulation", {"agent_id": "x"}, total=5, start=False)
    claimed = jobs._claim_next_job()
    assert claimed is not None
    assert claimed["id"] == job_id
    assert claimed["status"] == jobs.RUNNING


def test_complete_job_sets_succeeded():
    job_id = jobs.enqueue("run_simulation", {"agent_id": "x"}, start=False)
    jobs._claim_next_job()  # move to running
    jobs._complete_job(job_id, {"run": {"id": "run-1", "score": 90}})
    job = jobs.get_job(job_id)
    assert job["status"] == jobs.SUCCEEDED
    assert job["result"]["run"]["score"] == 90
    assert job["progress"] == job["total"]


def test_fail_job_sets_failed_with_error():
    job_id = jobs.enqueue("run_simulation", {"agent_id": "x"}, start=False)
    jobs._claim_next_job()
    jobs._fail_job(job_id, "boom")
    job = jobs.get_job(job_id)
    assert job["status"] == jobs.FAILED
    assert job["error"] == "boom"


def test_unknown_handler_fails_job():
    job_id = jobs.enqueue("nonexistent_kind", {}, start=False)
    jobs._run_one(jobs.get_job(job_id))
    job = jobs.get_job(job_id)
    assert job["status"] == jobs.FAILED
    assert "No handler" in job["error"]


def test_registered_handler_executes():
    @jobs.register_handler("test_kind")
    def _handler(payload, progress_fn):
        progress_fn(1, 2)
        progress_fn(2, 2)
        return {"ok": True, "got": payload["x"]}

    job_id = jobs.enqueue("test_kind", {"x": 42}, total=2)
    jobs._run_one(jobs.get_job(job_id))
    job = jobs.get_job(job_id)
    assert job["status"] == jobs.SUCCEEDED
    assert job["result"] == {"ok": True, "got": 42}
    assert job["progress"] == 2


def test_update_progress():
    job_id = jobs.enqueue("run_simulation", {"agent_id": "x"}, total=10, start=False)
    jobs._update_progress(job_id, 5, 10)
    job = jobs.get_job(job_id)
    assert job["progress"] == 5
    assert job["total"] == 10


def test_init_jobs_is_idempotent():
    # conftest already called init_jobs once; calling again must not error.
    jobs.init_jobs()
    jobs.init_jobs()
    with jobs.db.closing_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    # jobs from earlier tests may exist, just confirm no error + table present.
    assert count >= 0
