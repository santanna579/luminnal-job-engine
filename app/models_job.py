from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database import Base


class JobPostingModel(Base):
    __tablename__ = "job_posting"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    empresa = Column(String(200), nullable=False)
    localizacao = Column(String(200), nullable=True)
    origem = Column(String(50), nullable=False, default="linkedin")
    url = Column(Text, nullable=True)
    descricao = Column(Text, nullable=False)

    raw_description = Column(Text, nullable=True)
    job_json = Column(Text, nullable=True)
    job_summary = Column(Text, nullable=True)
    last_ai_processed_at = Column(DateTime, nullable=True)

    criado_em = Column(DateTime, default=datetime.utcnow)