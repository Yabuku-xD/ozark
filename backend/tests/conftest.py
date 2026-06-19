"""Shared pytest fixtures for the Ozark backend test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import db  # noqa: E402
from backend.engine import jobs  # noqa: E402


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    """Redirect the SQLite DB to a per-test temp file.

    Also stops the job worker thread and clears its handler registry
    state so tests don't leak pending jobs from prior tests.
    """
    # Stop any worker started by a previous test.
    jobs._STOP.set()
    if jobs._WORKER is not None:
        jobs._WORKER.join(timeout=2.0)
    with jobs._WORKER_LOCK:
        jobs._WORKER = None
    jobs._STOP.clear()
    with jobs._ACTIVE_LOCK:
        jobs._ACTIVE.clear()

    db_path = tmp_path / "test.sqlite3"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    monkeypatch.setattr(db, "_dir_ensured", False)
    db.init_db()
    jobs.init_jobs()
    yield

    # Teardown: stop the worker again in case the test started it.
    jobs._STOP.set()
    if jobs._WORKER is not None:
        jobs._WORKER.join(timeout=2.0)
    with jobs._WORKER_LOCK:
        jobs._WORKER = None

