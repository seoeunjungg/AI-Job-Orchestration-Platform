# main.py: API entry point and Client / Frontend -> FastAPI

import json
import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.db import DB_PATH, init_db
from app.events import record_job_event
from app.models import STATUS_QUEUED
from app.schemas import (
    JobEventResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobListItem,
    MetricsResponse,
    WorkerHealthResponse,
)
from worker.handlers import HANDLERS

app = FastAPI(title="Distributed AI Job Orchestration Platform")

init_db()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/jobs", response_model=JobCreateResponse)
def create_job(job: JobCreateRequest):
    if job.job_type not in HANDLERS:
        raise HTTPException(status_code=400, detail="Unsupported job type")

    now = datetime.now(timezone.utc).isoformat()

    db = sqlite3.connect(DB_PATH)
    cursor = db.execute(
        """
        INSERT INTO jobs(
            job_type,
            payload,
            status,
            result,
            error,
            attempts,
            max_attempts,
            created_at,
            updated_at,
            started_at,
            finished_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job.job_type,
            json.dumps(job.payload),
            STATUS_QUEUED,
            None,
            None,
            0,
            job.max_attempts,
            now,
            now,
            None,
            None,
        ),
    )

    db.commit()
    job_id = cursor.lastrowid
    db.close()
    record_job_event(job_id, "job_created", "Job was queued")

    return {
        "job_id": job_id,
        "status": STATUS_QUEUED,
        "job_type": job.job_type,
        "payload": job.payload,
        "max_attempts": job.max_attempts,
    }


@app.get("/jobs", response_model=list[JobListItem])
def list_jobs():
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        """
        SELECT id, job_type, status, attempts, max_attempts, error, created_at, updated_at
        FROM jobs
        ORDER BY id DESC
        LIMIT 50
        """
    ).fetchall()
    db.close()

    return [
        {
            "job_id": row[0],
            "job_type": row[1],
            "status": row[2],
            "attempts": row[3],
            "max_attempts": row[4],
            "error": row[5],
            "created_at": row[6],
            "updated_at": row[7],
        }
        for row in rows
    ]


@app.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: int):
    db = sqlite3.connect(DB_PATH)
    row = db.execute(
        """
        SELECT
            id,
            job_type,
            payload,
            status,
            result,
            error,
            attempts,
            max_attempts,
            created_at,
            updated_at,
            started_at,
            finished_at
        FROM jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()
    db.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": row[0],
        "job_type": row[1],
        "payload": json.loads(row[2]),
        "status": row[3],
        "result": json.loads(row[4]) if row[4] else None,
        "error": row[5],
        "attempts": row[6],
        "max_attempts": row[7],
        "created_at": row[8],
        "updated_at": row[9],
        "started_at": row[10],
        "finished_at": row[11],
        "duration_seconds": calculate_duration_seconds(row[10], row[11]),
    }


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        """
        SELECT status, attempts, max_attempts, started_at, finished_at
        FROM jobs
        """
    ).fetchall()
    db.close()

    total_jobs = len(rows)
    queued_jobs = count_status(rows, "queued")
    running_jobs = count_status(rows, "running")
    succeeded_jobs = count_status(rows, "succeeded")
    failed_jobs = count_status(rows, "failed")
    completed_jobs = succeeded_jobs + failed_jobs
    failed_after_retries = sum(
        1 for status, attempts, max_attempts, _, _ in rows
        if status == "failed" and attempts >= max_attempts
    )

    durations = [
        duration
        for _, _, _, started_at, finished_at in rows
        if (duration := calculate_duration_seconds(started_at, finished_at)) is not None
    ]

    return {
        "total_jobs": total_jobs,
        "queued_jobs": queued_jobs,
        "running_jobs": running_jobs,
        "succeeded_jobs": succeeded_jobs,
        "failed_jobs": failed_jobs,
        "success_rate": round(succeeded_jobs / completed_jobs, 4) if completed_jobs else 0,
        "failed_after_retries": failed_after_retries,
        "average_duration_seconds": round(sum(durations) / len(durations), 4) if durations else None,
    }


@app.get("/workers", response_model=list[WorkerHealthResponse])
def list_workers():
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        """
        SELECT id, status, current_job_id, started_at, last_seen_at
        FROM workers
        ORDER BY last_seen_at DESC
        """
    ).fetchall()
    db.close()

    now = datetime.now(timezone.utc)
    workers = []
    for worker_id, status, current_job_id, started_at, last_seen_at in rows:
        last_seen = datetime.fromisoformat(last_seen_at)
        seconds_since_last_seen = round((now - last_seen).total_seconds(), 4)

        workers.append(
            {
                "worker_id": worker_id,
                "status": status,
                "current_job_id": current_job_id,
                "started_at": started_at,
                "last_seen_at": last_seen_at,
                "seconds_since_last_seen": seconds_since_last_seen,
                "healthy": seconds_since_last_seen < 10,
            }
        )

    return workers


@app.get("/jobs/{job_id}/events", response_model=list[JobEventResponse])
def get_job_events(job_id: int):
    db = sqlite3.connect(DB_PATH)
    job = db.execute(
        """
        SELECT id
        FROM jobs
        WHERE id = ?
        """,
        (job_id,),
    ).fetchone()

    if job is None:
        db.close()
        raise HTTPException(status_code=404, detail="Job not found")

    rows = db.execute(
        """
        SELECT id, job_id, event_type, message, created_at
        FROM job_events
        WHERE job_id = ?
        ORDER BY id ASC
        """,
        (job_id,),
    ).fetchall()
    db.close()

    return [
        {
            "event_id": row[0],
            "job_id": row[1],
            "event_type": row[2],
            "message": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


def count_status(rows, status: str):
    return sum(1 for row in rows if row[0] == status)


def calculate_duration_seconds(started_at: str | None, finished_at: str | None):
    if not started_at or not finished_at:
        return None

    started = datetime.fromisoformat(started_at)
    finished = datetime.fromisoformat(finished_at)
    return round((finished - started).total_seconds(), 4)
