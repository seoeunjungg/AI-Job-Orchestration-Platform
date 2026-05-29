# schemas.py: job validation (defines valid request/response shapes)

from typing import Any

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    job_type: str
    payload: dict[str, Any]
    max_attempts: int = Field(default=3, ge=1, le=10)


class JobCreateResponse(BaseModel):
    job_id: int
    status: str
    job_type: str
    payload: dict[str, Any]
    max_attempts: int


class JobListItem(BaseModel):
    job_id: int
    job_type: str
    status: str
    attempts: int
    max_attempts: int
    error: str | None
    created_at: str
    updated_at: str


class JobDetailResponse(BaseModel):
    job_id: int
    job_type: str
    payload: dict[str, Any]
    status: str
    result: Any | None
    error: str | None
    attempts: int
    max_attempts: int
    created_at: str
    updated_at: str
    started_at: str | None
    finished_at: str | None
    duration_seconds: float | None


class MetricsResponse(BaseModel):
    total_jobs: int
    queued_jobs: int
    running_jobs: int
    succeeded_jobs: int
    failed_jobs: int
    success_rate: float
    failed_after_retries: int
    average_duration_seconds: float | None
