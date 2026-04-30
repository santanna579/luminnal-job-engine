from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class JobMatchModel(Base):
    __tablename__ = "job_match"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True, index=True)

    vaga_id = Column(Integer, nullable=False, index=True)
    nome_candidato = Column(String(100), nullable=False)

    score = Column(Integer, nullable=False)
    score_skills = Column(Integer, nullable=False)
    score_senioridade = Column(Integer, nullable=False)
    score_ingles = Column(Integer, nullable=False)

    nivel_aderencia = Column(String(50), nullable=False)

    palavras_chave_encontradas = Column(Text, nullable=True)
    skills_nao_relevantes = Column(Text, nullable=True)
    exigencias_nao_cobertas = Column(Text, nullable=True)

    recomendacao = Column(String(255), nullable=False)
    resumo_analitico = Column(Text, nullable=True)

    criado_em = Column(DateTime, default=datetime.utcnow)