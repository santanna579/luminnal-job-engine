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
    criado_em = Column(DateTime, default=datetime.utcnow)