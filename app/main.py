# main.py: API entry point and Client / Frontend -> FastAPI

import json
import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.db import DB_PATH, init_db
from app.models import STATUS_QUEUED
from app.schemas import JobCreateRequest, JobCreateResponse, JobDetailResponse, JobListItem
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
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job.job_type,
            json.dumps(job.payload),
            STATUS_QUEUED,
            None,
            None,
            now,
            now,
        ),
    )

    db.commit()
    job_id = cursor.lastrowid
    db.close()

    return {
        "job_id": job_id,
        "status": STATUS_QUEUED,
        "job_type": job.job_type,
        "payload": job.payload,
    }


@app.get("/jobs", response_model=list[JobListItem])
def list_jobs():
    db = sqlite3.connect(DB_PATH)
    rows = db.execute(
        """
        SELECT id, job_type, status, error, created_at, updated_at
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
            "error": row[3],
            "created_at": row[4],
            "updated_at": row[5],
        }
        for row in rows
    ]


@app.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: int):
    db = sqlite3.connect(DB_PATH)
    row = db.execute(
        """
        SELECT id, job_type, payload, status, result, error, created_at, updated_at
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
        "created_at": row[6],
        "updated_at": row[7],
    }
