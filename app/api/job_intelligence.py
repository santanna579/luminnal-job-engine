from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import get_current_user_id
from app.models_match import JobMatchModel
from app.models_generated import GeneratedContentModel

router = APIRouter()


@router.get("/jobs/{job_id}/intelligence-status")
def get_job_intelligence_status(
    job_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    match = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user_id)
        .filter(JobMatchModel.vaga_id == job_id)
        .order_by(JobMatchModel.criado_em.desc())
        .first()
    )

    resumo = (
        db.query(GeneratedContentModel)
        .filter(GeneratedContentModel.user_id == user_id)
        .filter(GeneratedContentModel.vaga_id == job_id)
        .order_by(GeneratedContentModel.criado_em.desc())
        .first()
    )

    return {
        "job_id": job_id,
        "has_match": bool(match),
        "has_resumo": bool(resumo),
        "match": {
            "score": match.score,
            "level": match.nivel_aderencia,
            "explanation": match.resumo_analitico,
            "created_at": match.criado_em,
        } if match else None,
        "resumo": {
            "created_at": resumo.criado_em,
        } if resumo else None,
    }


@router.get("/jobs/intelligence-statuses")
def get_jobs_intelligence_statuses(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    matches = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user_id)
        .order_by(JobMatchModel.vaga_id.asc(), JobMatchModel.criado_em.desc())
        .all()
    )

    contents = (
        db.query(GeneratedContentModel)
        .filter(GeneratedContentModel.user_id == user_id)
        .order_by(GeneratedContentModel.vaga_id.asc(), GeneratedContentModel.criado_em.desc())
        .all()
    )

    result = {}

    for match in matches:
        key = str(match.vaga_id)

        if key not in result:
            result[key] = {
                "job_id": match.vaga_id,
                "has_match": False,
                "has_resumo": False,
                "match_score": None,
                "match_level": None,
                "match_created_at": None,
                "resumo_created_at": None,
            }

        if not result[key]["has_match"]:
            result[key]["has_match"] = True
            result[key]["match_score"] = match.score
            result[key]["match_level"] = match.nivel_aderencia
            result[key]["match_created_at"] = match.criado_em

    for content in contents:
        key = str(content.vaga_id)

        if key not in result:
            result[key] = {
                "job_id": content.vaga_id,
                "has_match": False,
                "has_resumo": False,
                "match_score": None,
                "match_level": None,
                "match_created_at": None,
                "resumo_created_at": None,
            }

        if not result[key]["has_resumo"]:
            result[key]["has_resumo"] = True
            result[key]["resumo_created_at"] = content.criado_em

    return result