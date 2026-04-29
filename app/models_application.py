from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint

from app.database import Base


class ApplicationModel(Base):
    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)

    job_id = Column(Integer, nullable=False, index=True)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(30), nullable=False, default="saved")
    resume_snapshot = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)