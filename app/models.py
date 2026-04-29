from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database import Base


class CandidateProfileModel(Base):
    __tablename__ = "candidate_profile"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cargo_atual = Column(String(100), nullable=False)
    anos_experiencia = Column(Integer, nullable=False)
    skills = Column(Text, nullable=False)
    nivel_ingles = Column(String(50), nullable=False)
    objetivo = Column(String(100), nullable=False)

    raw_resume_text = Column(Text, nullable=True)
    profile_json = Column(Text, nullable=True)
    profile_summary = Column(Text, nullable=True)
    last_ai_processed_at = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

class UserProfileModel(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)

    profile_json = Column(Text, nullable=False)
    resume_filename = Column(String(255), nullable=True)

    snapshot_type = Column(String(20), nullable=False)  # active | previous

    created_at = Column(DateTime, default=datetime.utcnow)