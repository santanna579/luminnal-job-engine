from typing import List, Dict
import json
from sqlalchemy.orm import Session
from app.models import CandidateProfileModel
from app.models_job import JobPostingModel
from app.models_match import JobMatchModel
from app.models_generated import GeneratedContentModel
from datetime import datetime

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

def salvar_perfil_candidato_db(db: Session, perfil: Dict) -> Dict:
    perfil_existente = db.query(CandidateProfileModel).first()

    skills_json = json.dumps(perfil["skills"], ensure_ascii=False)

    if perfil_existente:
        perfil_existente.nome = perfil["nome"]
        perfil_existente.cargo_atual = perfil["cargo_atual"]
        perfil_existente.anos_experiencia = perfil["anos_experiencia"]
        perfil_existente.skills = skills_json
        perfil_existente.nivel_ingles = perfil["nivel_ingles"]
        perfil_existente.objetivo = perfil["objetivo"]
        db.commit()
        db.refresh(perfil_existente)
        return {
            "nome": perfil_existente.nome,
            "cargo_atual": perfil_existente.cargo_atual,
            "anos_experiencia": perfil_existente.anos_experiencia,
            "skills": json.loads(perfil_existente.skills),
            "nivel_ingles": perfil_existente.nivel_ingles,
            "objetivo": perfil_existente.objetivo,
        }

    novo_perfil = CandidateProfileModel(
        nome=perfil["nome"],
        cargo_atual=perfil["cargo_atual"],
        anos_experiencia=perfil["anos_experiencia"],
        skills=skills_json,
        nivel_ingles=perfil["nivel_ingles"],
        objetivo=perfil["objetivo"],
    )

    db.add(novo_perfil)
    db.commit()
    db.refresh(novo_perfil)

    return {
        "nome": novo_perfil.nome,
        "cargo_atual": novo_perfil.cargo_atual,
        "anos_experiencia": novo_perfil.anos_experiencia,
        "skills": json.loads(novo_perfil.skills),
        "nivel_ingles": novo_perfil.nivel_ingles,
        "objetivo": novo_perfil.objetivo,
    }


def obter_perfil_candidato_db(db: Session) -> Dict | None:
    perfil = db.query(CandidateProfileModel).first()

    if not perfil:
        return None

    return {
        "nome": perfil.nome,
        "cargo_atual": perfil.cargo_atual,
        "anos_experiencia": perfil.anos_experiencia,
        "skills": json.loads(perfil.skills),
        "nivel_ingles": perfil.nivel_ingles,
        "objetivo": perfil.objetivo,
    }

def salvar_vaga_db(db: Session, vaga: Dict) -> Dict:
    from app.core.dependencies import get_current_user_id

    nova_vaga = JobPostingModel(
        created_by_user_id=get_current_user_id(),
        titulo=vaga["titulo"],
        empresa=vaga["empresa"],
        localizacao=vaga.get("localizacao"),
        origem=vaga.get("origem", "linkedin"),
        url=vaga.get("url"),
        descricao=vaga["descricao"],
    )

    db.add(nova_vaga)
    db.commit()
    db.refresh(nova_vaga)

    return {
        "id": nova_vaga.id,
        "titulo": nova_vaga.titulo,
        "empresa": nova_vaga.empresa,
        "localizacao": nova_vaga.localizacao,
        "origem": nova_vaga.origem,
        "url": nova_vaga.url,
        "descricao": nova_vaga.descricao,
        "criado_em": nova_vaga.criado_em,
    }


def listar_vagas_db(db: Session) -> List[Dict]:
    vagas = db.query(JobPostingModel).order_by(JobPostingModel.id.desc()).all()

    return [
        {
            "id": vaga.id,
            "titulo": vaga.titulo,
            "empresa": vaga.empresa,
            "localizacao": vaga.localizacao,
            "origem": vaga.origem,
            "url": vaga.url,
            "descricao": vaga.descricao,
            "criado_em": vaga.criado_em,
        }
        for vaga in vagas
    ]


def obter_vaga_db(db: Session, vaga_id: int) -> Dict | None:
    vaga = db.query(JobPostingModel).filter(JobPostingModel.id == vaga_id).first()

    if not vaga:
        return None

    return {
        "id": vaga.id,
        "titulo": vaga.titulo,
        "empresa": vaga.empresa,
        "localizacao": vaga.localizacao,
        "origem": vaga.origem,
        "url": vaga.url,
        "descricao": vaga.descricao,
        "criado_em": vaga.criado_em,
    }

def salvar_job_match_db(db: Session, vaga_id: int, nome_candidato: str, resultado: Dict) -> Dict:
    novo_match = JobMatchModel(
        vaga_id=vaga_id,
        nome_candidato=nome_candidato,
        score=resultado["score"],
        score_skills=resultado["score_skills"],
        score_senioridade=resultado["score_senioridade"],
        score_ingles=resultado["score_ingles"],
        nivel_aderencia=resultado["nivel_aderencia"],
        palavras_chave_encontradas=json.dumps(
            resultado["palavras_chave_encontradas"],
            ensure_ascii=False
        ),
        skills_nao_relevantes=json.dumps(
            resultado["skills_do_candidato_nao_relevantes_para_esta_vaga"],
            ensure_ascii=False
        ),
        exigencias_nao_cobertas=json.dumps(
            resultado["exigencias_da_vaga_nao_cobertas"],
            ensure_ascii=False
        ),
        recomendacao=resultado["recomendacao"],
        resumo_analitico=resultado["resumo_analitico"],
    )

    db.add(novo_match)
    db.commit()
    db.refresh(novo_match)

    return {
        "id": novo_match.id,
        "vaga_id": novo_match.vaga_id,
        "nome_candidato": novo_match.nome_candidato,
        "score": novo_match.score,
        "score_skills": novo_match.score_skills,
        "score_senioridade": novo_match.score_senioridade,
        "score_ingles": novo_match.score_ingles,
        "nivel_aderencia": novo_match.nivel_aderencia,
        "palavras_chave_encontradas": json.loads(novo_match.palavras_chave_encontradas) if novo_match.palavras_chave_encontradas else [],
        "skills_do_candidato_nao_relevantes_para_esta_vaga": json.loads(novo_match.skills_nao_relevantes) if novo_match.skills_nao_relevantes else [],
        "exigencias_da_vaga_nao_cobertas": json.loads(novo_match.exigencias_nao_cobertas) if novo_match.exigencias_nao_cobertas else [],
        "recomendacao": novo_match.recomendacao,
        "resumo_analitico": novo_match.resumo_analitico,
        "criado_em": novo_match.criado_em,
    }


def listar_job_matches_db(db: Session) -> List[Dict]:
    matches = db.query(JobMatchModel).order_by(JobMatchModel.id.desc()).all()

    return [
        {
            "id": match.id,
            "vaga_id": match.vaga_id,
            "nome_candidato": match.nome_candidato,
            "score": match.score,
            "score_skills": match.score_skills,
            "score_senioridade": match.score_senioridade,
            "score_ingles": match.score_ingles,
            "nivel_aderencia": match.nivel_aderencia,
            "palavras_chave_encontradas": json.loads(match.palavras_chave_encontradas) if match.palavras_chave_encontradas else [],
            "skills_do_candidato_nao_relevantes_para_esta_vaga": json.loads(match.skills_nao_relevantes) if match.skills_nao_relevantes else [],
            "exigencias_da_vaga_nao_cobertas": json.loads(match.exigencias_nao_cobertas) if match.exigencias_nao_cobertas else [],
            "recomendacao": match.recomendacao,
            "resumo_analitico": match.resumo_analitico,
            "criado_em": match.criado_em,
        }
        for match in matches
    ]

def recomendar_vagas_para_perfil(db: Session, perfil: Dict) -> List[Dict]:
    vagas = db.query(JobPostingModel).order_by(JobPostingModel.id.desc()).all()

    recomendacoes = []

    for vaga in vagas:
        resultado = analisar_com_perfil(
            vaga.descricao,
            perfil["skills"],
            perfil["nivel_ingles"],
            perfil["anos_experiencia"]
        )

        recomendacoes.append({
            "vaga_id": vaga.id,
            "titulo": vaga.titulo,
            "empresa": vaga.empresa,
            "localizacao": vaga.localizacao,
            "origem": vaga.origem,
            "url": vaga.url,
            "score": resultado["score"],
            "nivel_aderencia": resultado["nivel_aderencia"],
            "recomendacao": resultado["recomendacao"],
            "resumo_analitico": resultado["resumo_analitico"],
        })

    recomendacoes.sort(key=lambda x: x["score"], reverse=True)

    return recomendacoes

def salvar_perfil_candidato_raw_db(db: Session, perfil: Dict) -> Dict:
    perfil_existente = db.query(CandidateProfileModel).first()

    skills_json = json.dumps(perfil["skills"], ensure_ascii=False)

    if perfil_existente:
        perfil_existente.nome = perfil["nome"]
        perfil_existente.cargo_atual = perfil["cargo_atual"]
        perfil_existente.anos_experiencia = perfil["anos_experiencia"]
        perfil_existente.skills = skills_json
        perfil_existente.nivel_ingles = perfil["nivel_ingles"]
        perfil_existente.objetivo = perfil["objetivo"]
        perfil_existente.raw_resume_text = perfil.get("raw_resume_text")
        perfil_existente.profile_json = perfil.get("profile_json")
        perfil_existente.profile_summary = perfil.get("profile_summary")

        db.commit()
        db.refresh(perfil_existente)

        return {
            "nome": perfil_existente.nome,
            "cargo_atual": perfil_existente.cargo_atual,
            "anos_experiencia": perfil_existente.anos_experiencia,
            "skills": json.loads(perfil_existente.skills),
            "nivel_ingles": perfil_existente.nivel_ingles,
            "objetivo": perfil_existente.objetivo,
            "raw_resume_text": perfil_existente.raw_resume_text,
            "profile_json": perfil_existente.profile_json,
            "profile_summary": perfil_existente.profile_summary,
        }

    novo_perfil = CandidateProfileModel(
        nome=perfil["nome"],
        cargo_atual=perfil["cargo_atual"],
        anos_experiencia=perfil["anos_experiencia"],
        skills=skills_json,
        nivel_ingles=perfil["nivel_ingles"],
        objetivo=perfil["objetivo"],
        raw_resume_text=perfil.get("raw_resume_text"),
        profile_json=perfil.get("profile_json"),
        profile_summary=perfil.get("profile_summary"),
    )

    db.add(novo_perfil)
    db.commit()
    db.refresh(novo_perfil)

    return {
        "nome": novo_perfil.nome,
        "cargo_atual": novo_perfil.cargo_atual,
        "anos_experiencia": novo_perfil.anos_experiencia,
        "skills": json.loads(novo_perfil.skills),
        "nivel_ingles": novo_perfil.nivel_ingles,
        "objetivo": novo_perfil.objetivo,
        "raw_resume_text": novo_perfil.raw_resume_text,
        "profile_json": novo_perfil.profile_json,
        "profile_summary": novo_perfil.profile_summary,
    }


def obter_perfil_candidato_raw_db(db: Session) -> Dict | None:
    perfil = db.query(CandidateProfileModel).first()

    if not perfil:
        return None

    return {
        "nome": perfil.nome,
        "cargo_atual": perfil.cargo_atual,
        "anos_experiencia": perfil.anos_experiencia,
        "skills": json.loads(perfil.skills),
        "nivel_ingles": perfil.nivel_ingles,
        "objetivo": perfil.objetivo,
        "raw_resume_text": perfil.raw_resume_text,
        "profile_json": perfil.profile_json,
        "profile_summary": perfil.profile_summary,
    }


def salvar_vaga_raw_db(db: Session, vaga: Dict) -> Dict:
    from app.core.dependencies import get_current_user_id

    nova_vaga = JobPostingModel(
        created_by_user_id=get_current_user_id(),
        titulo=vaga["titulo"],
        empresa=vaga["empresa"],
        localizacao=vaga.get("localizacao"),
        origem=vaga.get("origem", "linkedin"),
        url=vaga.get("url"),
        descricao=vaga["descricao"],
        raw_description=vaga.get("raw_description"),
        job_json=vaga.get("job_json"),
        job_summary=vaga.get("job_summary"),
    )

    db.add(nova_vaga)
    db.commit()
    db.refresh(nova_vaga)

    return {
        "id": nova_vaga.id,
        "titulo": nova_vaga.titulo,
        "empresa": nova_vaga.empresa,
        "localizacao": nova_vaga.localizacao,
        "origem": nova_vaga.origem,
        "url": nova_vaga.url,
        "descricao": nova_vaga.descricao,
        "raw_description": nova_vaga.raw_description,
        "job_json": nova_vaga.job_json,
        "job_summary": nova_vaga.job_summary,
        "criado_em": nova_vaga.criado_em,
    }


def obter_vaga_raw_db(db: Session, vaga_id: int) -> Dict | None:
    vaga = db.query(JobPostingModel).filter(JobPostingModel.id == vaga_id).first()

    if not vaga:
        return None

    return {
        "id": vaga.id,
        "titulo": vaga.titulo,
        "empresa": vaga.empresa,
        "localizacao": vaga.localizacao,
        "origem": vaga.origem,
        "url": vaga.url,
        "descricao": vaga.descricao,
        "raw_description": vaga.raw_description,
        "job_json": vaga.job_json,
        "job_summary": vaga.job_summary,
        "criado_em": vaga.criado_em,
    }

def processar_perfil_raw_db(db: Session) -> Dict | None:
    from app.ai.resume_parser import parse_resume_with_ai

    perfil = db.query(CandidateProfileModel).first()

    if not perfil or not perfil.raw_resume_text:
        return None

    resultado = parse_resume_with_ai(perfil.raw_resume_text)

    perfil.profile_json = json.dumps(resultado["profile_json"], ensure_ascii=False)
    perfil.profile_summary = resultado["profile_summary"]
    perfil.last_ai_processed_at = datetime.utcnow()

    db.commit()
    db.refresh(perfil)

    return {
        "nome": perfil.nome,
        "cargo_atual": perfil.cargo_atual,
        "anos_experiencia": perfil.anos_experiencia,
        "skills": json.loads(perfil.skills),
        "nivel_ingles": perfil.nivel_ingles,
        "objetivo": perfil.objetivo,
        "raw_resume_text": perfil.raw_resume_text,
        "profile_json": json.loads(perfil.profile_json) if perfil.profile_json else None,
        "profile_summary": perfil.profile_summary,
    }


def processar_vaga_raw_db(db: Session, vaga_id: int) -> Dict | None:
    from app.ai.job_parser import parse_job_with_ai
    from datetime import datetime

    vaga = db.query(JobPostingModel).filter(JobPostingModel.id == vaga_id).first()

    if not vaga:
        return None

    texto_base = vaga.raw_description or vaga.descricao

    if not texto_base:
        return None

    resultado = parse_job_with_ai(texto_base)

    vaga.raw_description = texto_base
    vaga.job_json = json.dumps(resultado["job_json"], ensure_ascii=False)
    vaga.job_summary = resultado["job_summary"]
    vaga.last_ai_processed_at = datetime.utcnow()

    db.commit()
    db.refresh(vaga)

    return {
        "id": vaga.id,
        "titulo": vaga.titulo,
        "empresa": vaga.empresa,
        "localizacao": vaga.localizacao,
        "origem": vaga.origem,
        "url": vaga.url,
        "descricao": vaga.descricao,
        "raw_description": vaga.raw_description,
        "job_json": json.loads(vaga.job_json) if vaga.job_json else None,
        "job_summary": vaga.job_summary,
        "criado_em": vaga.criado_em,
    }

def processar_match_semantico_db(db: Session, vaga_id: int) -> Dict | None:
    from app.ai.match_engine import semantic_match_with_ai

    perfil = db.query(CandidateProfileModel).first()
    vaga = db.query(JobPostingModel).filter(JobPostingModel.id == vaga_id).first()

    if not perfil or not vaga:
        return None

    if not perfil.profile_json or not vaga.job_json:
        return None

    profile_data = json.loads(perfil.profile_json)
    job_data = json.loads(vaga.job_json)

    resultado = semantic_match_with_ai(profile_data, job_data)

    if job_data.get("ingles_exigido", False):
        nivel_ingles = (perfil.nivel_ingles or "").lower()
        resultado["ingles_compativel"] = nivel_ingles in [
            "intermediario",
            "intermediário",
            "avancado",
            "avançado",
            "fluente"
        ]

        if resultado["ingles_compativel"]:
            resultado["score"] = min(resultado["score"], 80) if resultado["score"] < 80 else resultado["score"]
        else:
            resultado["recomendacao"] = "Compatibilidade reduzida por exigência de inglês"

    return resultado

def gerar_resumo_adaptado_db(db: Session, vaga_id: int) -> Dict | None:
    from app.ai.resume_generator import gerar_resumo_e_carta
    from app.ai.match_engine import semantic_match_with_ai
    import json

    perfil = db.query(CandidateProfileModel).first()
    vaga = db.query(JobPostingModel).filter(JobPostingModel.id == vaga_id).first()

    if not perfil or not vaga:
        return None

    if not perfil.profile_json or not vaga.job_json:
        return None

    profile_data = json.loads(perfil.profile_json)
    job_data = json.loads(vaga.job_json)

    match = semantic_match_with_ai(profile_data, job_data)

    resultado = gerar_resumo_e_carta(
        profile=perfil.__dict__,
        job=vaga.__dict__,
        match=match
    )

    return resultado

def gerar_pdf_curriculo_db(db: Session, vaga_id: int) -> str | None:
    from app.ai.resume_generator import gerar_resumo_e_carta
    from app.ai.match_engine import semantic_match_with_ai
    from app.utils.pdf_generator import gerar_pdf_curriculo
    import json
    import os

    perfil = db.query(CandidateProfileModel).first()
    vaga = db.query(JobPostingModel).filter(JobPostingModel.id == vaga_id).first()

    if not perfil or not vaga:
        return None

    if not perfil.profile_json or not vaga.job_json:
        return None

    profile_data = json.loads(perfil.profile_json)
    job_data = json.loads(vaga.job_json)

    match = semantic_match_with_ai(profile_data, job_data)

    resultado = gerar_resumo_e_carta(
        profile=perfil.__dict__,
        job=vaga.__dict__,
        match=match
    )

    curriculo = resultado["curriculo_estruturado"]

    os.makedirs("generated_files", exist_ok=True)
    file_path = f"generated_files/curriculo_vaga_{vaga_id}.pdf"

    gerar_pdf_curriculo(curriculo, file_path)

    return file_path

def gerar_e_salvar_conteudo_db(db: Session, vaga_id: int) -> Dict | None:
    resultado = gerar_resumo_adaptado_db(db, vaga_id)

    if not resultado:
        return None

    perfil = db.query(CandidateProfileModel).first()

    if not perfil:
        return None

    novo_conteudo = GeneratedContentModel(
        vaga_id=vaga_id,
        nome_candidato=perfil.nome,
        resumo_profissional_adaptado=resultado["resumo_profissional_adaptado"],
        carta_apresentacao=resultado["carta_apresentacao"],
    )

    db.add(novo_conteudo)
    db.commit()
    db.refresh(novo_conteudo)

    return {
        "id": novo_conteudo.id,
        "vaga_id": novo_conteudo.vaga_id,
        "nome_candidato": novo_conteudo.nome_candidato,
        "resumo_profissional_adaptado": novo_conteudo.resumo_profissional_adaptado,
        "carta_apresentacao": novo_conteudo.carta_apresentacao,
        "criado_em": novo_conteudo.criado_em,
    }


def listar_conteudos_gerados_db(db: Session) -> List[Dict]:
    conteudos = db.query(GeneratedContentModel).order_by(GeneratedContentModel.id.desc()).all()

    return [
        {
            "id": item.id,
            "vaga_id": item.vaga_id,
            "nome_candidato": item.nome_candidato,
            "resumo_profissional_adaptado": item.resumo_profissional_adaptado,
            "carta_apresentacao": item.carta_apresentacao,
            "criado_em": item.criado_em,
        }
        for item in conteudos
    ]

def gerar_job_feed_db(db: Session) -> List[Dict]:
    from app.ai.match_engine import semantic_match_with_ai
    from app.services.dashboard_service import get_hot_score_map
    import json

    perfil = db.query(CandidateProfileModel).first()

    if not perfil or not perfil.profile_json:
        return []

    profile_data = json.loads(perfil.profile_json)
    vagas = db.query(JobPostingModel).all()
    hot_score_map = get_hot_score_map(db)

    resultado = []

    for vaga in vagas:
        if not vaga.job_json:
            continue

        job_data = json.loads(vaga.job_json)
        match = semantic_match_with_ai(profile_data, job_data)

        hot_score = hot_score_map.get(vaga.id, 0)

        resultado.append({
            "vaga_id": vaga.id,
            "titulo": vaga.titulo,
            "empresa": vaga.empresa,
            "localizacao": vaga.localizacao,
            "score": match.get("score", 0),
            "nivel_aderencia": match.get("recomendacao", ""),
            "resumo_match": match.get("resumo_match_semantico", ""),
            "hot_score": hot_score,
            "is_hot": hot_score >= 70,
        })

    resultado.sort(
        key=lambda x: (
            x["hot_score"],
            x["score"],
        ),
        reverse=True
    )

    return resultado