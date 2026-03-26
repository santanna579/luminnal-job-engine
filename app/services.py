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