"""SQLite-backed job queue + worker for long-running eval pipelines.

Why a job queue?
----------------
``POST /api/runs`` and ``POST /api/experiments`` execute the full
simulation pipeline inline.  A 50 000-scenario run ties up an HTTP
worker thread for minutes with no progress visible to the client.

This module adds a durable job table (``jobs``) and a single background
worker thread that drains the queue.  Endpoints enqueue a job and
return immediately with ``202 Accepted`` + a job id; clients poll
``GET /api/jobs/{id}`` for status.

The queue lives in the same SQLite database as everything else, so it
inherits WAL mode, the busy-timeout, and crash-durability with zero
new infrastructure.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections.abc import Callable
from typing import Any

from .. import db
from ..models import iso_now

LOGGER = logging.getLogger(__name__)

# Job lifecycle states.
PENDING = "pending"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"

_ACTIVE: set[str] = set()
_ACTIVE_LOCK = threading.Lock()

_WORKER: threading.Thread | None = None
_WORKER_LOCK = threading.Lock()
_STOP = threading.Event()


# ---------------------------------------------------------------------------
# Schema + persistence
# ---------------------------------------------------------------------------

_CREATE_JOBS = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT NOT NULL,
    result TEXT,
    error TEXT,
    progress INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    updated_at TEXT NOT NULL
)
"""


def init_jobs() -> None:
    """Create the jobs table if absent (idempotent, additive)."""
    with db.transaction() as conn:
        conn.execute(_CREATE_JOBS)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)"
        )


def enqueue(
    kind: str,
    payload: dict[str, Any],
    *,
    total: int = 0,
    start: bool = True,
) -> str:
    """Insert a pending job and optionally wake the worker.

    Returns the job id.  Pass ``start=False`` in tests to enqueue without
    starting the worker thread (so the job stays pending for inspection).
    """
    job_id = "job-" + uuid.uuid4().hex[:12]
    now = iso_now()
    with db.closing_conn() as conn:
        conn.execute(
            """
            INSERT INTO jobs
            (id, kind, status, payload, progress, total,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (job_id, kind, PENDING, json.dumps(payload), total, now, now),
        )
    if start:
        _wake_worker()
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    with db.closing_conn() as conn:
        row = conn.execute(
            "SELECT id, kind, status, payload, result, error, progress, total, "
            "created_at, started_at, finished_at, updated_at FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
    if not row:
        return None
    return _job_from_row(row)


def list_jobs(status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 200))
    with db.closing_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT id, kind, status, payload, result, error, progress, total, "
                "created_at, started_at, finished_at, updated_at FROM jobs "
                "WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, kind, status, payload, result, error, progress, total, "
                "created_at, started_at, finished_at, updated_at FROM jobs "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [_job_from_row(row) for row in rows]


def _job_from_row(row) -> dict[str, Any]:
    return {
        "id": row[0],
        "kind": row[1],
        "status": row[2],
        "payload": json.loads(row[3]) if row[3] else {},
        "result": json.loads(row[4]) if row[4] else None,
        "error": row[5],
        "progress": row[6],
        "total": row[7],
        "created_at": row[8],
        "started_at": row[9],
        "finished_at": row[10],
        "updated_at": row[11],
    }


def _claim_next_job() -> dict[str, Any] | None:
    """Atomically claim the oldest pending job (CAS via a single UPDATE)."""
    now = iso_now()
    with db.transaction() as conn:
        row = conn.execute(
            "SELECT id FROM jobs WHERE status = ? ORDER BY created_at ASC LIMIT 1",
            (PENDING,),
        ).fetchone()
        if not row:
            return None
        job_id = row[0]
        # Mark as running only if still pending (guards against races).
        cur = conn.execute(
            "UPDATE jobs SET status = ?, started_at = ?, updated_at = ? "
            "WHERE id = ? AND status = ?",
            (RUNNING, now, now, job_id, PENDING),
        )
        if cur.rowcount == 0:
            return None
    return get_job(job_id)


def _update_progress(job_id: str, progress: int, total: int) -> None:
    now = iso_now()
    with db.closing_conn() as conn:
        conn.execute(
            "UPDATE jobs SET progress = ?, total = ?, updated_at = ? WHERE id = ?",
            (progress, total, now, job_id),
        )


def _complete_job(job_id: str, result: dict[str, Any]) -> None:
    now = iso_now()
    with db.closing_conn() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, result = ?, progress = total, "
            "finished_at = ?, updated_at = ? WHERE id = ?",
            (SUCCEEDED, json.dumps(result), now, now, job_id),
        )


def _fail_job(job_id: str, error: str) -> None:
    now = iso_now()
    with db.closing_conn() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, error = ?, finished_at = ?, updated_at = ? "
            "WHERE id = ?",
            (FAILED, error, now, now, job_id),
        )


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

# Registry of job handlers.  Each handler receives (payload, progress_fn)
# and returns a JSON-serialisable result dict.  ``progress_fn(done, total)``
# updates the job row so clients can poll progress.
JobHandler = Callable[[dict[str, Any], Callable[[int, int], None]], dict[str, Any]]
_HANDLERS: dict[str, JobHandler] = {}


def register_handler(kind: str) -> Callable[[JobHandler], JobHandler]:
    """Decorator: register a handler for a job ``kind``."""

    def deco(fn: JobHandler) -> JobHandler:
        _HANDLERS[kind] = fn
        return fn

    return deco


def _run_one(job: dict[str, Any]) -> None:
    job_id = job["id"]
    kind = job["kind"]
    handler = _HANDLERS.get(kind)
    if handler is None:
        _fail_job(job_id, f"No handler registered for job kind: {kind}")
        return

    def progress_fn(done: int, total: int) -> None:
        _update_progress(job_id, done, total)

    try:
        result = handler(job["payload"], progress_fn)
        _complete_job(job_id, result)
    except Exception as exc:  # noqa: BLE001 — worker must survive any failure
        LOGGER.exception("Job %s (%s) failed", job_id, kind)
        _fail_job(job_id, str(exc))


def _worker_loop() -> None:
    LOGGER.info("Ozark job worker started")
    while not _STOP.is_set():
        try:
            job = _claim_next_job()
            if job is None:
                _STOP.wait(timeout=1.0)
                continue
            with _ACTIVE_LOCK:
                _ACTIVE.add(job["id"])
            _run_one(job)
            with _ACTIVE_LOCK:
                _ACTIVE.discard(job["id"])
        except Exception:  # noqa: BLE001 — loop must survive handler errors
            LOGGER.exception("Job worker loop error")
    LOGGER.info("Ozark job worker stopped")


def _wake_worker() -> None:
    _STOP.clear()
    global _WORKER
    with _WORKER_LOCK:
        if _WORKER is None or not _WORKER.is_alive():
            _WORKER = threading.Thread(
                target=_worker_loop, name="ozark-worker", daemon=True
            )
            _WORKER.start()
    # Nudge an idle worker out of its 1 s wait.
    _STOP.set()
    _STOP.clear()


def start_worker() -> None:
    """Start the background worker (called once at server bootstrap)."""
    _STOP.clear()
    _wake_worker()


def active_job_count() -> int:
    with _ACTIVE_LOCK:
        return len(_ACTIVE)
