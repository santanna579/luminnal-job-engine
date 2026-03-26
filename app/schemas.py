from pydantic import BaseModel, Field
from typing import List


class JobInput(BaseModel):
    titulo: str = Field(..., example="Data Engineer")
    empresa: str = Field(..., example="Tech Company")
    localizacao: str = Field(..., example="Remoto - Brasil")
    descricao: str = Field(..., example="Estamos buscando um profissional com experiência em Python, SQL e AWS.")


class JobAnalysisResponse(BaseModel):
    score: int
    nivel_aderencia: str
    palavras_chave_encontradas: List[str]
    gaps_identificados: List[str]
    recomendacao: str