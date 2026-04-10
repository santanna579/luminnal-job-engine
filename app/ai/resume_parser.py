import os
import logging
from typing import Optional

from openai import OpenAI, RateLimitError
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY não configurada no ambiente.")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Você é um parser especialista em currículos.
Extraia as informações do currículo e devolva APENAS os dados estruturados no schema esperado.

Regras:
- Não invente dados.
- Se não encontrar um campo, deixe null ou lista vazia.
- Normalize textos quando fizer sentido.
- Datas podem permanecer como string se o formato não estiver claro.
- Skills devem ser curtas e sem duplicidade.
- Experiências e formações devem vir em listas.
"""

class ContactInfo(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class ExperienceItem(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: Optional[bool] = None
    description: Optional[str] = None


class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ResumeStructuredData(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


def normalize_resume_data(data: ResumeStructuredData) -> ResumeStructuredData:
    for exp in data.experience:
        if exp.end_date and exp.end_date.strip():
            exp.current = False

    return data


def parse_resume(text: str) -> ResumeStructuredData:
    if not text or not text.strip():
        raise ValueError("Texto do currículo vazio.")
    
    if len(text.strip()) < 50:
        raise ValueError("Texto extraído insuficiente para fazer o parse do currículo.")
    
    print("\n========== TEXTO RECEBIDO PELO PARSER ==========")
    print(text[:2000])
    print("========== FIM TEXTO RECEBIDO PELO PARSER ==========\n")
    print(f"Tamanho do texto recebido pelo parser: {len(text)}")

    try:
        response = client.responses.parse(
            model=OPENAI_MODEL,
            instructions=SYSTEM_PROMPT,
            input=f"Currículo:\n\n{text}",
            text_format=ResumeStructuredData,
        )

        parsed = response.output_parsed

        if not parsed:
            raise ValueError("A OpenAI não retornou output_parsed.")

        parsed = normalize_resume_data(parsed)

        return parsed

    except RateLimitError as e:
        logger.exception("Quota da OpenAI excedida.")
        raise RuntimeError(
            "A integração com OpenAI está ativa, mas a conta está sem quota/crédito disponível no momento."
        ) from e

    except Exception as e:
        logger.exception("Erro ao fazer parse do currículo com OpenAI.")
        raise RuntimeError(f"Falha no parse do currículo: {str(e)}") from e