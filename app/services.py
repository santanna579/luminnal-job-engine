from typing import List, Dict


PALAVRAS_CHAVE_BASE = [
    "python",
    "sql",
    "aws",
    "azure",
    "etl",
    "data warehouse",
    "airflow",
    "spark",
    "power bi",
    "oracle",
    "sql server",
    "postgresql",
    "modelagem de dados",
    "data modeling",
    "snowflake",
    "docker",
    "api",
    "fastapi",
    "ingles",
    "english",
    "remote",
    "remoto",
]


def analisar_vaga_texto(descricao: str) -> Dict:
    descricao_lower = descricao.lower()

    encontradas: List[str] = [
        palavra for palavra in PALAVRAS_CHAVE_BASE if palavra in descricao_lower
    ]

    gaps: List[str] = [
        palavra for palavra in ["python", "sql", "etl", "aws", "modelagem de dados"]
        if palavra not in descricao_lower
    ]

    score = min(len(encontradas) * 10, 100)

    if score >= 70:
        nivel = "alta"
        recomendacao = "Aplicar"
    elif score >= 40:
        nivel = "media"
        recomendacao = "Aplicar com revisão"
    else:
        nivel = "baixa"
        recomendacao = "Descartar ou avaliar com cautela"

    return {
        "score": score,
        "nivel_aderencia": nivel,
        "palavras_chave_encontradas": encontradas,
        "gaps_identificados": gaps,
        "recomendacao": recomendacao,
    }


def analisar_com_perfil(descricao: str, skills_candidato: List[str], nivel_ingles: str, anos_experiencia: int) -> Dict:
    descricao_lower = descricao.lower()
    skills_lower = [s.lower() for s in skills_candidato]

    skills_criticas = ["python", "sql", "etl", "aws"]
    skills_secundarias = ["oracle", "power bi", "docker", "airflow"]

    skills_esperadas_na_vaga = skills_criticas + skills_secundarias

    matches = []
    skills_nao_relevantes = []
    exigencias_nao_cobertas = []

    score_skills = 0

    for skill in skills_lower:
        if skill in descricao_lower:
            matches.append(skill)

            if skill in skills_criticas:
                score_skills += 20
            elif skill in skills_secundarias:
                score_skills += 10
            else:
                score_skills += 5
        else:
            skills_nao_relevantes.append(skill)

    for skill in skills_esperadas_na_vaga:
        if skill in descricao_lower and skill not in skills_lower:
            exigencias_nao_cobertas.append(skill)

    score_skills = min(score_skills, 70)

    score_senioridade = 0
    if "senior" in descricao_lower or "sênior" in descricao_lower:
        if anos_experiencia >= 5:
            score_senioridade = 15
    elif "pleno" in descricao_lower:
        if anos_experiencia >= 3:
            score_senioridade = 15
    elif "junior" in descricao_lower or "júnior" in descricao_lower:
        if anos_experiencia >= 1:
            score_senioridade = 15
    else:
        score_senioridade = 10

    score_ingles = 0
    exige_ingles = "english" in descricao_lower or "ingles" in descricao_lower or "inglês" in descricao_lower

    if exige_ingles:
        if nivel_ingles.lower() in ["intermediario", "intermediário", "avancado", "avançado", "fluente"]:
            score_ingles = 15
    else:
        score_ingles = 15

    score_total = min(score_skills + score_senioridade + score_ingles, 100)

    if score_total >= 80:
        nivel = "alta"
        recomendacao = "Aplicar com confiança"
    elif score_total >= 50:
        nivel = "media"
        recomendacao = "Aplicar com ajustes no currículo"
    else:
        nivel = "baixa"
        recomendacao = "Baixa aderência"

    if exige_ingles and score_ingles == 0:
        exigencias_nao_cobertas.append("ingles")

    if score_senioridade < 15:
        exigencias_nao_cobertas.append("senioridade_aderente")

    partes_resumo = []

    if matches:
        partes_resumo.append(
            f"Boa aderência nas skills: {', '.join(matches)}."
        )
    else:
        partes_resumo.append(
            "Pouca aderência técnica identificada nas skills principais."
        )

    if exigencias_nao_cobertas:
        partes_resumo.append(
            f"Gaps relevantes para a vaga: {', '.join(exigencias_nao_cobertas)}."
        )

    if skills_nao_relevantes:
        partes_resumo.append(
            f"Skills do candidato que não agregam tanto nesta vaga: {', '.join(skills_nao_relevantes)}."
        )

    partes_resumo.append(f"Recomendação final: {recomendacao}.")

    resumo_analitico = " ".join(partes_resumo)

    return {
        "score": score_total,
        "score_skills": score_skills,
        "score_senioridade": score_senioridade,
        "score_ingles": score_ingles,
        "nivel_aderencia": nivel,
        "palavras_chave_encontradas": matches,
        "skills_do_candidato_nao_relevantes_para_esta_vaga": skills_nao_relevantes,
        "exigencias_da_vaga_nao_cobertas": exigencias_nao_cobertas,
        "recomendacao": recomendacao,
        "resumo_analitico": resumo_analitico,
    }

perfil_candidato_storage = None


def salvar_perfil_candidato(perfil: Dict) -> Dict:
    global perfil_candidato_storage
    perfil_candidato_storage = perfil
    return perfil_candidato_storage


def obter_perfil_candidato() -> Dict | None:
    return perfil_candidato_storage