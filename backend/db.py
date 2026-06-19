"""SQLite persistence layer for Ozark.

Connection policy
-----------------
Every call site opens a short-lived connection via :func:`connect` (or
:func:`transaction` for multi-statement batches).  Connections are
configured for WAL mode, a 5 s busy-timeout, foreign keys, and a 64 MB
page cache — the defaults that let ``ThreadingHTTPServer`` serve
concurrent readers and a single writer without ``database is locked``
errors under normal load.

Schema evolution
----------------
:func:`init_db` creates every table with ``IF NOT EXISTS`` (idempotent
bootstrap) then walks a real migration ladder keyed on
``schema_version``.  Each step is additive and safe to re-run.
"""

from __future__ import annotations

import base64
import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ozark.sqlite3"

# Highest schema version the code understands.  Bump when adding a
# migration step in :func:`_run_migrations`.
SCHEMA_VERSION = 5

_PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA foreign_keys=ON",
    "PRAGMA busy_timeout=5000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA cache_size=-65536",  # ~64 MB page cache
)

_dir_ensured = False


def connect() -> sqlite3.Connection:
    """Open a short-lived, WAL-configured connection in autocommit mode.

    ``isolation_level=None`` puts the connection in autocommit so that
    PRAGMAs execute immediately and single-statement helpers commit per
    statement.  Multi-statement batches should use :func:`transaction`
    which issues explicit ``BEGIN``/``COMMIT``.
    """
    global _dir_ensured
    if not _dir_ensured:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _dir_ensured = True

    db = sqlite3.connect(str(DB_PATH), timeout=30.0, isolation_level=None)
    db.row_factory = sqlite3.Row
    for pragma in _PRAGMAS:
        db.execute(pragma)
    return db


@contextmanager
def closing_conn() -> Iterator[sqlite3.Connection]:
    """Yield a connection that is always closed on exit (autocommit)."""
    db = connect()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction() -> Iterator[sqlite3.Connection]:
    """Yield a connection wrapped in an explicit transaction.

    Issues ``BEGIN`` before yielding and ``COMMIT`` after the block
    exits cleanly.  Any exception triggers ``ROLLBACK`` so partial writes
    are never observed by concurrent readers.
    """
    db = connect()
    try:
        db.execute("BEGIN")
        yield db
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Schema bootstrap + migration ladder
# ---------------------------------------------------------------------------

_CREATE_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        config TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS scenarios (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        agent_id TEXT NOT NULL,
        score INTEGER NOT NULL,
        status TEXT NOT NULL,
        summary TEXT NOT NULL,
        trace TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS coverage (
        agent_id TEXT NOT NULL,
        report TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (agent_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        source TEXT NOT NULL,
        metadata TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dataset_items (
        id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        scenario TEXT NOT NULL,
        source_run_id TEXT NOT NULL,
        source_result_name TEXT NOT NULL,
        tags TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS eval_policies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        gates TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evaluators (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        evaluator_type TEXT NOT NULL,
        config TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS issues (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        signature TEXT NOT NULL,
        severity TEXT NOT NULL,
        status TEXT NOT NULL,
        first_seen_run_id TEXT NOT NULL,
        last_seen_run_id TEXT NOT NULL,
        occurrence_count INTEGER NOT NULL,
        metadata TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS annotations (
        id TEXT PRIMARY KEY,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        label TEXT NOT NULL,
        score REAL,
        comment TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )
    """,
)

# Migration step 5: add indexes that the original bootstrap omitted.
# Every index is created with IF NOT EXISTS so re-running is safe.
_INDEXES_V5 = (
    "CREATE INDEX IF NOT EXISTS idx_runs_agent_id ON runs(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_issues_signature ON issues(signature)",
    "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status)",
    "CREATE INDEX IF NOT EXISTS idx_issues_updated_at ON issues(updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_dataset_items_dataset_id ON dataset_items(dataset_id)",
    "CREATE INDEX IF NOT EXISTS idx_annotations_target ON annotations(target_type, target_id)",
    "CREATE INDEX IF NOT EXISTS idx_scenarios_name ON scenarios(name)",
)


def init_db() -> None:
    """Create tables if absent and run pending migrations."""
    with transaction() as db:
        for stmt in _CREATE_TABLES:
            db.execute(stmt)

        cur = db.execute("SELECT MAX(version) FROM schema_version")
        current = cur.fetchone()[0] or 0

        # v1-v4 were placeholders in the original codebase; record them so
        # existing databases don't re-run legacy no-op steps.
        for v in range(1, min(5, current + 1)):
            db.execute("INSERT OR IGNORE INTO schema_version VALUES (?)", (v,))
        if current < 4:
            for v in range(current + 1, 5):
                db.execute("INSERT OR IGNORE INTO schema_version VALUES (?)", (v,))

        # v5: add indexes for query performance under load.
        if current < 5:
            for stmt in _INDEXES_V5:
                db.execute(stmt)
            db.execute("INSERT OR IGNORE INTO schema_version VALUES (5)")


# ---------------------------------------------------------------------------
# Cursor helpers (keyset pagination for list_runs)
# ---------------------------------------------------------------------------

def _encode_cursor(created_at: str, run_id: str) -> str:
    raw = f"{created_at}|{run_id}".encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[str, str] | None:
    try:
        pad = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(cursor + pad).decode("utf-8")
        ts, _, rid = raw.partition("|")
        if not ts or not rid:
            return None
        return ts, rid
    except (ValueError, UnicodeDecodeError):
        return None


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

def upsert_agent(
    agent_id: str, name: str, description: str, config: dict, now: str
) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT OR REPLACE INTO agents VALUES (?, ?, ?, ?, ?)",
            (agent_id, name, description, json.dumps(config), now),
        )


def list_agents() -> list[dict]:
    with closing_conn() as db:
        rows = db.execute(
            "SELECT id, name, description, config, created_at FROM agents ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "config": json.loads(r[3]),
            "created_at": r[4],
        }
        for r in rows
    ]


def get_agent(agent_id: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            "SELECT id, name, description, config, created_at FROM agents WHERE id = ?",
            (agent_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "config": json.loads(row[3]),
        "created_at": row[4],
    }


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

def save_run(
    run_id: str,
    agent_id: str,
    score: int,
    status: str,
    summary: str,
    trace: dict,
    now: str,
) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, agent_id, score, status, summary, json.dumps(trace), now),
        )


def save_runs_batch(rows: Sequence[dict]) -> None:
    """Persist multiple runs in a single transaction (for experiments)."""
    with transaction() as db:
        for row in rows:
            db.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    row["id"],
                    row["agent_id"],
                    row["score"],
                    row["status"],
                    row["summary"],
                    json.dumps(row["trace"]),
                    row["now"],
                ),
            )


def get_run_by_id(run_id: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            "SELECT id, agent_id, score, status, summary, trace, created_at FROM runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "agent_id": row[1],
        "score": row[2],
        "status": row[3],
        "summary": row[4],
        "trace": json.loads(row[5]),
        "created_at": row[6],
    }


def get_run_scenarios(run_id: str) -> list[dict]:
    run = get_run_by_id(run_id)
    if not run:
        return []
    return run["trace"].get("results", [])


def list_runs(
    limit: int = 20,
    before: str | None = None,
) -> dict:
    """Return a page of run summaries **without** loading the trace blob.

    Keyset-paginated on ``(created_at DESC, id DESC)`` so that paging
    through thousands of runs is O(limit) regardless of offset.

    Returns ``{"runs": [...], "next_cursor": str | None}``.
    """
    limit = max(1, min(limit, 200))
    params: list[Any] = [limit]

    if before:
        decoded = _decode_cursor(before)
        if decoded:
            ts, rid = decoded
            rows = (
                # Rows older than the cursor, or same timestamp with a
                # lexicographically smaller id.
                "SELECT id, agent_id, score, status, summary, created_at "
                "FROM runs "
                "WHERE created_at < ? OR (created_at = ? AND id < ?) "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                (ts, ts, rid, limit),
            )
        else:
            rows = (
                "SELECT id, agent_id, score, status, summary, created_at "
                "FROM runs ORDER BY created_at DESC, id DESC LIMIT ?",
                params,
            )
    else:
        rows = (
            "SELECT id, agent_id, score, status, summary, created_at "
            "FROM runs ORDER BY created_at DESC, id DESC LIMIT ?",
            params,
        )

    with closing_conn() as db:
        result = db.execute(*rows).fetchall()

    runs = [
        {
            "id": r[0],
            "agent_id": r[1],
            "score": r[2],
            "status": r[3],
            "summary": r[4],
            "created_at": r[5],
        }
        for r in result
    ]

    next_cursor = None
    if len(runs) == limit:
        last = runs[-1]
        next_cursor = _encode_cursor(last["created_at"], last["id"])

    return {"runs": runs, "next_cursor": next_cursor}


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def save_coverage(agent_id: str, report: dict, now: str) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT OR REPLACE INTO coverage VALUES (?, ?, ?)",
            (agent_id, json.dumps(report), now),
        )


def get_coverage(agent_id: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            "SELECT report FROM coverage WHERE agent_id = ?", (agent_id,)
        ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

def create_dataset(
    dataset_id: str, name: str, description: str, source: str, metadata: dict, now: str
) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT OR REPLACE INTO datasets VALUES (?, ?, ?, ?, ?, ?)",
            (dataset_id, name, description, source, json.dumps(metadata), now),
        )


def list_datasets() -> list[dict]:
    with closing_conn() as db:
        rows = db.execute(
            """
            SELECT d.id, d.name, d.description, d.source, d.metadata, d.created_at,
                   COUNT(i.id) AS item_count
            FROM datasets d
            LEFT JOIN dataset_items i ON i.dataset_id = d.id
            GROUP BY d.id
            ORDER BY d.created_at DESC
            """
        ).fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "source": r[3],
            "metadata": json.loads(r[4]),
            "created_at": r[5],
            "item_count": r[6],
        }
        for r in rows
    ]


def get_dataset(dataset_id: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            "SELECT id, name, description, source, metadata, created_at FROM datasets WHERE id = ?",
            (dataset_id,),
        ).fetchone()
        if not row:
            return None
        items = db.execute(
            "SELECT id, scenario, source_run_id, source_result_name, tags, created_at "
            "FROM dataset_items WHERE dataset_id = ? ORDER BY created_at ASC",
            (dataset_id,),
        ).fetchall()
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "source": row[3],
        "metadata": json.loads(row[4]),
        "created_at": row[5],
        "items": [
            {
                "id": item[0],
                "scenario": json.loads(item[1]),
                "source_run_id": item[2],
                "source_result_name": item[3],
                "tags": json.loads(item[4]),
                "created_at": item[5],
            }
            for item in items
        ],
    }


def add_dataset_item(
    item_id: str,
    dataset_id: str,
    scenario: dict,
    source_run_id: str,
    source_result_name: str,
    tags: list[str],
    now: str,
) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT OR REPLACE INTO dataset_items VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                item_id,
                dataset_id,
                json.dumps(scenario),
                source_run_id,
                source_result_name,
                json.dumps(tags),
                now,
            ),
        )


def add_dataset_items_batch(items: Sequence[dict]) -> int:
    """Insert many dataset items in one transaction. Returns count inserted."""
    if not items:
        return 0
    with transaction() as db:
        for item in items:
            db.execute(
                "INSERT OR REPLACE INTO dataset_items VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    item["id"],
                    item["dataset_id"],
                    json.dumps(item["scenario"]),
                    item["source_run_id"],
                    item["source_result_name"],
                    json.dumps(item["tags"]),
                    item["now"],
                ),
            )
    return len(items)


# ---------------------------------------------------------------------------
# Eval policies + evaluators
# ---------------------------------------------------------------------------

def upsert_eval_policy(policy_id: str, name: str, gates: dict, now: str) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT OR REPLACE INTO eval_policies VALUES (?, ?, ?, ?)",
            (policy_id, name, json.dumps(gates), now),
        )


def get_eval_policy(policy_id: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            "SELECT id, name, gates, created_at FROM eval_policies WHERE id = ?",
            (policy_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "gates": json.loads(row[2]),
        "created_at": row[3],
    }


def list_eval_policies() -> list[dict]:
    with closing_conn() as db:
        rows = db.execute(
            "SELECT id, name, gates, created_at FROM eval_policies ORDER BY created_at DESC"
        ).fetchall()
    return [
        {"id": r[0], "name": r[1], "gates": json.loads(r[2]), "created_at": r[3]}
        for r in rows
    ]


def upsert_evaluator(
    evaluator_id: str, name: str, evaluator_type: str, config: dict, now: str
) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT OR REPLACE INTO evaluators VALUES (?, ?, ?, ?, ?)",
            (evaluator_id, name, evaluator_type, json.dumps(config), now),
        )


def list_evaluators() -> list[dict]:
    with closing_conn() as db:
        rows = db.execute(
            "SELECT id, name, evaluator_type, config, created_at FROM evaluators ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "type": r[2],
            "config": json.loads(r[3]),
            "created_at": r[4],
        }
        for r in rows
    ]


def get_evaluator(evaluator_id: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            "SELECT id, name, evaluator_type, config, created_at FROM evaluators WHERE id = ?",
            (evaluator_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "type": row[2],
        "config": json.loads(row[3]),
        "created_at": row[4],
    }


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

_ISSUE_COLUMNS = (
    "id, title, signature, severity, status, first_seen_run_id, "
    "last_seen_run_id, occurrence_count, metadata, created_at, updated_at"
)


def _issue_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row[0],
        "title": row[1],
        "signature": row[2],
        "severity": row[3],
        "status": row[4],
        "first_seen_run_id": row[5],
        "last_seen_run_id": row[6],
        "occurrence_count": row[7],
        "metadata": json.loads(row[8]),
        "created_at": row[9],
        "updated_at": row[10],
    }


def upsert_issue(issue: dict) -> None:
    with closing_conn() as db:
        db.execute(
            """
            INSERT OR REPLACE INTO issues
            (id, title, signature, severity, status, first_seen_run_id, last_seen_run_id,
             occurrence_count, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue["id"],
                issue["title"],
                issue["signature"],
                issue["severity"],
                issue["status"],
                issue["first_seen_run_id"],
                issue["last_seen_run_id"],
                issue["occurrence_count"],
                json.dumps(issue.get("metadata", {})),
                issue["created_at"],
                issue["updated_at"],
            ),
        )


def upsert_issues_batch(issues: Sequence[dict]) -> None:
    """Persist all issues in a single transaction (one COMMIT, not N)."""
    if not issues:
        return
    with transaction() as db:
        for issue in issues:
            db.execute(
                """
                INSERT OR REPLACE INTO issues
                (id, title, signature, severity, status, first_seen_run_id, last_seen_run_id,
                 occurrence_count, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    issue["id"],
                    issue["title"],
                    issue["signature"],
                    issue["severity"],
                    issue["status"],
                    issue["first_seen_run_id"],
                    issue["last_seen_run_id"],
                    issue["occurrence_count"],
                    json.dumps(issue.get("metadata", {})),
                    issue["created_at"],
                    issue["updated_at"],
                ),
            )


def get_issue_by_signature(signature: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            f"SELECT {_ISSUE_COLUMNS} FROM issues WHERE signature = ?",
            (signature,),
        ).fetchone()
    return _issue_from_row(row) if row else None


def get_issue(issue_id: str) -> dict | None:
    with closing_conn() as db:
        row = db.execute(
            f"SELECT {_ISSUE_COLUMNS} FROM issues WHERE id = ?",
            (issue_id,),
        ).fetchone()
    return _issue_from_row(row) if row else None


def list_issues(status: str | None = None) -> list[dict]:
    with closing_conn() as db:
        if status:
            rows = db.execute(
                f"SELECT {_ISSUE_COLUMNS} FROM issues WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = db.execute(
                f"SELECT {_ISSUE_COLUMNS} FROM issues ORDER BY updated_at DESC"
            ).fetchall()
    return [_issue_from_row(row) for row in rows]


def update_issue_status(issue_id: str, status: str, now: str) -> None:
    with closing_conn() as db:
        db.execute(
            "UPDATE issues SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, issue_id),
        )


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------

def add_annotation(
    annotation_id: str,
    target_type: str,
    target_id: str,
    label: str,
    score: float | None,
    comment: str,
    now: str,
) -> None:
    with closing_conn() as db:
        db.execute(
            "INSERT OR REPLACE INTO annotations VALUES (?, ?, ?, ?, ?, ?, ?)",
            (annotation_id, target_type, target_id, label, score, comment, now),
        )


def list_annotations(
    target_type: str | None = None, target_id: str | None = None
) -> list[dict]:
    with closing_conn() as db:
        if target_type and target_id:
            rows = db.execute(
                "SELECT id, target_type, target_id, label, score, comment, created_at "
                "FROM annotations WHERE target_type = ? AND target_id = ? ORDER BY created_at DESC",
                (target_type, target_id),
            ).fetchall()
        elif target_type:
            rows = db.execute(
                "SELECT id, target_type, target_id, label, score, comment, created_at "
                "FROM annotations WHERE target_type = ? ORDER BY created_at DESC",
                (target_type,),
            ).fetchall()
        elif target_id:
            rows = db.execute(
                "SELECT id, target_type, target_id, label, score, comment, created_at "
                "FROM annotations WHERE target_id = ? ORDER BY created_at DESC",
                (target_id,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT id, target_type, target_id, label, score, comment, created_at "
                "FROM annotations ORDER BY created_at DESC"
            ).fetchall()
    return [
        {
            "id": r[0],
            "target_type": r[1],
            "target_id": r[2],
            "label": r[3],
            "score": r[4],
            "comment": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]
