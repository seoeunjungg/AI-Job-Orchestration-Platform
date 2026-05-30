# db.py: database connection and setup

import os
import sqlite3

DB_PATH = os.getenv("DB_PATH", "jobs.db")


def init_db():
    db = sqlite3.connect(DB_PATH)

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            error TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            current_job_id INTEGER,
            started_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL
        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS job_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    ensure_column(db, "jobs", "attempts", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(db, "jobs", "max_attempts", "INTEGER NOT NULL DEFAULT 3")
    ensure_column(db, "jobs", "started_at", "TEXT")
    ensure_column(db, "jobs", "finished_at", "TEXT")

    db.commit()
    db.close()


def ensure_column(db, table_name: str, column_name: str, column_definition: str):
    columns = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_names = {column[1] for column in columns}

    if column_name not in column_names:
        db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
