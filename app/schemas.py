from pydantic import BaseModel, Field
from typing import List


class JobInput(BaseModel):
    titulo: str = Field(..., example="Data Engineer")
    empresa: str = Field(..., example="Tech Company")
    localizacao: str = Field(..., example="Remoto - Brasil")
    descricao: str = Field(..., example="Estamos buscando um profissional com experiência em Python, SQL e AWS.")


class JobAnalysisResponse(BaseModel):
    score: int
    score_skills: int
    score_senioridade: int
    score_ingles: int
    nivel_aderencia: str
    palavras_chave_encontradas: List[str]
    skills_do_candidato_nao_relevantes_para_esta_vaga: List[str]
    exigencias_da_vaga_nao_cobertas: List[str]
    recomendacao: str
    resumo_analitico: str


class CandidateProfile(BaseModel):
    nome: str
    cargo_atual: str
    anos_experiencia: int
    skills: List[str]
    nivel_ingles: str
    objetivo: str


class JobWithProfileInput(BaseModel):
    vaga: JobInput
    candidato: CandidateProfile