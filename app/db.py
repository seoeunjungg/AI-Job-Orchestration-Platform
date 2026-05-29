# db.py: database connection (connects to SQLite)

import sqlite3

DB_PATH = "jobs.db"

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
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    db.commit()
    db.close()
