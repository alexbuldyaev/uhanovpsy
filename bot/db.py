import json
import sqlite3
from datetime import datetime, timezone

from .scoring import TestResult


class Storage:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS checkups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                answers TEXT NOT NULL,
                results TEXT NOT NULL
            )"""
        )
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON checkups(user_id, created_at)")
        self.conn.commit()

    def save(self, user_id: int, answers_json: str, results: list[TestResult]) -> None:
        summary = [
            {"id": r.test_id, "total": r.total, "level": r.level, "label": r.label,
             **({"subscales": {x.id: x.total for x in r.subscales}} if r.subscales else {})}
            for r in results
        ]
        self.conn.execute(
            "INSERT INTO checkups (user_id, created_at, answers, results) VALUES (?, ?, ?, ?)",
            (user_id, datetime.now(timezone.utc).isoformat(), answers_json,
             json.dumps(summary, ensure_ascii=False)),
        )
        self.conn.commit()

    def history(self, user_id: int, limit: int = 5) -> list[dict]:
        rows = self.conn.execute(
            "SELECT created_at, results FROM checkups WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [{"created_at": r["created_at"], "results": json.loads(r["results"])} for r in rows]

    def delete_user(self, user_id: int) -> int:
        cur = self.conn.execute("DELETE FROM checkups WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return cur.rowcount
