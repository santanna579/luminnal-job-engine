from typing import Dict, List


def semantic_match_with_ai(profile_data: Dict, job_data: Dict) -> Dict:
    profile_skills = set(profile_data.get("skills_identificadas", []))
    job_skills = set(job_data.get("skills_identificadas", []))

    skills_em_comum = sorted(list(profile_skills.intersection(job_skills)))
    skills_faltantes = sorted(list(job_skills - profile_skills))
    skills_extras = sorted(list(profile_skills - job_skills))

    senioridade_perfil = profile_data.get("senioridade_estimada", "not_defined")
    senioridade_vaga = job_data.get("senioridade_estimada", "not_defined")
    ingles_exigido = job_data.get("ingles_exigido", False)

    senioridade_compativel = False
    if senioridade_vaga == "not_defined":
        senioridade_compativel = True
    elif senioridade_perfil == senioridade_vaga:
        senioridade_compativel = True
    elif senioridade_perfil == "senior" and senioridade_vaga in ["pleno", "junior"]:
        senioridade_compativel = True
    elif senioridade_perfil == "pleno" and senioridade_vaga == "junior":
        senioridade_compativel = True

    ingles_compativel = ingles_exigido  # aqui vamos complementar no service com base no perfil real
    if not ingles_exigido:
        ingles_compativel = True

    score_skills = min(len(skills_em_comum) * 20, 60)
    score_senioridade = 20 if senioridade_compativel else 0
    score_ingles = 20 if ingles_compativel else 0

    score_total = min(score_skills + score_senioridade + score_ingles, 100)

    if score_total >= 80:
        recomendacao = "Alta compatibilidade semântica"
    elif score_total >= 50:
        recomendacao = "Compatibilidade semântica moderada"
    else:
        recomendacao = "Baixa compatibilidade semântica"

    forcas_transferiveis: List[str] = skills_extras[:5]

    resumo = (
        f"Skills em comum: {', '.join(skills_em_comum) if skills_em_comum else 'nenhuma identificada'}. "
        f"Skills faltantes: {', '.join(skills_faltantes) if skills_faltantes else 'nenhuma relevante'}. "
        f"Senioridade compatível: {'sim' if senioridade_compativel else 'não'}. "
        f"Inglês compatível: {'sim' if ingles_compativel else 'não'}. "
        f"Recomendação: {recomendacao}."
    )

    return {
        "score": score_total,
        "skills_em_comum": skills_em_comum,
        "skills_faltantes": skills_faltantes,
        "forcas_transferiveis": forcas_transferiveis,
        "senioridade_compativel": senioridade_compativel,
        "ingles_compativel": ingles_compativel,
        "recomendacao": recomendacao,
        "resumo_match_semantico": resumo,
    }