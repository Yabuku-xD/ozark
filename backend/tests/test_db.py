"""Tests for the SQLite data layer (db.py).

Covers connection handling, WAL mode, indexes, migration ladder,
keyset pagination, and batch writes.
"""

from __future__ import annotations

import pytest

from backend import db


def test_init_db_creates_all_tables():
    with db.closing_conn() as conn:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    expected = {
        "agents", "scenarios", "runs", "coverage", "datasets",
        "dataset_items", "eval_policies", "evaluators", "issues",
        "annotations", "schema_version", "jobs",
    }
    assert expected.issubset(tables), f"missing: {expected - tables}"


def test_wal_mode_enabled():
    with db.closing_conn() as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"


def test_schema_version_is_current():
    with db.closing_conn() as conn:
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version == db.SCHEMA_VERSION


def test_indexes_exist():
    with db.closing_conn() as conn:
        names = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
    assert "idx_runs_created_at" in names
    assert "idx_issues_signature" in names
    assert "idx_issues_status" in names


def test_save_and_get_run_roundtrip():
    trace = {"id": "run-abc", "score": 88, "results": [{"scenario_name": "s1"}]}
    db.save_run("run-abc", "agent-1", 88, "passed", "summary", trace, "2026-01-01T00:00:00Z")
    fetched = db.get_run_by_id("run-abc")
    assert fetched is not None
    assert fetched["score"] == 88
    assert fetched["trace"]["results"][0]["scenario_name"] == "s1"


def test_list_runs_excludes_trace_blob():
    db.save_run("r1", "a", 90, "passed", "s1", {"id": "r1"}, "2026-01-01T00:00:00Z")
    db.save_run("r2", "a", 80, "passed", "s2", {"id": "r2"}, "2026-01-02T00:00:00Z")
    page = db.list_runs(limit=10)
    assert "trace" not in page["runs"][0]
    assert page["runs"][0]["id"] == "r2"  # newest first


def test_list_runs_keyset_pagination():
    for i in range(5):
        db.save_run(
            f"run-{i}", "a", 50 + i, "passed", f"s{i}",
            {"id": f"run-{i}"}, f"2026-01-0{i+1}T00:00:00Z",
        )
    page1 = db.list_runs(limit=2)
    assert len(page1["runs"]) == 2
    assert page1["next_cursor"] is not None

    page2 = db.list_runs(limit=2, before=page1["next_cursor"])
    assert len(page2["runs"]) == 2
    # No overlap between pages.
    ids1 = {r["id"] for r in page1["runs"]}
    ids2 = {r["id"] for r in page2["runs"]}
    assert ids1.isdisjoint(ids2)


def test_upsert_issues_batch_single_transaction():
    now = "2026-01-01T00:00:00Z"
    issues = [
        {
            "id": f"issue-{i}", "title": f"t{i}", "signature": f"sig-{i}",
            "severity": "high", "status": "open",
            "first_seen_run_id": "r1", "last_seen_run_id": "r1",
            "occurrence_count": 1, "metadata": {}, "created_at": now, "updated_at": now,
        }
        for i in range(5)
    ]
    db.upsert_issues_batch(issues)
    assert len(db.list_issues()) == 5


def test_add_dataset_items_batch():
    now = "2026-01-01T00:00:00Z"
    db.create_dataset("ds1", "test", "", "test", {}, now)
    items = [
        {
            "id": f"item-{i}", "dataset_id": "ds1",
            "scenario": {"name": f"s{i}"}, "source_run_id": "r1",
            "source_result_name": f"s{i}", "tags": ["regression"], "now": now,
        }
        for i in range(3)
    ]
    added = db.add_dataset_items_batch(items)
    assert added == 3
    ds = db.get_dataset("ds1")
    assert len(ds["items"]) == 3


def test_transaction_rolls_back_on_error():
    with pytest.raises(RuntimeError), db.transaction() as conn:
        conn.execute("INSERT INTO runs VALUES ('x','a',1,'p','s','{}','now')")
        raise RuntimeError("boom")
    # The insert should have been rolled back.
    assert db.get_run_by_id("x") is None


def test_save_runs_batch():
    now = "2026-01-01T00:00:00Z"
    rows = [
        {
            "id": f"batch-{i}", "agent_id": "a", "score": 70 + i,
            "status": "passed", "summary": f"b{i}",
            "trace": {"id": f"batch-{i}"}, "now": now,
        }
        for i in range(3)
    ]
    db.save_runs_batch(rows)
    page = db.list_runs(limit=10)
    ids = {r["id"] for r in page["runs"]}
    assert {"batch-0", "batch-1", "batch-2"}.issubset(ids)
