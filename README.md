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
- Swagger docs at `/docs`
- Supported v0 job types: `echo`, `sleep`

## Job Lifecycle

```text
queued -> running -> succeeded
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
  "created_at": "2026-05-29T01:58:42.777684+00:00",
  "updated_at": "2026-05-29T01:59:13.601906+00:00"
}
```

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

- Retry support
- Multiple worker safety
- Worker heartbeat tracking
- PostgreSQL/Redis version
- Simple dashboard
- Real AI workloads such as summarization, OCR, embeddings, or image processing
