from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id
from app.database import get_db
from app.schemas.job_schema import (
    JobApplyResponse,
    JobCatalogItemResponse,
    JobCreate,
    JobImportResponse,
)
from app.services.job_service import (
    apply_to_job_db,
    create_jobs_bulk_db,
    list_jobs_catalog_db,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/import", response_model=JobImportResponse)
def import_jobs(
    jobs: list[JobCreate],
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = create_jobs_bulk_db(
        db=db,
        jobs=jobs,
        created_by_user_id=user_id,
    )
    return result


@router.get("/search", response_model=list[JobCatalogItemResponse])
def search_jobs(
    q: Optional[str] = Query(default=None),
    company: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_jobs_catalog_db(
        db=db,
        q=q,
        company=company,
        location=location,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{job_id}/apply",
    response_model=JobApplyResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_to_job(
    job_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = apply_to_job_db(
        db=db,
        job_id=job_id,
        user_id=user_id,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Vaga não encontrada.",
        )

    application = result["application"]

    return {
        "application_id": application.id,
        "status": application.status,
        "already_exists": result["already_exists"],
    }