from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_id
from app.models_application import ApplicationModel
from app.models_application_history import ApplicationStatusHistoryModel


def create_application_db(db: Session, data: dict):
    current_user_id = get_current_user_id()

    existing = (
        db.query(ApplicationModel)
        .filter(
            ApplicationModel.user_id == current_user_id,
            ApplicationModel.job_id == data["job_id"],
        )
        .first()
    )

    if existing:
        return None

    application = ApplicationModel(
        user_id=current_user_id,
        job_id=data["job_id"],
        job_title=data["job_title"],
        company=data.get("company"),
        location=data.get("location"),
        status=data.get("status", "saved"),
        resume_snapshot=data.get("resume_snapshot"),
        cover_letter=data.get("cover_letter"),
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    history = ApplicationStatusHistoryModel(
        application_id=application.id,
        user_id=current_user_id,
        from_status=None,
        to_status=application.status,
    )

    db.add(history)
    db.commit()

    return application


def list_applications_db(db: Session, user_id: int):
    current_user_id = get_current_user_id()

    return (
        db.query(ApplicationModel)
        .filter(ApplicationModel.user_id == user_id)
        .order_by(ApplicationModel.created_at.desc())
        .all()
    )


def update_application_status_db(db: Session, application_id: int, status: str):
    current_user_id = get_current_user_id()

    application = (
        db.query(ApplicationModel)
        .filter(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == current_user_id,
        )
        .first()
    )

    if not application:
        return None

    old_status = application.status

    if old_status == status:
        return application

    application.status = status
    db.commit()
    db.refresh(application)

    history = ApplicationStatusHistoryModel(
        application_id=application.id,
        user_id=current_user_id,
        from_status=old_status,
        to_status=status,
    )

    db.add(history)
    db.commit()

    return application


def delete_application_db(db: Session, application_id: int):
    current_user_id = get_current_user_id()

    application = (
        db.query(ApplicationModel)
        .filter(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == current_user_id,
        )
        .first()
    )

    if not application:
        return False

    (
        db.query(ApplicationStatusHistoryModel)
        .filter(
            ApplicationStatusHistoryModel.application_id == application.id,
            ApplicationStatusHistoryModel.user_id == current_user_id,
        )
        .delete(synchronize_session=False)
    )

    db.delete(application)
    db.commit()
    return True