# schemas.py: job validation (defines valid request/response shapes)

from typing import Any

from pydantic import BaseModel


class JobCreateRequest(BaseModel):
    job_type: str
    payload: dict[str, Any]


class JobCreateResponse(BaseModel):
    job_id: int
    status: str
    job_type: str
    payload: dict[str, Any]


class JobListItem(BaseModel):
    job_id: int
    job_type: str
    status: str
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
    created_at: str
    updated_at: str
