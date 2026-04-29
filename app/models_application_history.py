from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from app.database import Base


class ApplicationStatusHistoryModel(Base):
    __tablename__ = "application_status_history"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(Integer, nullable=False, index=True)

    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)

    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)