# worker.py: Worker polls database -> finds queued job -> runs handler -> updates database

import json
import sqlite3
import time
from datetime import datetime, timezone

from app.db import DB_PATH
from app.models import STATUS_FAILED, STATUS_QUEUED, STATUS_RUNNING, STATUS_SUCCEEDED
from worker.handlers import HANDLERS


POLL_INTERVAL_SECONDS = 2


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def get_next_queued_job():
    db = sqlite3.connect(DB_PATH)
    row = db.execute(
        """
        SELECT id, job_type, payload
        FROM jobs
        WHERE status = ?
        ORDER BY id ASC
        LIMIT 1
        """,
        (STATUS_QUEUED,),
    ).fetchone()
    db.close()

    return row


def update_job_status(job_id: int, status: str, result=None, error=None):
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        UPDATE jobs
        SET status = ?, result = ?, error = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            json.dumps(result) if result is not None else None,
            error,
            utc_now(),
            job_id,
        ),
    )
    db.commit()
    db.close()


def run_job(row):
    job_id, job_type, payload_json = row
    payload = json.loads(payload_json)

    handler = HANDLERS.get(job_type)
    if handler is None:
        update_job_status(job_id, STATUS_FAILED, error=f"Unsupported job type: {job_type}")
        return

    update_job_status(job_id, STATUS_RUNNING)

    try:
        result = handler(payload)
    except Exception as exc:
        update_job_status(job_id, STATUS_FAILED, error=str(exc))
        return

    update_job_status(job_id, STATUS_SUCCEEDED, result=result)


def main():
    print("Worker started. Waiting for queued jobs...")

    while True:
        job = get_next_queued_job()

        if job is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        print(f"Processing job {job[0]} ({job[1]})")
        run_job(job)


if __name__ == "__main__":
    main()
