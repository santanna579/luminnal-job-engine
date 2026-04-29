from datetime import datetime

from sqlalchemy.orm import Session

from app.models_application import ApplicationModel
from app.models_application_history import ApplicationStatusHistoryModel
from app.models_match import JobMatchModel
from app.services.applications_intelligence_service import (
    list_applications_summary_db,
    normalize_status,
)


def get_dashboard_metrics_db(db: Session, user_id: int):
    applications = (
        db.query(ApplicationModel)
        .filter(ApplicationModel.user_id == user_id)
        .all()
    )

    now = datetime.utcnow()
    current_year = now.year
    current_month = now.month

    normalized_statuses = [normalize_status(item.status) for item in applications]

    total = len(applications)

    saved = sum(1 for status in normalized_statuses if status == "saved")
    applied = sum(1 for status in normalized_statuses if status == "applied")
    recruiter_contact = sum(1 for status in normalized_statuses if status == "recruiter_contact")
    interview = sum(1 for status in normalized_statuses if status == "interview")
    proposal = sum(1 for status in normalized_statuses if status == "proposal")
    hired = sum(1 for status in normalized_statuses if status == "hired")
    declined = sum(1 for status in normalized_statuses if status == "declined")
    rejected = sum(1 for status in normalized_statuses if status == "rejected")

    created_this_month = sum(
        1
        for item in applications
        if item.created_at
        and item.created_at.year == current_year
        and item.created_at.month == current_month
    )

    response_base = recruiter_contact + interview + proposal + hired + declined
    interview_base = interview + proposal + hired + declined

    response_rate = round((response_base / total) * 100, 1) if total > 0 else 0
    interview_rate = round((interview_base / total) * 100, 1) if total > 0 else 0
    success_rate = round((hired / total) * 100, 1) if total > 0 else 0

    summary = list_applications_summary_db(db, user_id=user_id)
    hot_jobs = [item for item in summary if item["is_hot"]][:5]
    needs_action_jobs = [item for item in summary if item["needs_action"]][:5]

    return {
        "total": total,
        "saved": saved,
        "applied": applied,
        "recruiter_contact": recruiter_contact,
        "interview": interview,
        "proposal": proposal,
        "hired": hired,
        "declined": declined,
        "rejected": rejected,
        "created_this_month": created_this_month,
        "response_rate": response_rate,
        "interview_rate": interview_rate,
        "success_rate": success_rate,
        "hot_jobs_count": len([item for item in summary if item["is_hot"]]),
        "needs_action_count": len([item for item in summary if item["needs_action"]]),
        "top_hot_jobs": hot_jobs,
        "top_needs_action_jobs": needs_action_jobs,
    }


def _get_last_update_date(db: Session, application_id: int, created_at):
    last_history = (
        db.query(ApplicationStatusHistoryModel)
        .filter(ApplicationStatusHistoryModel.application_id == application_id)
        .order_by(ApplicationStatusHistoryModel.changed_at.desc())
        .first()
    )

    if last_history and last_history.changed_at:
        return last_history.changed_at

    return created_at


def _get_latest_match_score(db: Session, job_id: int) -> int:
    latest_match = (
        db.query(JobMatchModel)
        .filter(JobMatchModel.vaga_id == job_id)
        .order_by(JobMatchModel.criado_em.desc())
        .first()
    )

    if latest_match and latest_match.score is not None:
        return int(latest_match.score)

    return 0


def _get_pipeline_weight(status: str) -> int:
    weights = {
        "saved": 20,
        "applied": 35,
        "recruiter_contact": 90,
        "interview": 85,
        "interview_process": 85,
        "proposal": 95,
        "offer": 95,
        "hired": 100,
        "rejected": 0,
        "declined": 0,
    }
    return weights.get(status, 10)


def _get_recency_score(days_without_update: int) -> int:
    if days_without_update <= 1:
        return 100
    if days_without_update <= 3:
        return 85
    if days_without_update <= 7:
        return 65
    if days_without_update <= 14:
        return 40
    return 15


def _build_hot_label(status: str, score: int, days_without_update: int) -> str:
    if status in ["proposal", "offer"]:
        return "Proposta em andamento"
    if status in ["recruiter_contact"]:
        return "Contato de recrutador recente"
    if status in ["interview", "interview_process"]:
        return "Processo ativo"
    if score >= 80 and days_without_update <= 7:
        return "Alta compatibilidade com tração"
    if score >= 70:
        return "Boa oportunidade"
    return "Monitorar"


def get_hot_jobs_ranked_db(db: Session, user_id: int, limit: int = 5):
    applications = (
        db.query(ApplicationModel)
        .filter(
            ApplicationModel.user_id == user_id,
            ApplicationModel.status.notin_(["rejected", "declined", "hired"])
        )
        .all()
    )

    now = datetime.utcnow()
    ranked_items = []

    for app in applications:
        reference_date = _get_last_update_date(db, app.id, app.created_at)
        days_without_update = (now - reference_date).days if reference_date else 999

        match_score = _get_latest_match_score(db, app.job_id)
        pipeline_weight = _get_pipeline_weight(app.status)
        recency_score = _get_recency_score(days_without_update)

        hot_score = round(
            (pipeline_weight * 0.45) +
            (match_score * 0.35) +
            (recency_score * 0.20),
            1
        )

        ranked_items.append({
            "application_id": app.id,
            "job_id": app.job_id,
            "job_title": app.job_title,
            "company": app.company,
            "location": app.location,
            "status": app.status,
            "match_score": match_score,
            "days_without_update": days_without_update,
            "pipeline_weight": pipeline_weight,
            "recency_score": recency_score,
            "hot_score": hot_score,
            "hot_label": _build_hot_label(app.status, match_score, days_without_update),
            "last_update_at": reference_date,
            "is_hot": hot_score >= 70,
        })

    ranked_items.sort(
        key=lambda item: (
            item["hot_score"],
            item["match_score"],
            -item["days_without_update"],
        ),
        reverse=True
    )

    return ranked_items[:limit]


def get_hot_score_map(db: Session, user_id: int):
    hot_items = get_hot_jobs_ranked_db(db=db, user_id=user_id, limit=100)

    return {
        item["job_id"]: item["hot_score"]
        for item in hot_items
    }


def _build_follow_up_action(status: str, days_without_update: int):
    if status == "saved" and days_without_update >= 2:
        return {
            "action_key": "apply_now",
            "action_label": "Aplicar agora",
            "reason": "A vaga está salva há alguns dias e ainda não virou candidatura.",
            "priority": "high" if days_without_update >= 5 else "medium",
        }

    if status == "applied" and days_without_update >= 3:
        return {
            "action_key": "send_follow_up",
            "action_label": "Enviar follow-up",
            "reason": "A candidatura foi enviada, mas ainda não houve avanço recente.",
            "priority": "high" if days_without_update >= 7 else "medium",
        }

    if status == "recruiter_contact" and days_without_update >= 2:
        return {
            "action_key": "reply_recruiter",
            "action_label": "Responder recruiter",
            "reason": "Existe contato inicial e o timing agora influencia o avanço do processo.",
            "priority": "high" if days_without_update >= 4 else "medium",
        }

    if status in ["interview", "interview_process"] and days_without_update >= 2:
        return {
            "action_key": "prepare_next_step",
            "action_label": "Preparar próximo passo",
            "reason": "O processo está em entrevista e precisa de manutenção ativa.",
            "priority": "high" if days_without_update >= 5 else "medium",
        }

    if status in ["proposal", "offer"] and days_without_update >= 1:
        return {
            "action_key": "review_offer",
            "action_label": "Revisar proposta",
            "reason": "Existe proposta em aberto e essa etapa é sensível ao tempo.",
            "priority": "high",
        }

    return None


def get_follow_up_suggestions_db(db: Session, user_id: int, limit: int = 5):
    applications = (
        db.query(ApplicationModel)
        .filter(
            ApplicationModel.user_id == user_id,
            ApplicationModel.status.notin_(["rejected", "declined", "hired"])
        )
        .all()
    )

    now = datetime.utcnow()
    suggestions = []

    for app in applications:
        reference_date = _get_last_update_date(db, app.id, app.created_at)
        days_without_update = (now - reference_date).days if reference_date else 999

        action = _build_follow_up_action(app.status, days_without_update)

        if not action:
            continue

        suggestions.append({
            "application_id": app.id,
            "job_id": app.job_id,
            "job_title": app.job_title,
            "company": app.company,
            "location": app.location,
            "status": app.status,
            "days_without_update": days_without_update,
            "last_update_at": reference_date,
            "action_key": action["action_key"],
            "action_label": action["action_label"],
            "reason": action["reason"],
            "priority": action["priority"],
        })

    priority_weight = {"high": 2, "medium": 1, "low": 0}

    suggestions.sort(
        key=lambda item: (
            priority_weight.get(item["priority"], 0),
            item["days_without_update"],
        ),
        reverse=True,
    )

    return suggestions[:limit]


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def get_funnel_analytics_db(db: Session, user_id: int):
    applications = (
        db.query(ApplicationModel)
        .filter(ApplicationModel.user_id == user_id)
        .all()
    )

    total_saved = sum(1 for item in applications if item.status == "saved")
    total_applied = sum(1 for item in applications if item.status == "applied")
    total_recruiter = sum(1 for item in applications if item.status == "recruiter_contact")
    total_interviews = sum(1 for item in applications if item.status == "interview_process")
    total_offers = sum(1 for item in applications if item.status == "offer")
    total_hired = sum(1 for item in applications if item.status == "hired")

    applied_or_beyond = sum(
        1 for item in applications
        if item.status in [
            "applied",
            "recruiter_contact",
            "interview_process",
            "offer",
            "hired",
            "declined",
            "rejected",
        ]
    )

    recruiter_or_beyond = sum(
        1 for item in applications
        if item.status in [
            "recruiter_contact",
            "interview_process",
            "offer",
            "hired",
            "declined",
        ]
    )

    interviews_or_beyond = sum(
        1 for item in applications
        if item.status in [
            "interview_process",
            "offer",
            "hired",
            "declined",
        ]
    )

    offers_or_beyond = sum(
        1 for item in applications
        if item.status in [
            "offer",
            "hired",
            "declined",
        ]
    )

    applied_to_recruiter = _safe_rate(recruiter_or_beyond, applied_or_beyond)
    recruiter_to_interview = _safe_rate(interviews_or_beyond, recruiter_or_beyond)
    interview_to_offer = _safe_rate(offers_or_beyond, interviews_or_beyond)
    offer_to_hired = _safe_rate(total_hired, offers_or_beyond)

    days_saved_to_applied = []
    days_applied_to_recruiter = []
    days_recruiter_to_interview = []
    days_interview_to_offer = []

    for app in applications:
        history = (
            db.query(ApplicationStatusHistoryModel)
            .filter(ApplicationStatusHistoryModel.application_id == app.id)
            .order_by(ApplicationStatusHistoryModel.changed_at.asc())
            .all()
        )

        status_dates = {}
        for event in history:
            if event.to_status not in status_dates:
                status_dates[event.to_status] = event.changed_at

        saved_date = status_dates.get("saved") or app.created_at
        applied_date = status_dates.get("applied")
        recruiter_date = status_dates.get("recruiter_contact")
        interview_date = status_dates.get("interview_process")
        offer_date = status_dates.get("offer")

        if saved_date and applied_date:
            days_saved_to_applied.append((applied_date - saved_date).days)

        if applied_date and recruiter_date:
            days_applied_to_recruiter.append((recruiter_date - applied_date).days)

        if recruiter_date and interview_date:
            days_recruiter_to_interview.append((interview_date - recruiter_date).days)

        if interview_date and offer_date:
            days_interview_to_offer.append((offer_date - interview_date).days)

    def avg_days(values: list[int]) -> float:
        if not values:
            return 0.0
        return round(sum(values) / len(values), 1)

    average_days = {
        "saved_to_applied": avg_days(days_saved_to_applied),
        "applied_to_recruiter": avg_days(days_applied_to_recruiter),
        "recruiter_to_interview": avg_days(days_recruiter_to_interview),
        "interview_to_offer": avg_days(days_interview_to_offer),
    }

    conversion_rates = {
        "applied_to_recruiter": applied_to_recruiter,
        "recruiter_to_interview": recruiter_to_interview,
        "interview_to_offer": interview_to_offer,
        "offer_to_hired": offer_to_hired,
    }

    bottleneck_key = min(conversion_rates, key=conversion_rates.get) if conversion_rates else None

    bottleneck_labels = {
        "applied_to_recruiter": "Aplicada → Recruiter",
        "recruiter_to_interview": "Recruiter → Entrevista",
        "interview_to_offer": "Entrevista → Proposta",
        "offer_to_hired": "Proposta → Contratação",
    }

    return {
        "counts": {
            "saved": total_saved,
            "applied": total_applied,
            "recruiter_contact": total_recruiter,
            "interview_process": total_interviews,
            "offer": total_offers,
            "hired": total_hired,
        },
        "conversion_rates": conversion_rates,
        "average_days": average_days,
        "bottleneck": {
            "key": bottleneck_key,
            "label": bottleneck_labels.get(bottleneck_key, "Sem dados suficientes"),
            "value": conversion_rates.get(bottleneck_key, 0.0) if bottleneck_key else 0.0,
        },
    }