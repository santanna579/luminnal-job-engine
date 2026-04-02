from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class GeneratedContentModel(Base):
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, index=True)
    vaga_id = Column(Integer, nullable=False)
    nome_candidato = Column(String(100), nullable=False)
    resumo_profissional_adaptado = Column(Text, nullable=False)
    carta_apresentacao = Column(Text, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)