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


def _extract_skills(raw_description: str) -> List[str]:
    text = raw_description.lower()
    found = []

    for skill in SKILL_CATALOG:
        if skill in text:
            found.append(skill)

    return found


def _estimate_seniority(raw_description: str) -> str:
    text = raw_description.lower()

    if "senior" in text or "sênior" in text:
        return "senior"
    if "pleno" in text:
        return "pleno"
    if "junior" in text or "júnior" in text:
        return "junior"
    return "not_defined"


def _detect_english_requirement(raw_description: str) -> bool:
    text = raw_description.lower()
    return "english" in text or "ingles" in text or "inglês" in text


def parse_job_with_ai(raw_description: str) -> Dict:
    skills = _extract_skills(raw_description)
    seniority = _estimate_seniority(raw_description)
    english_required = _detect_english_requirement(raw_description)

    job_json = {
        "skills_identificadas": skills,
        "senioridade_estimada": seniority,
        "ingles_exigido": english_required,
        "texto_original_presente": bool(raw_description and raw_description.strip())
    }

    resumo_partes = []

    if skills:
        resumo_partes.append(f"Vaga indica skills como: {', '.join(skills)}.")
    else:
        resumo_partes.append("Não foi possível identificar skills com confiança.")

    resumo_partes.append(f"Senioridade estimada: {seniority}.")

    if english_required:
        resumo_partes.append("Há indício de exigência de inglês.")
    else:
        resumo_partes.append("Não há indício claro de exigência de inglês.")

    return {
        "raw_description": raw_description,
        "job_json": job_json,
        "job_summary": " ".join(resumo_partes),
        "status": "processed"
    }