import os
import logging
from typing import Optional

from openai import OpenAI, RateLimitError
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FALLBACK_MODEL = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY não configurada no ambiente.")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Você é um parser especialista em currículos.

Sua tarefa é extrair os dados do currículo e devolver APENAS os dados estruturados no schema esperado.

Regras obrigatórias:
- Não invente dados.
- Se não encontrar um campo, deixe null ou lista vazia.
- NÃO resuma experiências profissionais.
- Preserve o máximo de detalhe possível nas descrições das experiências.
- Mantenha responsabilidades, tecnologias, ferramentas, contextos e resultados sempre que estiverem presentes.
- Se uma experiência tiver várias linhas ou bullets, consolide tudo no campo "description" sem perder conteúdo relevante.
- NÃO simplifique linguagem técnica.
- NÃO reescreva em versão curta.
- Skills devem ser curtas, padronizadas e sem duplicidade óbvia.
- Experiências e formações devem vir em listas.
- Datas podem permanecer como string se o formato não estiver claro.
- Se houver um cargo atual e uma data final explícita, considere current = false.
- Se houver indicação clara de trabalho atual e não houver data final, considere current = true.

INSTRUÇÕES CRÍTICAS DE CLASSIFICAÇÃO:
Você deve separar corretamente:
- skills
- certifications
- courses

Essa separação é obrigatória.

INSTRUÇÕES PARA EXPERIÊNCIAS:
- "company" deve conter apenas a empresa.
- "role" deve conter apenas o cargo.
- "description" deve manter o máximo de profundidade possível.
- Se houver bullets, junte em um único texto coeso, sem perder informação.

INSTRUÇÕES PARA CERTIFICAÇÕES:
Certificações são credenciais formais emitidas por instituição reconhecida, normalmente associadas a exame, credencial oficial ou título certificado.

Inclua em "certifications" SOMENTE quando houver evidência de certificação formal.

Exemplos válidos:
- AWS Certified Solutions Architect
- Microsoft Certified: Azure Data Engineer
- Oracle Certified Professional
- PMP
- ITIL Foundation
- Certificado em Fundamentos do Scrum

Exemplos inválidos:
- Python Sênior
- DBA SQL Server
- Especialista em Dados
- Power BI
- Governança de Dados
- Tuning SQL
- Azure Storage

Se houver dúvida entre curso e certificação, prefira classificar como "courses", e NÃO como "certifications".

Para certificações:
- name = nome da certificação
- issuer = instituição emissora, se houver
- date = data, se houver

INSTRUÇÕES PARA CURSOS:
Cursos são:
- cursos livres
- treinamentos
- bootcamps
- formações online
- capacitações
- trilhas educacionais

Inclua em "courses" itens como:
- cursos da Alura
- cursos da Udemy
- cursos da ByLearn
- treinamentos internos
- formações técnicas
- capacitações sem credencial oficial clara

Exemplos válidos:
- Governança de Dados
- Azure Storage
- Tuning SQL
- Curso de SQL Server
- Formação Power BI
- Python Completo
- Data Warehouse com Data Lake e SQL Server
- Business Agility
- Dominando o Power BI

Se o currículo listar vários itens técnicos curtos sob uma seção de cursos, treinamentos, certificações ou competências, e não houver evidência clara de certificação oficial, classifique como "courses".

Para cursos:
- name = nome do curso ou treinamento
- institution = instituição, se houver
- date = data, se houver
- workload = carga horária, se houver

INSTRUÇÕES PARA SKILLS:
Skills são tecnologias, ferramentas, linguagens, metodologias e conhecimentos técnicos.

Exemplos:
- SQL Server
- Python
- Power BI
- ETL
- PostgreSQL
- Oracle
- SSIS

Skills não devem ser classificadas como certificações.

INSTRUÇÕES PARA IDIOMAS:
- Extraia nome e nível, quando houver.
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


class CertificationItem(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None


class CourseItem(BaseModel):
    name: Optional[str] = None
    institution: Optional[str] = None
    date: Optional[str] = None
    workload: Optional[str] = None


class LanguageItem(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None


class ResumeStructuredData(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    courses: list[CourseItem] = Field(default_factory=list)
    languages: list[LanguageItem] = Field(default_factory=list)


def normalize_resume_data(data: ResumeStructuredData) -> ResumeStructuredData:
    # current=false quando há end_date explícita
    for exp in data.experience:
        if exp.end_date and exp.end_date.strip():
            exp.current = False

    # skills: limpa vazios e deduplica
    normalized_skills = []
    seen_skills = set()

    for skill in data.skills:
        cleaned = (skill or "").strip()
        if not cleaned:
            continue

        key = cleaned.lower()
        if key not in seen_skills:
            seen_skills.add(key)
            normalized_skills.append(cleaned)

    data.skills = normalized_skills

    # certificações: limpa vazias
    cleaned_certifications = []
    for cert in data.certifications:
        if (
            (cert.name and cert.name.strip()) or
            (cert.issuer and cert.issuer.strip()) or
            (cert.date and cert.date.strip())
        ):
            cleaned_certifications.append(cert)

    data.certifications = cleaned_certifications

    # cursos: limpa vazios
    cleaned_courses = []
    for course in data.courses:
        if (
            (course.name and course.name.strip()) or
            (course.institution and course.institution.strip()) or
            (course.date and course.date.strip()) or
            (course.workload and course.workload.strip())
        ):
            cleaned_courses.append(course)

    data.courses = cleaned_courses

    # idiomas: limpa vazios
    cleaned_languages = []
    for lang in data.languages:
        if (lang.name and lang.name.strip()) or (lang.level and lang.level.strip()):
            cleaned_languages.append(lang)

    data.languages = cleaned_languages

    # reclassificação heurística: certificações falsas -> cursos
    cert_keywords = [
        "certified",
        "certification",
        "certificate",
        "certificado",
        "scrumstudy",
        "pmp",
        "itil",
        "foundation",
        "professional",
        "oracle certified",
        "microsoft certified",
        "aws certified",
    ]

    course_keywords = [
        "udemy",
        "alura",
        "bylearn",
        "curso",
        "treinamento",
        "bootcamp",
        "formação",
        "formacao",
        "trilha",
        "power bi",
        "governança",
        "governanca",
        "azure storage",
        "tuning sql",
        "mongo",
        "data warehouse",
        "python completo",
        "always on",
        "hadr",
    ]

    hard_not_certifications = {
        "governança de dados",
        "governanca de dados",
        "azure storage",
        "tuning sql",
        "dba sql server + always on",
        "python sênior",
        "python senior",
    }

    filtered_certifications = []
    moved_to_courses = []

    for cert in data.certifications:
        name = (cert.name or "").strip()
        issuer = (cert.issuer or "").strip()
        combined = f"{name} {issuer}".lower().strip()

        is_hard_not_cert = combined in hard_not_certifications
        looks_like_course = any(keyword in combined for keyword in course_keywords)
        looks_like_cert = any(keyword in combined for keyword in cert_keywords)

        # regra:
        # - se for explicitamente "não-certificação", mover para curso
        # - se parecer curso e não parecer certificação formal, mover para curso
        if is_hard_not_cert or (looks_like_course and not looks_like_cert):
            moved_to_courses.append(
                CourseItem(
                    name=cert.name,
                    institution=cert.issuer or None,
                    date=cert.date,
                    workload=None,
                )
            )
        else:
            filtered_certifications.append(cert)

    data.certifications = filtered_certifications
    data.courses.extend(moved_to_courses)

    # dedup de courses
    dedup_courses = []
    seen_courses = set()

    for course in data.courses:
        name = (course.name or "").strip()
        institution = (course.institution or "").strip()
        key = f"{name.lower()}|{institution.lower()}"

        if not name:
            continue

        if key not in seen_courses:
            seen_courses.add(key)
            dedup_courses.append(course)

    data.courses = dedup_courses

    return data


def parse_with_model(model: str, text: str) -> ResumeStructuredData:
    response = client.responses.parse(
        model=model,
        instructions=SYSTEM_PROMPT,
        input=f"Currículo:\n\n{text}",
        text_format=ResumeStructuredData,
    )

    parsed = response.output_parsed

    if not parsed:
        raise ValueError("A OpenAI não retornou output_parsed.")

    return parsed


def needs_fallback(parsed: ResumeStructuredData) -> bool:
    if not parsed.experience or len(parsed.experience) < 1:
        return True

    if len(parsed.skills) < 3:
        return True

    # se todas as descrições vierem curtas demais, provavelmente parse ficou fraco
    detailed_experiences = sum(
        1 for exp in parsed.experience
        if (exp.description or "").strip() and len((exp.description or "").strip()) >= 80
    )

    if detailed_experiences < 1:
        return True

    return False


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
        parsed = parse_with_model(OPENAI_MODEL, text)

        if needs_fallback(parsed) and FALLBACK_MODEL and FALLBACK_MODEL != OPENAI_MODEL:
            print(f"Fallback para {FALLBACK_MODEL} (qualidade mínima insuficiente)")
            parsed = parse_with_model(FALLBACK_MODEL, text)

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