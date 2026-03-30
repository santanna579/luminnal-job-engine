from sqlalchemy import Column, Integer, String, Text

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