# Distributed AI Job Orchestration Platform

A minimal backend platform for submitting asynchronous jobs, storing them in a SQLite-backed queue, and executing them with a background worker.

The current version focuses on the orchestration core:

1. A client submits a job through FastAPI.
2. The API stores the job as `queued`.
3. A worker polls for queued jobs.
4. The worker executes the matching job handler.
5. The worker stores the result and updates the final status.

## Current Features

- FastAPI job submission API
- SQLite job store
- Background worker process
- Job lifecycle tracking
- Retry tracking with configurable `max_attempts`
- Runtime timing with `started_at`, `finished_at`, and `duration_seconds`
- Reliability metrics endpoint
- Worker heartbeat monitoring
- Swagger docs at `/docs`
- Supported v0 job types: `echo`, `sleep`, `fail_once`

## Job Lifecycle

```text
queued -> running -> succeeded
queued -> running -> queued -> running -> succeeded
queued -> running -> failed
```

## API Endpoints

### Health Check

```text
GET /health
```

### Create Job

```text
POST /jobs
```

Example request:

```json
{
  "job_type": "echo",
  "max_attempts": 3,
  "payload": {
    "message": "hello"
  }
}
```

Example response:

```json
{
  "job_id": 1,
  "status": "queued",
  "job_type": "echo",
  "max_attempts": 3,
  "payload": {
    "message": "hello"
  }
}
```

### List Recent Jobs

```text
GET /jobs
```

### Get Job Status

```text
GET /jobs/{job_id}
```

Example response after the worker completes an `echo` job:

```json
{
  "job_id": 1,
  "job_type": "echo",
  "payload": {
    "message": "hello"
  },
  "status": "succeeded",
  "result": {
    "message": "hello"
  },
  "error": null,
  "attempts": 1,
  "max_attempts": 3,
  "created_at": "2026-05-29T01:58:42.777684+00:00",
  "updated_at": "2026-05-29T01:59:13.601906+00:00",
  "started_at": "2026-05-29T01:59:13.599361+00:00",
  "finished_at": "2026-05-29T01:59:13.601906+00:00",
  "duration_seconds": 0.0025
}
```

### Reliability Metrics

```text
GET /metrics
```

Example response:

```json
{
  "total_jobs": 10,
  "queued_jobs": 0,
  "running_jobs": 0,
  "succeeded_jobs": 9,
  "failed_jobs": 1,
  "success_rate": 0.9,
  "failed_after_retries": 1,
  "average_duration_seconds": 0.2541
}
```

### Worker Health

```text
GET /workers
```

Example response:

```json
[
  {
    "worker_id": "MacBook-Pro-231-a1b2c3d4",
    "status": "idle",
    "current_job_id": null,
    "started_at": "2026-05-29T02:30:00.000000+00:00",
    "last_seen_at": "2026-05-29T02:30:06.000000+00:00",
    "seconds_since_last_seen": 1.2041,
    "healthy": true
  }
]
```

Workers update their heartbeat while idle and while processing jobs. The API marks a worker unhealthy if it has not been seen recently.

## Demo Jobs

```json
{
  "job_type": "sleep",
  "max_attempts": 3,
  "payload": {
    "seconds": 3
  }
}
```

```json
{
  "job_type": "fail_once",
  "max_attempts": 3,
  "payload": {}
}
```

`fail_once` intentionally fails on the first attempt and succeeds on retry, which demonstrates retry behavior.

## Run Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

In another terminal, start the worker:

```bash
python -m worker.worker
```

Open the Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Project Structure

```text
app/
  main.py       FastAPI routes
  schemas.py    Request and response models
  db.py         SQLite setup
  models.py     Shared job status constants

worker/
  handlers.py   Supported job type implementations
  worker.py     Polling loop that executes queued jobs
```

## Next Planned Improvements

- Multiple worker safety
- PostgreSQL/Redis version
- Simple dashboard
- Real AI workloads such as summarization, OCR, embeddings, or image processing
- Kubernetes deployment and autoscaling
