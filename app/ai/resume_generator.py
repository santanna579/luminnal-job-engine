from typing import Dict


def gerar_resumo_e_carta(profile: Dict, job: Dict, match: Dict) -> Dict:
    skills_comum = match.get("skills_em_comum", [])
    skills_faltantes = match.get("skills_faltantes", [])
    forcas = match.get("forcas_transferiveis", [])

    nome = profile.get("nome", "Profissional")
    objetivo = profile.get("objetivo", "área de dados")
    anos = profile.get("anos_experiencia", 0)

    titulo_vaga = job.get("titulo", "")
    empresa = job.get("empresa", "")

    # ======================
    # RESUMO PROFISSIONAL
    # ======================
    resumo = (
        f"Profissional com {anos} anos de experiência na área de dados, "
        f"com forte atuação em {', '.join(skills_comum) if skills_comum else 'tecnologias relevantes'}. "
    )

    if forcas:
        resumo += f"Possui experiência adicional em {', '.join(forcas[:3])}, agregando versatilidade técnica. "

    if skills_faltantes:
        resumo += (
            f"Atualmente em evolução em tecnologias como {', '.join(skills_faltantes)}, "
            f"com foco em alinhamento às demandas do mercado. "
        )

    resumo += f"Busca oportunidade como {titulo_vaga} para gerar impacto e crescimento contínuo."

    # ======================
    # SKILLS PARA DESTACAR
    # ======================
    skills_destacar = skills_comum + forcas[:2]

    # ======================
    # GAPS
    # ======================
    gaps = skills_faltantes

    # ======================
    # CARTA DE APRESENTAÇÃO
    # ======================
    carta = f"""
Olá,

Meu nome é {nome} e gostaria de me candidatar à vaga de {titulo_vaga} na {empresa}.

Ao analisar a descrição da vaga, identifiquei uma forte aderência com minha experiência, especialmente em {', '.join(skills_comum) if skills_comum else 'tecnologias da área'}.

Tenho {anos} anos de atuação na área de dados, com experiência em projetos envolvendo {', '.join(forcas[:3]) if forcas else 'análise e engenharia de dados'}.

Atualmente, também venho aprofundando meus conhecimentos em {', '.join(skills_faltantes) if skills_faltantes else 'novas tecnologias relevantes'}, buscando constante evolução e alinhamento com o mercado.

Acredito que posso contribuir com a equipe trazendo visão analítica, experiência prática e capacidade de adaptação.

Fico à disposição para conversarmos melhor.

Atenciosamente,  
{nome}
""".strip()

    curriculo_estruturado = {
        "nome": nome,
        "titulo_objetivo": titulo_vaga,
        "resumo": resumo,
        "skills": skills_destacar,
        "gaps": gaps
    }

    return {
        "resumo_profissional_adaptado": resumo,
        "skills_para_destacar": skills_destacar,
        "gaps_para_contornar": gaps,
        "carta_apresentacao": carta,
        "curriculo_estruturado": curriculo_estruturado
    }