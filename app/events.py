# events.py: shared job event logging helpers

import sqlite3
from datetime import datetime, timezone

from app.db import DB_PATH


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def record_job_event(job_id: int, event_type: str, message: str):
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        INSERT INTO job_events (job_id, event_type, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (job_id, event_type, message, utc_now()),
    )
    db.commit()
    db.close()
