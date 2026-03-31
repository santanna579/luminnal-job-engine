from typing import Dict, List


SKILL_CATALOG = [
    "python",
    "sql",
    "oracle",
    "sql server",
    "postgresql",
    "etl",
    "ssis",
    "power bi",
    "aws",
    "azure",
    "airflow",
    "docker",
    "fastapi",
    "data warehouse",
    "modelagem de dados",
    "snowflake",
]


def _extract_skills(raw_resume_text: str) -> List[str]:
    text = raw_resume_text.lower()
    found = []

    for skill in SKILL_CATALOG:
        if skill in text:
            found.append(skill)

    return found


def _estimate_seniority(raw_resume_text: str) -> str:
    text = raw_resume_text.lower()

    if "senior" in text or "sênior" in text or "10 anos" in text or "8 anos" in text or "7 anos" in text:
        return "senior"
    if "pleno" in text or "5 anos" in text or "4 anos" in text or "3 anos" in text:
        return "pleno"
    return "junior"


def parse_resume_with_ai(raw_resume_text: str) -> Dict:
    skills = _extract_skills(raw_resume_text)
    seniority = _estimate_seniority(raw_resume_text)

    profile_json = {
        "skills_identificadas": skills,
        "senioridade_estimada": seniority,
        "texto_original_presente": bool(raw_resume_text and raw_resume_text.strip())
    }

    if skills:
        resumo = (
            f"Currículo indica experiência com: {', '.join(skills)}. "
            f"Senioridade estimada: {seniority}."
        )
    else:
        resumo = (
            f"Não foi possível identificar skills com confiança. "
            f"Senioridade estimada: {seniority}."
        )

    return {
        "raw_resume_text": raw_resume_text,
        "profile_json": profile_json,
        "profile_summary": resumo,
        "status": "processed"
    }