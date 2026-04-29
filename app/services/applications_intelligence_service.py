from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id
from app.models_application import ApplicationModel
from app.models_application_history import ApplicationStatusHistoryModel
from app.models_match import JobMatchModel


STATUS_ALIASES = {
    "saved": "saved",
    "applied": "applied",
    "recruiter_contact": "recruiter_contact",
    "interview": "interview",
    "interview_process": "interview",
    "proposal": "proposal",
    "offer": "proposal",
    "hired": "hired",
    "rejected": "rejected",
    "declined": "declined",
}

STATUS_WEIGHTS = {
    "saved": 8,
    "applied": 18,
    "recruiter_contact": 36,
    "interview": 48,
    "proposal": 62,
    "hired": 100,
    "rejected": 0,
    "declined": 0,
}


def normalize_status(status: str | None) -> str:
    if not status:
        return "saved"
    return STATUS_ALIASES.get(status, status)


def get_last_update_map(db: Session, application_ids: list[int]) -> dict[int, datetime | None]:
    if not application_ids:
        return {}

    history_rows = (
        db.query(ApplicationStatusHistoryModel)
        .filter(ApplicationStatusHistoryModel.application_id.in_(application_ids))
        .order_by(
            ApplicationStatusHistoryModel.application_id.asc(),
            ApplicationStatusHistoryModel.changed_at.desc(),
        )
        .all()
    )

    result: dict[int, datetime | None] = {}

    for row in history_rows:
        if row.application_id not in result:
            result[row.application_id] = row.changed_at

    return result


def get_match_score_map(db: Session, job_ids: list[int]) -> dict[int, int]:
    if not job_ids:
        return {}

    rows = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.vaga_id.in_(job_ids))
        .order_by(JobMatchModel.vaga_id.asc(), JobMatchModel.criado_em.desc())
        .all()
    )

    result: dict[int, int] = {}

    for row in rows:
        if row.vaga_id not in result:
            result[row.vaga_id] = int(row.score or 0)

    return result


def score_recency(days_without_update: int) -> int:
    if days_without_update <= 1:
        return 18
    if days_without_update <= 3:
        return 12
    if days_without_update <= 7:
        return 7
    if days_without_update <= 14:
        return 2
    return 0


def score_match(match_score: int) -> int:
    if match_score >= 90:
        return 22
    if match_score >= 80:
        return 18
    if match_score >= 70:
        return 14
    if match_score >= 60:
        return 10
    if match_score >= 50:
        return 6
    return 2


def score_stage(status: str) -> int:
    return STATUS_WEIGHTS.get(status, 0)


def build_hot_reasons(
    normalized_status: str,
    match_score: int,
    days_without_update: int,
) -> list[str]:
    reasons: list[str] = []

    if normalized_status in {"recruiter_contact", "interview", "proposal"}:
        reasons.append("Etapa avançada no pipeline")

    if match_score >= 80:
        reasons.append("Alta compatibilidade com a vaga")
    elif match_score >= 65:
        reasons.append("Boa aderência ao perfil")

    if days_without_update <= 3:
        reasons.append("Movimentação recente")

    return reasons[:3]


def build_followup_label(normalized_status: str, days_without_update: int) -> str | None:
    if normalized_status == "applied" and days_without_update >= 5:
        return "Enviar follow-up para reforçar interesse"
    if normalized_status == "saved" and days_without_update >= 3:
        return "Revisar abordagem e decidir se vai aplicar"
    if normalized_status == "recruiter_contact" and days_without_update >= 4:
        return "Retomar contato com o recrutador"
    if normalized_status == "interview" and days_without_update >= 5:
        return "Fazer acompanhamento pós-entrevista"
    if normalized_status == "proposal" and days_without_update >= 3:
        return "Acompanhar andamento da proposta"
    return None


def compute_hot_score(
    normalized_status: str,
    match_score: int,
    days_without_update: int,
) -> int:
    if normalized_status in {"rejected", "declined"}:
        return 0

    if normalized_status == "hired":
        return 100

    score = (
        score_stage(normalized_status)
        + score_match(match_score)
        + score_recency(days_without_update)
    )

    return max(0, min(100, score))


def classify_priority(hot_score: int, normalized_status: str) -> str:
    if normalized_status in {"rejected", "declined"}:
        return "closed"
    if normalized_status == "hired":
        return "won"
    if hot_score >= 75:
        return "top_priority"
    if hot_score >= 55:
        return "high_priority"
    if hot_score >= 35:
        return "medium_priority"
    return "low_priority"


def build_hot_label(hot_score: int, normalized_status: str) -> str:
    if normalized_status == "hired":
        return "Contratado"
    if normalized_status in {"rejected", "declined"}:
        return "Encerrada"
    if hot_score >= 75:
        return "Muito quente"
    if hot_score >= 55:
        return "Quente"
    if hot_score >= 35:
        return "Monitorar"
    return "Fria"


def build_application_summary_item(
    application: ApplicationModel,
    last_update_at: datetime | None,
    match_score: int,
    now: datetime,
) -> dict[str, Any]:
    normalized_status = normalize_status(application.status)
    reference_date = last_update_at or application.created_at or now
    days_without_update = max((now - reference_date).days, 0)

    hot_score = compute_hot_score(
        normalized_status=normalized_status,
        match_score=match_score,
        days_without_update=days_without_update,
    )

    followup_label = build_followup_label(
        normalized_status=normalized_status,
        days_without_update=days_without_update,
    )

    is_hot = normalized_status in {"recruiter_contact", "interview", "proposal"} or hot_score >= 55
    needs_action = followup_label is not None

    return {
        "application_id": application.id,
        "job_id": application.job_id,
        "job_title": application.job_title,
        "company": application.company,
        "location": application.location,
        "status": application.status,
        "normalized_status": normalized_status,
        "match_score": match_score,
        "last_update_at": reference_date.isoformat() if reference_date else None,
        "days_without_update": days_without_update,
        "hot_score": hot_score,
        "hot_label": build_hot_label(hot_score, normalized_status),
        "priority_bucket": classify_priority(hot_score, normalized_status),
        "is_hot": is_hot,
        "needs_action": needs_action,
        "needs_action_label": followup_label,
        "reasons": build_hot_reasons(
            normalized_status=normalized_status,
            match_score=match_score,
            days_without_update=days_without_update,
        ),
    }


def list_applications_summary_db(db: Session, user_id: int | None = None) -> list[dict[str, Any]]:
    current_user_id = user_id if user_id is not None else get_current_user_id()

    applications = (
        db.query(ApplicationModel)
        .filter(ApplicationModel.user_id == current_user_id)
        .order_by(ApplicationModel.created_at.desc())
        .all()
    )

    if not applications:
        return []

    application_ids = [item.id for item in applications]
    job_ids = [item.job_id for item in applications]

    last_update_map = get_last_update_map(db, application_ids)
    match_score_map = get_match_score_map(db, job_ids)
    now = datetime.utcnow()

    result = [
        build_application_summary_item(
            application=item,
            last_update_at=last_update_map.get(item.id),
            match_score=match_score_map.get(item.job_id, 0),
            now=now,
        )
        for item in applications
    ]

    result.sort(
        key=lambda item: (
            item["hot_score"],
            -item["days_without_update"],
            item["match_score"],
        ),
        reverse=True,
    )

    return result