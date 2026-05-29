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
        SELECT id, job_type, payload, attempts, max_attempts
        FROM jobs
        WHERE status = ?
        ORDER BY id ASC
        LIMIT 1
        """,
        (STATUS_QUEUED,),
    ).fetchone()
    db.close()

    return row


def mark_running(job_id: int, attempts: int):
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        UPDATE jobs
        SET status = ?, attempts = ?, error = ?, started_at = COALESCE(started_at, ?), updated_at = ?
        WHERE id = ?
        """,
        (
            STATUS_RUNNING,
            attempts,
            None,
            utc_now(),
            utc_now(),
            job_id,
        ),
    )
    db.commit()
    db.close()


def mark_retry(job_id: int, error: str):
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        UPDATE jobs
        SET status = ?, error = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            STATUS_QUEUED,
            error,
            utc_now(),
            job_id,
        ),
    )
    db.commit()
    db.close()


def mark_succeeded(job_id: int, result):
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        UPDATE jobs
        SET status = ?, result = ?, error = ?, finished_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            STATUS_SUCCEEDED,
            json.dumps(result),
            None,
            utc_now(),
            utc_now(),
            job_id,
        ),
    )
    db.commit()
    db.close()


def mark_failed(job_id: int, error: str):
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        UPDATE jobs
        SET status = ?, error = ?, finished_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            STATUS_FAILED,
            error,
            utc_now(),
            utc_now(),
            job_id,
        ),
    )
    db.commit()
    db.close()


def run_job(row):
    job_id, job_type, payload_json, attempts, max_attempts = row
    payload = json.loads(payload_json)
    next_attempt = attempts + 1

    handler = HANDLERS.get(job_type)
    if handler is None:
        mark_failed(job_id, f"Unsupported job type: {job_type}")
        return

    mark_running(job_id, next_attempt)

    try:
        handler_payload = {**payload, "_attempt": next_attempt}
        result = handler(handler_payload)
    except Exception as exc:
        if next_attempt < max_attempts:
            mark_retry(job_id, str(exc))
        else:
            mark_failed(job_id, str(exc))
        return

    mark_succeeded(job_id, result)


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
