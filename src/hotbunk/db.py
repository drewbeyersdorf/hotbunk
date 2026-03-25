"""SQLite persistence layer for HotBunk daemon state.

Stores job history, events, and throttle tracking. WAL mode for
concurrent reads from CLI while daemon writes.
"""

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

from .accounts import HOTBUNK_DIR


DEFAULT_DB_PATH = HOTBUNK_DIR / "hotbunk.db"
THROTTLE_DURATION = 1800  # 30 minutes
COOLDOWN_DURATION = 3600  # 1 hour


class HotBunkDB:
    """SQLite database for daemon state persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                command TEXT NOT NULL,
                account TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                exit_code INTEGER,
                pid INTEGER,
                started_at REAL NOT NULL,
                completed_at REAL,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                account TEXT,
                message TEXT,
                timestamp REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS throttles (
                account TEXT PRIMARY KEY,
                throttled_at REAL NOT NULL
            );
        """)
        self._conn.commit()

    def record_job(self, job_type: str, command: str, account: str, pid: int = 0) -> str:
        job_id = str(uuid.uuid4())[:8]
        self._conn.execute(
            "INSERT INTO jobs (id, job_type, command, account, status, pid, started_at) VALUES (?, ?, ?, ?, 'running', ?, ?)",
            (job_id, job_type, command, account, pid, time.time()),
        )
        self._conn.commit()
        return job_id

    def complete_job(self, job_id: str, exit_code: int = 0, error: str = ""):
        self._conn.execute(
            "UPDATE jobs SET status = ?, exit_code = ?, error = ?, completed_at = ? WHERE id = ?",
            ("completed" if exit_code == 0 else "failed", exit_code, error, time.time(), job_id),
        )
        self._conn.commit()

    def list_jobs(self, status: Optional[str] = None, limit: int = 50) -> list[dict]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY started_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def record_event(self, event_type: str, account: str, message: str):
        self._conn.execute(
            "INSERT INTO events (event_type, account, message, timestamp) VALUES (?, ?, ?, ?)",
            (event_type, account, message, time.time()),
        )
        self._conn.commit()

    def list_events(self, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def record_throttle(self, account: str, timestamp: Optional[float] = None):
        ts = timestamp or time.time()
        self._conn.execute(
            "INSERT OR REPLACE INTO throttles (account, throttled_at) VALUES (?, ?)",
            (account, ts),
        )
        self._conn.commit()

    def is_throttled(self, account: str, duration: float = COOLDOWN_DURATION) -> bool:
        row = self._conn.execute(
            "SELECT throttled_at FROM throttles WHERE account = ?", (account,)
        ).fetchone()
        if not row:
            return False
        return (time.time() - row["throttled_at"]) < duration

    def close(self):
        self._conn.close()
