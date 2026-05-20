"""SQLite persistence layer for Ozark."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ozark.sqlite3"


def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(str(DB_PATH))


def init_db():
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


def upsert_agent(agent_id: str, name: str, description: str, config: dict, now: str):
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO agents VALUES (?, ?, ?, ?, ?)",
            (agent_id, name, description, json.dumps(config), now),
        )


def list_agents() -> list:
    with connect() as db:
        rows = db.execute(
            "SELECT id, name, description, config, created_at FROM agents ORDER BY created_at DESC"
        ).fetchall()
    return [
        {"id": r[0], "name": r[1], "description": r[2], "config": json.loads(r[3]), "created_at": r[4]}
        for r in rows
    ]


def get_agent(agent_id: str) -> dict | None:
    with connect() as db:
        row = db.execute(
            "SELECT id, name, description, config, created_at FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "name": row[1], "description": row[2], "config": json.loads(row[3]), "created_at": row[4]}


def upsert_scenario(scenario_id: str, name: str, body: dict, now: str):
    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO scenarios VALUES (?, ?, ?, ?)",
            (scenario_id, name, json.dumps(body), now),
        )


def list_scenarios() -> list:
    with connect() as db:
        rows = db.execute(
            "SELECT id, name, body, created_at FROM scenarios ORDER BY created_at ASC"
        ).fetchall()
    return [dict(json.loads(r[2]), id=r[0], created_at=r[3]) for r in rows]


def save_run(run_id: str, agent_id: str, score: int, status: str, summary: str, trace: dict, now: str):
    with connect() as db:
        db.execute(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, agent_id, score, status, summary, json.dumps(trace), now),
        )


def list_runs(limit: int = 20) -> list:
    with connect() as db:
        rows = db.execute(
            "SELECT id, agent_id, score, status, summary, trace, created_at FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"id": r[0], "agent_id": r[1], "score": r[2], "status": r[3], "summary": r[4],
         "trace": json.loads(r[5]), "created_at": r[6]}
        for r in rows
    ]
