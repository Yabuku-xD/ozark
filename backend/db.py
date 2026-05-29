import json
import sqlite3
from typing import Any
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ozark.sqlite3"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                trace TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS coverage (
                agent_id TEXT NOT NULL,
                report TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (agent_id)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS dataset_items (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                scenario TEXT NOT NULL,
                source_run_id TEXT NOT NULL,
                source_result_name TEXT NOT NULL,
                tags TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS eval_policies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                gates TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS evaluators (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                evaluator_type TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
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
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                id TEXT PRIMARY KEY,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                label TEXT NOT NULL,
                score REAL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        cur = db.execute("SELECT MAX(version) FROM schema_version")
        current = cur.fetchone()[0] or 0
        if current < 1:
            db.execute("INSERT OR IGNORE INTO schema_version VALUES (1)")
        if current < 2:
            # version 2 placeholder — coverage table already created above
            db.execute("INSERT OR IGNORE INTO schema_version VALUES (2)")
        if current < 3:
            db.execute("INSERT OR IGNORE INTO schema_version VALUES (3)")
        if current < 4:
            db.execute("INSERT OR IGNORE INTO schema_version VALUES (4)")


def upsert_agent(
    agent_id: str, name: str, description: str, config: dict, now: str
) -> None:
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO agents VALUES (?, ?, ?, ?, ?)",
            (agent_id, name, description, json.dumps(config), now),
        )


def list_agents() -> list[dict]:
    with connect() as db:
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
    with connect() as db:
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


def upsert_scenario(scenario_id: str, name: str, body: dict, now: str) -> None:
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO scenarios VALUES (?, ?, ?, ?)",
            (scenario_id, name, json.dumps(body), now),
        )


def list_scenarios() -> list[dict]:
    with connect() as db:
        rows = db.execute(
            "SELECT id, name, body, created_at FROM scenarios ORDER BY created_at ASC"
        ).fetchall()
    return [dict(json.loads(r[2]), id=r[0], created_at=r[3]) for r in rows]


def save_run(
    run_id: str,
    agent_id: str,
    score: int,
    status: str,
    summary: str,
    trace: dict,
    now: str,
) -> None:
    with connect() as db:
        db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, agent_id, score, status, summary, json.dumps(trace), now),
        )


def get_run_by_id(run_id: str) -> dict | None:
    with connect() as db:
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


def list_runs(limit: int = 20) -> list[dict]:
    with connect() as db:
        rows = db.execute(
            "SELECT id, agent_id, score, status, summary, trace, created_at FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": r[0],
            "agent_id": r[1],
            "score": r[2],
            "status": r[3],
            "summary": r[4],
            "trace": json.loads(r[5]),
            "created_at": r[6],
        }
        for r in rows
    ]


def save_coverage(agent_id: str, report: dict, now: str) -> None:
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO coverage VALUES (?, ?, ?)",
            (agent_id, json.dumps(report), now),
        )


def get_coverage(agent_id: str) -> dict | None:
    with connect() as db:
        row = db.execute(
            "SELECT report FROM coverage WHERE agent_id = ?", (agent_id,)
        ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def create_dataset(
    dataset_id: str, name: str, description: str, source: str, metadata: dict, now: str
) -> None:
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO datasets VALUES (?, ?, ?, ?, ?, ?)",
            (dataset_id, name, description, source, json.dumps(metadata), now),
        )


def list_datasets() -> list[dict]:
    with connect() as db:
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
    with connect() as db:
        row = db.execute(
            "SELECT id, name, description, source, metadata, created_at FROM datasets WHERE id = ?",
            (dataset_id,),
        ).fetchone()
        items = db.execute(
            "SELECT id, scenario, source_run_id, source_result_name, tags, created_at FROM dataset_items WHERE dataset_id = ? ORDER BY created_at ASC",
            (dataset_id,),
        ).fetchall()
    if not row:
        return None
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
    with connect() as db:
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


def upsert_eval_policy(policy_id: str, name: str, gates: dict, now: str) -> None:
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO eval_policies VALUES (?, ?, ?, ?)",
            (policy_id, name, json.dumps(gates), now),
        )


def get_eval_policy(policy_id: str) -> dict | None:
    with connect() as db:
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
    with connect() as db:
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
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO evaluators VALUES (?, ?, ?, ?, ?)",
            (evaluator_id, name, evaluator_type, json.dumps(config), now),
        )


def list_evaluators() -> list[dict]:
    with connect() as db:
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
    with connect() as db:
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


def upsert_issue(issue: dict) -> None:
    with connect() as db:
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
    with connect() as db:
        row = db.execute(
            "SELECT id, title, signature, severity, status, first_seen_run_id, last_seen_run_id, occurrence_count, metadata, created_at, updated_at FROM issues WHERE signature = ?",
            (signature,),
        ).fetchone()
    return _issue_from_row(row) if row else None


def get_issue(issue_id: str) -> dict | None:
    with connect() as db:
        row = db.execute(
            "SELECT id, title, signature, severity, status, first_seen_run_id, last_seen_run_id, occurrence_count, metadata, created_at, updated_at FROM issues WHERE id = ?",
            (issue_id,),
        ).fetchone()
    return _issue_from_row(row) if row else None


def list_issues(status: str | None = None) -> list[dict]:
    with connect() as db:
        if status:
            rows = db.execute(
                """
                SELECT id, title, signature, severity, status, first_seen_run_id,
                       last_seen_run_id, occurrence_count, metadata, created_at, updated_at
                FROM issues
                WHERE status = ?
                ORDER BY updated_at DESC
                """,
                (status,),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, title, signature, severity, status, first_seen_run_id,
                       last_seen_run_id, occurrence_count, metadata, created_at, updated_at
                FROM issues
                ORDER BY updated_at DESC
                """
            ).fetchall()
    return [_issue_from_row(row) for row in rows]


def update_issue_status(issue_id: str, status: str, now: str) -> None:
    with connect() as db:
        db.execute(
            "UPDATE issues SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, issue_id),
        )


def add_annotation(
    annotation_id: str,
    target_type: str,
    target_id: str,
    label: str,
    score: float | None,
    comment: str,
    now: str,
) -> None:
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO annotations VALUES (?, ?, ?, ?, ?, ?, ?)",
            (annotation_id, target_type, target_id, label, score, comment, now),
        )


def list_annotations(
    target_type: str | None = None, target_id: str | None = None
) -> list[dict]:
    with connect() as db:
        if target_type and target_id:
            rows = db.execute(
                """
                SELECT id, target_type, target_id, label, score, comment, created_at
                FROM annotations
                WHERE target_type = ? AND target_id = ?
                ORDER BY created_at DESC
                """,
                (target_type, target_id),
            ).fetchall()
        elif target_type:
            rows = db.execute(
                """
                SELECT id, target_type, target_id, label, score, comment, created_at
                FROM annotations
                WHERE target_type = ?
                ORDER BY created_at DESC
                """,
                (target_type,),
            ).fetchall()
        elif target_id:
            rows = db.execute(
                """
                SELECT id, target_type, target_id, label, score, comment, created_at
                FROM annotations
                WHERE target_id = ?
                ORDER BY created_at DESC
                """,
                (target_id,),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT id, target_type, target_id, label, score, comment, created_at
                FROM annotations
                ORDER BY created_at DESC
                """
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


def _issue_from_row(row) -> dict:
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


class AgentStore:
    def upsert(
        self,
        agent_id: str,
        name: str,
        description: str,
        config: dict[str, Any],
        now: str,
    ) -> None:
        upsert_agent(agent_id, name, description, config, now)

    def list(self) -> list[dict[str, Any]]:
        return list_agents()

    def get(self, agent_id: str) -> dict[str, Any] | None:
        return get_agent(agent_id)


class RunStore:
    def save(
        self,
        run_id: str,
        agent_id: str,
        score: int,
        status: str,
        summary: str,
        body: dict[str, Any],
        now: str,
    ) -> None:
        save_run(run_id, agent_id, score, status, summary, body, now)

    def get(self, run_id: str) -> dict[str, Any] | None:
        return get_run_by_id(run_id)

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        return list_runs(limit)

    def scenarios(self, run_id: str) -> list[dict[str, Any]]:
        return get_run_scenarios(run_id)

    def save_coverage(self, agent_id: str, report: dict[str, Any], now: str) -> None:
        save_coverage(agent_id, report, now)

    def get_coverage(self, agent_id: str) -> dict[str, Any] | None:
        return get_coverage(agent_id)


class DatasetStore:
    def create(
        self,
        dataset_id: str,
        name: str,
        description: str,
        source: str,
        metadata: dict[str, Any],
        now: str,
    ) -> None:
        create_dataset(dataset_id, name, description, source, metadata, now)

    def list(self) -> list[dict[str, Any]]:
        return list_datasets()

    def get(self, dataset_id: str) -> dict[str, Any] | None:
        return get_dataset(dataset_id)

    def add_item(
        self,
        item_id: str,
        dataset_id: str,
        scenario: dict[str, Any],
        source_run_id: str,
        source_scenario_name: str,
        tags: list[str],
        now: str,
    ) -> None:
        add_dataset_item(
            item_id,
            dataset_id,
            scenario,
            source_run_id,
            source_scenario_name,
            tags,
            now,
        )


class PolicyStore:
    def upsert_eval_policy(
        self, policy_id: str, name: str, gates: dict[str, Any], now: str
    ) -> None:
        upsert_eval_policy(policy_id, name, gates, now)

    def get_eval_policy(self, policy_id: str) -> dict[str, Any] | None:
        return get_eval_policy(policy_id)

    def list_eval_policies(self) -> list[dict[str, Any]]:
        return list_eval_policies()

    def upsert_evaluator(
        self,
        evaluator_id: str,
        name: str,
        evaluator_type: str,
        config: dict[str, Any],
        now: str,
    ) -> None:
        upsert_evaluator(evaluator_id, name, evaluator_type, config, now)

    def list_evaluators(self) -> list[dict[str, Any]]:
        return list_evaluators()

    def get_evaluator(self, evaluator_id: str) -> dict[str, Any] | None:
        return get_evaluator(evaluator_id)
