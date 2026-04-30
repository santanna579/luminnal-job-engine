from datetime import datetime
from typing import Any
import json
import re

from sqlalchemy.orm import Session

from app.models import UserProfileModel
from app.models_job import JobPostingModel
from app.models_match import JobMatchModel
from app.schemas.match import (
    MatchProfile,
    MatchProfileExperienceItem,
    MatchProfileEducationItem,
    MatchJob,
)
from app.services.match_engine import calculate_match


DEFAULT_FREE_LIMIT = 10  # free mais restrito
PRO_LIMIT = 30
PREMIUM_LIMIT = 200
UNLIMITED_LIMIT = 999999


def _get_user_plan_limit(user_id: int) -> int:
    # FUTURO: aqui você vai buscar do banco (tabela user_plan)
    
    # POR ENQUANTO:
    return PRO_LIMIT


KNOWN_SKILLS = [
    "sql",
    "python",
    "etl",
    "aws",
    "azure",
    "airflow",
    "docker",
    "power bi",
    "qlik sense",
    "oracle",
    "sql server",
    "mysql",
    "postgresql",
    "postgres",
    "data warehouse",
    "data warehousing",
    "data modeling",
    "modelagem de dados",
    "snowflake",
    "spark",
    "fastapi",
    "api",
    "inglês",
    "ingles",
    "english",
]


def _safe_json_loads(value: str | None):
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return []


def _safe_json_dumps(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _extract_requirements_from_description(description: str | None) -> list[str]:
    text = _normalize_text(description)

    if not text:
        return []

    found = []

    for skill in KNOWN_SKILLS:
        normalized_skill = _normalize_text(skill)

        if normalized_skill in text and normalized_skill not in found:
            found.append(normalized_skill)

    return found


def _normalize_certifications(items: list[Any]) -> list[str]:
    result = []

    for item in items or []:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            name = item.get("name") or item.get("title") or ""
            issuer = item.get("issuer") or ""
            text = f"{name} - {issuer}".strip(" -")
            if text:
                result.append(text)

    return result


def _get_level(score: int) -> str:
    if score >= 75:
        return "alto"
    if score >= 50:
        return "medio"
    return "baixo"


def _recommendation_by_score(score: int) -> str:
    if score >= 75:
        return "Alta aderência. Vale priorizar esta vaga."
    if score >= 50:
        return "Aderência média. Vale avaliar os gaps antes de aplicar."
    return "Baixa aderência. Aplicar somente se fizer sentido estratégico."


def _parse_profile(profile_json: str) -> MatchProfile:
    data = json.loads(profile_json)
    profile_data = data.get("profile", data)

    experiences = []

    for exp in profile_data.get("experiences", []) or []:
        experiences.append(
            MatchProfileExperienceItem(
                title=exp.get("title") or exp.get("role"),
                company=exp.get("company"),
                description=exp.get("description"),
                start_date=exp.get("start_date") or exp.get("startDate") or exp.get("start"),
                end_date=exp.get("end_date") or exp.get("endDate") or exp.get("end"),
                current=exp.get("current"),
            )
        )

    education = []

    for edu in profile_data.get("education", []) or []:
        education.append(
            MatchProfileEducationItem(
                degree=edu.get("degree"),
                institution=edu.get("institution"),
                field_of_study=edu.get("field_of_study") or edu.get("fieldOfStudy"),
            )
        )

    return MatchProfile(
        full_name=(
            profile_data.get("full_name")
            or profile_data.get("fullName")
            or profile_data.get("contact", {}).get("full_name")
        ),
        summary=profile_data.get("summary"),
        skills=profile_data.get("skills", []) or [],
        experience=experiences,
        education=education,
        languages=profile_data.get("languages", []) or [],
        certifications=_normalize_certifications(profile_data.get("certifications", [])),
    )


def _parse_job(job: JobPostingModel) -> MatchJob:
    return MatchJob(
        id=str(job.id),
        title=job.titulo,
        company=job.empresa,
        description=job.descricao,
        requirements=_extract_requirements_from_description(job.descricao),
        nice_to_have=[],
        seniority=None,
        location=job.localizacao,
    )


def _get_month_start() -> datetime:
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


def get_user_analysis_usage_db(db: Session, user_id: int) -> dict:
    month_start = _get_month_start()

    used = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user_id)
        .filter(JobMatchModel.criado_em >= month_start)
        .count()
    )

    limit = _get_user_plan_limit(user_id)

    remaining = max(limit - used, 0)

    return {
        "monthly_limit": limit,
        "used": used,
        "remaining": remaining,
    }

def _build_response_from_cache(match: JobMatchModel) -> dict:
    return {
        "cached": True,
        "match_id": match.id,
        "job_id": match.vaga_id,
        "score": match.score,
        "level": match.nivel_aderencia,
        "explanation": match.resumo_analitico,
        "strengths": _safe_json_loads(match.palavras_chave_encontradas),
        "gaps": _safe_json_loads(match.exigencias_nao_cobertas),
        "suggestions": _safe_json_loads(match.skills_nao_relevantes),
        "details": {
            "skills_score": match.score_skills,
            "experience_score": match.score_senioridade,
            "semantic_score": match.score_ingles,
        },
        "created_at": match.criado_em,
    }


def analyze_job_match_on_demand_db(db: Session, user_id: int, job_id: int) -> dict:
    existing_match = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user_id)
        .filter(JobMatchModel.vaga_id == job_id)
        .order_by(JobMatchModel.criado_em.desc())
        .first()
    )

    if existing_match:
        response = _build_response_from_cache(existing_match)
        response["usage"] = get_user_analysis_usage_db(db, user_id)
        return response

    usage = get_user_analysis_usage_db(db, user_id)

    if usage["remaining"] <= 0:
        return {
            "error": "MONTHLY_LIMIT_REACHED",
            "message": "Limite mensal de análises atingido para este perfil.",
            "usage": usage,
        }

    profile = (
        db.query(UserProfileModel)
        .filter(UserProfileModel.user_id == user_id)
        .filter(UserProfileModel.snapshot_type == "active")
        .first()
    )

    if not profile:
        return {
            "error": "PROFILE_NOT_FOUND",
            "message": "Perfil do candidato não cadastrado.",
        }

    job = (
        db.query(JobPostingModel)
        .filter(JobPostingModel.id == job_id)
        .first()
    )

    if not job:
        return {
            "error": "JOB_NOT_FOUND",
            "message": "Vaga não encontrada.",
        }

    parsed_profile = _parse_profile(profile.profile_json)
    parsed_job = _parse_job(job)

    result = calculate_match(
        profile=parsed_profile,
        job=parsed_job,
    )

    score = int(result.get("score", 0))
    details = result.get("details", {}) or {}

    new_match = JobMatchModel(
        user_id=user_id,
        vaga_id=job.id,
        nome_candidato=parsed_profile.full_name or "Candidato",
        score=score,
        score_skills=int(details.get("skills_score", 0)),
        score_senioridade=int(details.get("experience_score", 0)),
        score_ingles=int(details.get("semantic_score", 0)),
        nivel_aderencia=_get_level(score),
        palavras_chave_encontradas=_safe_json_dumps(result.get("strengths", [])),
        skills_nao_relevantes=_safe_json_dumps(result.get("suggestions", [])),
        exigencias_nao_cobertas=_safe_json_dumps(result.get("gaps", [])),
        recomendacao=_recommendation_by_score(score),
        resumo_analitico=result.get("summary", ""),
    )

    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    response = _build_response_from_cache(new_match)
    response["cached"] = False
    response["usage"] = get_user_analysis_usage_db(db, user_id)

    return response