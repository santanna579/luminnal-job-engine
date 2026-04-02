from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class JobCreate(BaseModel):
    titulo: str
    empresa: str
    localizacao: Optional[str] = None
    origem: str = "linkedin"
    url: Optional[str] = None
    descricao: str


class JobResponse(BaseModel):
    id: int
    titulo: str
    empresa: str
    localizacao: Optional[str] = None
    origem: str
    url: Optional[str] = None
    descricao: str
    criado_em: datetime

    class Config:
        from_attributes = True


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


class JobMatchResponse(BaseModel):
    id: int
    vaga_id: int
    nome_candidato: str
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
    criado_em: datetime

    class Config:
        from_attributes = True

class RecommendedJobResponse(BaseModel):
    vaga_id: int
    titulo: str
    empresa: str
    localizacao: Optional[str] = None
    origem: str
    url: Optional[str] = None
    score: int
    nivel_aderencia: str
    recomendacao: str
    resumo_analitico: str


class CandidateProfileRawInput(BaseModel):
    nome: str
    cargo_atual: str
    anos_experiencia: int
    skills: List[str]
    nivel_ingles: str
    objetivo: str
    raw_resume_text: str
    profile_json: Optional[str] = None
    profile_summary: Optional[str] = None


class CandidateProfileRawResponse(BaseModel):
    nome: str
    cargo_atual: str
    anos_experiencia: int
    skills: List[str]
    nivel_ingles: str
    objetivo: str
    raw_resume_text: Optional[str] = None
    profile_json: Optional[str] = None
    profile_summary: Optional[str] = None


class JobRawInput(BaseModel):
    titulo: str
    empresa: str
    localizacao: Optional[str] = None
    origem: str = "linkedin"
    url: Optional[str] = None
    descricao: str
    raw_description: Optional[str] = None
    job_json: Optional[str] = None
    job_summary: Optional[str] = None


class JobRawResponse(BaseModel):
    id: int
    titulo: str
    empresa: str
    localizacao: Optional[str] = None
    origem: str
    url: Optional[str] = None
    descricao: str
    raw_description: Optional[str] = None
    job_json: Optional[str] = None
    job_summary: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class CandidateProfileProcessedResponse(BaseModel):
    nome: str
    cargo_atual: str
    anos_experiencia: int
    skills: List[str]
    nivel_ingles: str
    objetivo: str
    raw_resume_text: Optional[str] = None
    profile_json: Optional[Any] = None
    profile_summary: Optional[str] = None


class JobProcessedResponse(BaseModel):
    id: int
    titulo: str
    empresa: str
    localizacao: Optional[str] = None
    origem: str
    url: Optional[str] = None
    descricao: str
    raw_description: Optional[str] = None
    job_json: Optional[Any] = None
    job_summary: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True

class SemanticMatchResponse(BaseModel):
    score: int
    skills_em_comum: List[str]
    skills_faltantes: List[str]
    forcas_transferiveis: List[str]
    senioridade_compativel: bool
    ingles_compativel: bool
    recomendacao: str
    resumo_match_semantico: str


class ResumeAdaptadoResponse(BaseModel):
    resumo_profissional_adaptado: str
    skills_para_destacar: List[str]
    gaps_para_contornar: List[str]
    carta_apresentacao: str


class GeneratedContentResponse(BaseModel):
    id: int
    vaga_id: int
    nome_candidato: str
    resumo_profissional_adaptado: str
    carta_apresentacao: str
    criado_em: datetime

    class Config:
        from_attributes = True

class JobFeedItem(BaseModel):
    vaga_id: int
    titulo: str
    empresa: str
    localizacao: str
    score: int
    nivel_aderencia: str
    resumo_match: str