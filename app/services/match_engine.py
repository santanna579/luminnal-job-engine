import json
import math
import re
from typing import List, Dict, Any, Tuple

from app.schemas.match import MatchProfile, MatchJob


def normalize_text(value: str) -> str:
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_token(value: str) -> str:
    value = normalize_text(value)
    value = re.sub(r"[^a-z0-9áàâãéèêíïóôõöúç\+\#\.\-\s]", "", value)
    return value.strip()

def canonicalize_skill(value: str) -> str:
    if not value:
        return ""

    skill = normalize_token(value)

    synonyms = {
        "sql server": "sql",
        "t-sql": "sql",
        "tsql": "sql",
        "pl/sql": "sql",
        "plsql": "sql",
        "postgres": "postgresql",
        "modelagem de dados": "data modeling",
        "analise de dados": "analytics",
        "análise de dados": "analytics",
        "powerbi": "power bi",
    }

    return synonyms.get(skill, skill)


def normalize_skill_list(items: list[str]) -> list[str]:
    result = []
    seen = set()

    for item in items:
        normalized = canonicalize_skill(item)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return result

def unique_normalized_items(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        norm = normalize_token(item)
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def build_profile_experience_text(profile: MatchProfile) -> str:
    parts = []

    if profile.summary:
        parts.append(profile.summary)

    for exp in profile.experience:
        chunk = " ".join(
            [
                exp.title or "",
                exp.company or "",
                exp.description or "",
            ]
        ).strip()
        if chunk:
            parts.append(chunk)

    return " ".join(parts)


def build_job_text(job: MatchJob) -> str:
    parts = [
        job.title or "",
        job.description or "",
        " ".join(job.requirements or []),
        " ".join(job.nice_to_have or []),
        job.seniority or "",
    ]
    return " ".join(parts).strip()


def extract_job_keywords(job: MatchJob) -> List[str]:
    raw_items = []
    raw_items.extend(job.requirements or [])
    raw_items.extend(job.nice_to_have or [])

    if job.title:
        raw_items.append(job.title)

    return unique_normalized_items(raw_items)


def compute_skills_match(profile: MatchProfile, job: MatchJob) -> tuple[int, dict]:
    profile_skills = normalize_skill_list(profile.skills or [])
    job_keywords = normalize_skill_list(extract_job_keywords(job))

    if not job_keywords:
        return 50, {
            "matched_skills": [],
            "missing_skills": [],
            "profile_skills": profile_skills,
            "job_keywords": job_keywords,
        }

    strong_weights = {
        "sql": 2,
        "python": 2,
        "etl": 2,
        "data modeling": 2,
    }

    profile_skill_set = set(profile_skills)

    matched = []
    missing = []
    score_points = 0
    total_points = 0

    for keyword in job_keywords:
        weight = strong_weights.get(keyword, 1)
        total_points += weight

        if keyword in profile_skill_set:
            matched.append(keyword)
            score_points += weight
        else:
            missing.append(keyword)

    score = int(round((score_points / max(total_points, 1)) * 100))

    return score, {
        "matched_skills": matched,
        "missing_skills": missing,
        "profile_skills": profile_skills,
        "job_keywords": job_keywords,
        "score_points": score_points,
        "total_points": total_points,
    }


def compute_experience_match(profile: MatchProfile, job: MatchJob) -> tuple[int, dict]:
    profile_text = normalize_text(build_profile_experience_text(profile))
    job_text = normalize_text(build_job_text(job))

    if not profile_text or not job_text:
        return 40, {
            "reason": "profile_or_job_text_missing"
        }

    job_terms = normalize_skill_list(
        (job.requirements or []) +
        (job.nice_to_have or []) +
        ([job.title] if job.title else [])
    )

    matched_terms = [term for term in job_terms if term and term in profile_text]

    base_ratio = len(matched_terms) / max(len(job_terms), 1)
    base_score = int(round(base_ratio * 100))

    experience_bonus = 0
    seniority_bonus = 0
    title_bonus = 0

    if profile.experience:
        experience_bonus += 10

    joined_titles = " ".join(
        normalize_text(exp.title or "") for exp in profile.experience
    )

    senior_terms = ["senior", "lead", "specialist", "staff", "principal", "sr"]
    mid_terms = ["pleno", "mid", "intermediate"]

    job_title_normalized = normalize_text(job.title or "")
    job_seniority_normalized = normalize_text(job.seniority or "")

    if any(term in joined_titles for term in senior_terms):
        seniority_bonus += 10
    elif any(term in joined_titles for term in mid_terms):
        seniority_bonus += 5

    if "engineer" in job_title_normalized and "engineer" in joined_titles:
        title_bonus += 8
    elif "analyst" in job_title_normalized and "analyst" in joined_titles:
        title_bonus += 8
    elif "dba" in job_title_normalized and "dba" in joined_titles:
        title_bonus += 8
    elif "data" in job_title_normalized and "data" in joined_titles:
        title_bonus += 5

    final_score = base_score + experience_bonus + seniority_bonus + title_bonus
    final_score = max(0, min(100, final_score))

    return final_score, {
        "matched_experience_terms": matched_terms,
        "job_terms_considered": job_terms,
        "experience_bonus": experience_bonus,
        "seniority_bonus": seniority_bonus,
        "title_bonus": title_bonus,
    }


def try_semantic_llm_analysis(profile: MatchProfile, job: MatchJob) -> Dict[str, Any]:
    """
    Esta função foi desenhada para ficar isolada.
    Aqui você encaixa o client OpenAI que já existe no seu projeto.
    Se falhar, o sistema continua funcionando com fallback determinístico.
    """

    try:
        # IMPORTANTE:
        # Ajuste este import conforme o helper que já existe no seu projeto.
        # Exemplo comum:
        # from app.services.openai_client import get_openai_client
        # client = get_openai_client()

        from openai import OpenAI
        client = OpenAI()

        profile_payload = {
            "summary": profile.summary,
            "skills": profile.skills,
            "experience": [
                {
                    "title": exp.title,
                    "company": exp.company,
                    "description": exp.description,
                }
                for exp in profile.experience
            ],
            "education": [
                {
                    "degree": edu.degree,
                    "institution": edu.institution,
                    "field_of_study": edu.field_of_study,
                }
                for edu in profile.education
            ],
            "languages": profile.languages,
            "certifications": profile.certifications,
        }

        job_payload = {
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "requirements": job.requirements,
            "nice_to_have": job.nice_to_have,
            "seniority": job.seniority,
        }

        system_prompt = """
Você é um mecanismo de análise de compatibilidade entre candidato e vaga.

Responda SEMPRE em português do Brasil.

Retorne APENAS JSON válido com a seguinte estrutura:
{
  "semantic_score": number,
  "summary": "string",
  "strengths": ["string"],
  "gaps": ["string"],
  "suggestions": ["string"]
}

Regras:
- semantic_score deve estar entre 0 e 100
- Seja objetivo, claro e profissional
- strengths: pontos fortes reais do candidato para a vaga
- gaps: lacunas reais do perfil em relação à vaga
- suggestions: ações práticas e úteis para melhorar aderência
- Não use markdown
- Não use inglês
- Não invente experiência inexistente
"""

        user_prompt = f"""
CANDIDATE_PROFILE:
{json.dumps(profile_payload, ensure_ascii=False)}

JOB:
{json.dumps(job_payload, ensure_ascii=False)}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)

        semantic_score = int(parsed.get("semantic_score", 50))
        semantic_score = max(0, min(100, semantic_score))

        return {
            "semantic_score": semantic_score,
            "summary": parsed.get("summary", ""),
            "strengths": parsed.get("strengths", []),
            "gaps": parsed.get("gaps", []),
            "suggestions": parsed.get("suggestions", []),
            "source": "llm",
        }

    except Exception as exc:
        return {
            "semantic_score": 50,
            "summary": "",
            "strengths": [],
            "gaps": [],
            "suggestions": [],
            "source": "fallback",
            "error": str(exc),
        }


def build_fallback_semantic_result(
    skills_data: Dict[str, Any],
    experience_data: Dict[str, Any],
    skills_score: int,
    experience_score: int,
    profile: MatchProfile,
    job: MatchJob,
) -> Dict[str, Any]:
    matched_skills = skills_data.get("matched_skills", [])
    missing_skills = skills_data.get("missing_skills", [])

    strengths = []
    gaps = []
    suggestions = []

    if matched_skills:
        strengths.append(
            f"O perfil já demonstra aderência em competências relevantes como: {', '.join(matched_skills[:5])}."
        )

    if profile.experience:
        strengths.append(
            "O candidato possui histórico profissional estruturado, o que fortalece a leitura de aderência para a vaga."
        )

    if missing_skills:
        gaps.append(
            f"Há sinais de lacuna em requisitos importantes, principalmente: {', '.join(missing_skills[:5])}."
        )
        suggestions.append(
            "Inclua no perfil skills técnicas e funcionais que já domina, mas que ainda não estão explícitas."
        )
        suggestions.append(
            "Reforce no resumo profissional a aderência direta aos requisitos centrais da vaga."
        )

    if not profile.summary:
        gaps.append("O perfil não possui um resumo profissional forte o suficiente para contextualizar a candidatura.")
        suggestions.append("Adicione um resumo profissional orientado ao tipo de vaga que deseja alcançar.")

    semantic_score = int(round((skills_score * 0.6) + (experience_score * 0.4)))

    summary = (
        "O match foi calculado com base em aderência de skills e sinais de experiência presentes no perfil, "
        "com análise heurística inicial."
    )

    return {
        "semantic_score": semantic_score,
        "summary": summary,
        "strengths": strengths[:4],
        "gaps": gaps[:4],
        "suggestions": suggestions[:4],
        "source": "fallback_rule_based",
    }


def compute_final_score(skills_score: int, experience_score: int, semantic_score: int) -> int:
    semantic_score = max(20, semantic_score)

    final_score = (
        (skills_score * 0.40) +
        (experience_score * 0.40) +
        (semantic_score * 0.20)
    )
    return int(round(final_score))


def calculate_match(profile: MatchProfile, job: MatchJob) -> Dict[str, Any]:
    skills_score, skills_data = compute_skills_match(profile, job)
    experience_score, experience_data = compute_experience_match(profile, job)

    semantic_result = try_semantic_llm_analysis(profile, job)

    if semantic_result.get("source") != "llm":
        semantic_result = build_fallback_semantic_result(
            skills_data=skills_data,
            experience_data=experience_data,
            skills_score=skills_score,
            experience_score=experience_score,
            profile=profile,
            job=job,
        )

    semantic_score = int(semantic_result.get("semantic_score", 50))
    final_score = compute_final_score(skills_score, experience_score, semantic_score)

    return {
        "score": final_score,
        "summary": semantic_result.get("summary", ""),
        "strengths": semantic_result.get("strengths", []),
        "gaps": semantic_result.get("gaps", []),
        "suggestions": semantic_result.get("suggestions", []),
        "details": {
            "skills_score": skills_score,
            "experience_score": experience_score,
            "semantic_score": semantic_score,
        },
        "debug": {
            "skills_data": skills_data,
            "experience_data": experience_data,
            "semantic_source": semantic_result.get("source"),
        },
    }