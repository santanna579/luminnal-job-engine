from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import re

from app.models_job import JobPostingModel
from app.models import UserProfileModel
from app.schemas.match import (
    MatchProfile,
    MatchProfileExperienceItem,
    MatchProfileEducationItem,
    MatchJob,
)
from app.services.match_engine import calculate_match


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


def _safe_json_loads(value: str) -> dict:
    try:
        return json.loads(value)
    except Exception:
        return {}


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


def _parse_profile(profile_json: str) -> MatchProfile:
    data = _safe_json_loads(profile_json)
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
    requirements = _extract_requirements_from_description(job.descricao)

    return MatchJob(
        id=str(job.id),
        title=job.titulo,
        company=job.empresa,
        description=job.descricao,
        requirements=requirements,
        nice_to_have=[],
        seniority=None,
        location=job.localizacao,
    )


def _get_level(score: int) -> str:
    if score >= 75:
        return "alto"
    if score >= 50:
        return "medio"
    return "baixo"


def get_job_feed_with_score_db(db: Session, user_id: int) -> List[Dict]:
    profile = (
        db.query(UserProfileModel)
        .filter(UserProfileModel.user_id == user_id)
        .filter(UserProfileModel.snapshot_type == "active")
        .first()
    )

    if not profile:
        raise Exception("Perfil do candidato não cadastrado")

    parsed_profile = _parse_profile(profile.profile_json)

    jobs = (
        db.query(JobPostingModel)
        .order_by(JobPostingModel.criado_em.desc())
        .limit(50)
        .all()
    )

    response = []

    for job in jobs:
        parsed_job = _parse_job(job)

        match = calculate_match(
            profile=parsed_profile,
            job=parsed_job,
        )

        score = int(match.get("score", 0))

        response.append(
            {
                "id": job.id,
                "titulo": job.titulo,
                "empresa": job.empresa,
                "localizacao": job.localizacao,
                "origem": job.origem,
                "url": job.url,
                "descricao": job.descricao,
                "criado_em": job.criado_em,

                "score": score,
                "level": _get_level(score),
                "explanation": match.get("summary", ""),
                "strengths": match.get("strengths", []),
                "gaps": match.get("gaps", []),
                "suggestions": match.get("suggestions", []),
                "details": match.get("details", {}),
            }
        )

    return response