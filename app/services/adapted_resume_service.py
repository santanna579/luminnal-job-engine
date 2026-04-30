from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import UserProfileModel
from app.models_job import JobPostingModel
from app.models_generated import GeneratedContentModel
from app.models_match import JobMatchModel
from app.ai.resume_generator import gerar_resumo_e_carta

MONTHLY_ADAPTED_RESUME_LIMIT = 10

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
    "ssas",
    "ssis",
    "dax",
    "dbt",
    "git",
    "ci/cd",
]


def get_user_adapted_resume_usage_db(db: Session, user_id: int) -> dict:
    from datetime import datetime

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    used = (
        db.query(GeneratedContentModel)
        .filter(GeneratedContentModel.user_id == user_id)
        .filter(GeneratedContentModel.criado_em >= month_start)
        .count()
    )

    remaining = max(MONTHLY_ADAPTED_RESUME_LIMIT - used, 0)

    return {
        "monthly_limit": MONTHLY_ADAPTED_RESUME_LIMIT,
        "used": used,
        "remaining": remaining,
    }


def _safe_json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}

    try:
        return json.loads(value)
    except Exception:
        return {}


def _safe_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _extract_skills_from_text(text: str | None) -> list[str]:
    normalized_text = _normalize_text(text)

    if not normalized_text:
        return []

    result: list[str] = []

    for skill in KNOWN_SKILLS:
        normalized_skill = _normalize_text(skill)

        if normalized_skill in normalized_text and normalized_skill not in result:
            result.append(normalized_skill)

    return result


def _extract_years_from_summary(summary: str | None) -> int:
    if not summary:
        return 0

    match = re.search(r"(\d+)\s+anos", summary.lower())

    if not match:
        return 0

    try:
        return int(match.group(1))
    except Exception:
        return 0


def _get_profile_data(profile_json: str) -> dict[str, Any]:
    data = _safe_json_loads(profile_json)
    return data.get("profile", data)


def _build_profile_for_generator(profile_json: str) -> dict[str, Any]:
    profile_data = _get_profile_data(profile_json)

    full_name = (
        profile_data.get("fullName")
        or profile_data.get("full_name")
        or profile_data.get("contact", {}).get("full_name")
        or "Profissional"
    )

    summary = profile_data.get("summary") or ""
    skills = profile_data.get("skills") or []

    years = _extract_years_from_summary(summary)

    return {
        "nome": full_name,
        "objetivo": profile_data.get("headline") or "área de dados",
        "anos_experiencia": years,
        "skills": skills,
        "profile_json": profile_json,
    }


def _build_job_for_generator(job: JobPostingModel) -> dict[str, Any]:
    return {
        "id": job.id,
        "titulo": job.titulo,
        "empresa": job.empresa,
        "localizacao": job.localizacao,
        "descricao": job.descricao,
        "job_summary": job.job_summary,
    }


def _build_match_from_existing_job_match(match: JobMatchModel) -> dict[str, Any]:
    strengths = _safe_json_loads(match.palavras_chave_encontradas)
    gaps = _safe_json_loads(match.exigencias_nao_cobertas)

    return {
        "score": match.score,
        "skills_em_comum": strengths if isinstance(strengths, list) else [],
        "skills_faltantes": gaps if isinstance(gaps, list) else [],
        "forcas_transferiveis": [],
        "senioridade_compativel": match.score_senioridade >= 50,
        "ingles_compativel": True,
        "recomendacao": match.recomendacao,
        "resumo_match_semantico": match.resumo_analitico or "",
    }


def _build_match_from_profile_and_job(
    profile: dict[str, Any],
    job: JobPostingModel,
) -> dict[str, Any]:
    profile_skills = profile.get("skills") or []
    profile_skills_normalized = [_normalize_text(item) for item in profile_skills]

    job_text = " ".join(
        [
            job.titulo or "",
            job.descricao or "",
            job.job_summary or "",
        ]
    )

    job_skills = _extract_skills_from_text(job_text)

    skills_em_comum = [
        skill
        for skill in job_skills
        if skill in profile_skills_normalized
        or any(skill in item for item in profile_skills_normalized)
    ]

    skills_faltantes = [
        skill
        for skill in job_skills
        if skill not in skills_em_comum
    ]

    forcas_transferiveis = [
        skill
        for skill in profile_skills_normalized
        if skill not in skills_em_comum
    ][:5]

    score_skills = min(len(skills_em_comum) * 20, 80)
    score_total = min(score_skills + 20, 100)

    if score_total >= 80:
        recomendacao = "Alta compatibilidade"
    elif score_total >= 50:
        recomendacao = "Compatibilidade moderada"
    else:
        recomendacao = "Baixa compatibilidade"

    resumo = (
        f"Skills em comum: {', '.join(skills_em_comum) if skills_em_comum else 'nenhuma identificada'}. "
        f"Skills faltantes: {', '.join(skills_faltantes) if skills_faltantes else 'nenhuma relevante'}. "
        f"Recomendação: {recomendacao}."
    )

    return {
        "score": score_total,
        "skills_em_comum": skills_em_comum,
        "skills_faltantes": skills_faltantes,
        "forcas_transferiveis": forcas_transferiveis,
        "senioridade_compativel": True,
        "ingles_compativel": True,
        "recomendacao": recomendacao,
        "resumo_match_semantico": resumo,
    }


def _get_cached_content(
    db: Session,
    user_id: int,
    vaga_id: int,
) -> dict[str, Any] | None:
    cached = (
        db.query(GeneratedContentModel)
        .filter(GeneratedContentModel.user_id == user_id)
        .filter(GeneratedContentModel.vaga_id == vaga_id)
        .order_by(GeneratedContentModel.criado_em.desc())
        .first()
    )

    if not cached:
        return None

    content = _safe_json_loads(cached.content_json)

    if content:
        return content

    return {
        "cached": True,
        "resumo_profissional_adaptado": cached.resumo_profissional_adaptado,
        "skills_para_destacar": [],
        "gaps_para_contornar": [],
        "carta_apresentacao": cached.carta_apresentacao,
        "curriculo_estruturado": {
            "nome": cached.nome_candidato,
            "titulo_objetivo": "",
            "resumo": cached.resumo_profissional_adaptado,
            "skills": [],
            "gaps": [],
        },
    }


def gerar_resumo_adaptado_db(
    db: Session,
    vaga_id: int,
    user_id: int = 1,
) -> dict[str, Any] | None:
    cached = _get_cached_content(
        db=db,
        user_id=user_id,
        vaga_id=vaga_id,
    )

    if cached:
        return cached
    
    usage = get_user_adapted_resume_usage_db(db=db, user_id=user_id)

    if usage["remaining"] <= 0:
        return {
            "error": "MONTHLY_LIMIT_REACHED",
            "message": "Limite mensal de geração de resumo adaptado atingido para este perfil.",
            "usage": usage,
        }

    profile_row = (
        db.query(UserProfileModel)
        .filter(UserProfileModel.user_id == user_id)
        .filter(UserProfileModel.snapshot_type == "active")
        .first()
    )

    job = (
        db.query(JobPostingModel)
        .filter(JobPostingModel.id == vaga_id)
        .first()
    )

    if not profile_row or not job:
        return None

    if not profile_row.profile_json or not job.descricao:
        return None

    profile_for_generator = _build_profile_for_generator(profile_row.profile_json)
    job_for_generator = _build_job_for_generator(job)

    existing_match = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.user_id == user_id)
        .filter(JobMatchModel.vaga_id == vaga_id)
        .order_by(JobMatchModel.criado_em.desc())
        .first()
    )

    if existing_match:
        match = _build_match_from_existing_job_match(existing_match)
    else:
        match = _build_match_from_profile_and_job(
            profile=profile_for_generator,
            job=job,
        )

    result = gerar_resumo_e_carta(
        profile=profile_for_generator,
        job=job_for_generator,
        match=match,
    )

    generated = GeneratedContentModel(
        user_id=user_id,
        vaga_id=vaga_id,
        nome_candidato=profile_for_generator.get("nome", "Profissional"),
        resumo_profissional_adaptado=result.get("resumo_profissional_adaptado", ""),
        carta_apresentacao=result.get("carta_apresentacao", ""),
        content_json=_safe_json_dumps(result),
    )

    db.add(generated)
    db.commit()
    db.refresh(generated)

    result["cached"] = False
    result["usage"] = get_user_adapted_resume_usage_db(db=db, user_id=user_id)

    return result