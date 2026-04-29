from typing import Optional

from sqlalchemy.orm import Session

from app.models_application import ApplicationModel
from app.models_application_history import ApplicationStatusHistoryModel
from app.models_job import JobPostingModel
from app.schemas.job_schema import JobCreate


def _find_existing_job(db: Session, job: JobCreate):
    if job.url:
        existing = (
            db.query(JobPostingModel)
            .filter(JobPostingModel.url == job.url)
            .first()
        )
        if existing:
            return existing

    return (
        db.query(JobPostingModel)
        .filter(
            JobPostingModel.titulo == job.titulo,
            JobPostingModel.empresa == job.empresa,
            JobPostingModel.localizacao == job.localizacao,
        )
        .first()
    )


def create_jobs_bulk_db(
    db: Session,
    jobs: list[JobCreate],
    created_by_user_id: Optional[int],
):
    created_count = 0
    skipped_count = 0

    for job in jobs:
        existing = _find_existing_job(db, job)

        if existing:
            skipped_count += 1
            continue

        new_job = JobPostingModel(
            created_by_user_id=created_by_user_id,
            titulo=job.titulo,
            empresa=job.empresa,
            descricao=job.descricao,
            localizacao=job.localizacao,
            origem=job.origem or "linkedin",
            url=job.url,
            raw_description=job.raw_description,
            job_json=job.job_json,
            job_summary=job.job_summary,
        )

        db.add(new_job)
        created_count += 1

    db.commit()

    return {
        "created_count": created_count,
        "skipped_count": skipped_count,
    }


def list_jobs_catalog_db(
    db: Session,
    q: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    query = db.query(JobPostingModel)

    if q:
        search = f"%{q}%"
        query = query.filter(
            (JobPostingModel.titulo.ilike(search)) |
            (JobPostingModel.empresa.ilike(search)) |
            (JobPostingModel.descricao.ilike(search))
        )

    if company:
        query = query.filter(JobPostingModel.empresa.ilike(f"%{company}%"))

    if location:
        query = query.filter(JobPostingModel.localizacao.ilike(f"%{location}%"))

    return (
        query
        .order_by(JobPostingModel.criado_em.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def apply_to_job_db(
    db: Session,
    job_id: int,
    user_id: int,
):
    existing = (
        db.query(ApplicationModel)
        .filter(
            ApplicationModel.user_id == user_id,
            ApplicationModel.job_id == job_id,
        )
        .first()
    )

    if existing:
        return {
            "application": existing,
            "already_exists": True,
        }

    job = (
        db.query(JobPostingModel)
        .filter(JobPostingModel.id == job_id)
        .first()
    )

    if not job:
        return None

    application = ApplicationModel(
        user_id=user_id,
        job_id=job.id,
        job_title=job.titulo,
        company=job.empresa,
        location=job.localizacao,
        status="applied",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    history = ApplicationStatusHistoryModel(
        application_id=application.id,
        user_id=user_id,
        from_status=None,
        to_status="applied",
    )

    db.add(history)
    db.commit()

    return {
        "application": application,
        "already_exists": False,
    }