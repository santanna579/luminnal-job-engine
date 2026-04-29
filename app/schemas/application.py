from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ApplicationStatus = Literal[
    "saved",
    "applied",
    "recruiter_contact",
    "interview_process",
    "offer",
    "hired",
    "declined",
    "rejected",
]


class ApplicationCreate(BaseModel):
    job_id: int
    job_title: str
    company: str | None = None
    location: str | None = None
    status: ApplicationStatus = "saved"
    resume_snapshot: str | None = None
    cover_letter: str | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    job_title: str
    company: str | None = None
    location: str | None = None
    created_at: datetime
    status: ApplicationStatus
    resume_snapshot: str | None = None
    cover_letter: str | None = None

    model_config = ConfigDict(from_attributes=True)