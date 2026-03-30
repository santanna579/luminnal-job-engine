from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.models import Base
from app.services import (
    analisar_vaga_texto,
    analisar_com_perfil,
    salvar_perfil_candidato_db,
    obter_perfil_candidato_db,
    salvar_vaga_db,
    listar_vagas_db,
    obter_vaga_db,
    salvar_job_match_db,
    listar_job_matches_db,
    recomendar_vagas_para_perfil
)
from app.models_job import JobPostingModel
from app.models_match import JobMatchModel
from app.schemas import JobInput, JobAnalysisResponse, JobWithProfileInput, CandidateProfile, JobCreate, JobResponse, JobMatchResponse, RecommendedJobResponse


app = FastAPI(
    title="Luminnal Job Engine",
    description="API inicial do motor de vagas da Luminnal",
    version="0.1.0"
)

Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Luminnal Job Engine no ar"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/perfil-candidato", response_model=CandidateProfile)
def criar_perfil_candidato(perfil: CandidateProfile, db: Session = Depends(get_db)):
    return salvar_perfil_candidato_db(db, perfil.model_dump())


@app.get("/perfil-candidato", response_model=CandidateProfile)
def consultar_perfil_candidato(db: Session = Depends(get_db)):
    perfil = obter_perfil_candidato_db(db)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil do candidato não cadastrado")
    return perfil


@app.post("/analisar-vaga-usando-perfil-salvo", response_model=JobAnalysisResponse)
def analisar_vaga_usando_perfil_salvo(job: JobInput, db: Session = Depends(get_db)):
    perfil = obter_perfil_candidato_db(db)

    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil do candidato não cadastrado")

    resultado = analisar_com_perfil(
        job.descricao,
        perfil["skills"],
        perfil["nivel_ingles"],
        perfil["anos_experiencia"]
    )

    return resultado


@app.post("/analisar-vaga", response_model=JobAnalysisResponse)
def analisar_vaga(job: JobInput):
    resultado = analisar_vaga_texto(job.descricao)
    return resultado


@app.post("/analisar-vaga-com-perfil", response_model=JobAnalysisResponse)
def analisar_vaga_com_perfil(data: JobWithProfileInput):
    resultado = analisar_com_perfil(
        data.vaga.descricao,
        data.candidato.skills,
        data.candidato.nivel_ingles,
        data.candidato.anos_experiencia
    )
    return resultado

@app.post("/vaga", response_model=JobResponse)
def criar_vaga(vaga: JobCreate, db: Session = Depends(get_db)):
    return salvar_vaga_db(db, vaga.model_dump())


@app.get("/vagas", response_model=list[JobResponse])
def listar_vagas(db: Session = Depends(get_db)):
    return listar_vagas_db(db)


@app.post("/analisar-vaga-salva/{vaga_id}", response_model=JobAnalysisResponse)
def analisar_vaga_salva(vaga_id: int, db: Session = Depends(get_db)):
    perfil = obter_perfil_candidato_db(db)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil do candidato não cadastrado")

    vaga = obter_vaga_db(db, vaga_id)
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    resultado = analisar_com_perfil(
        vaga["descricao"],
        perfil["skills"],
        perfil["nivel_ingles"],
        perfil["anos_experiencia"]
    )

    salvar_job_match_db(
        db=db,
        vaga_id=vaga_id,
        nome_candidato=perfil["nome"],
        resultado=resultado
    )

    return resultado


@app.get("/job-matches", response_model=list[JobMatchResponse])
def listar_job_matches(db: Session = Depends(get_db)):
    return listar_job_matches_db(db)

@app.get("/vagas-recomendadas", response_model=list[RecommendedJobResponse])
def vagas_recomendadas(db: Session = Depends(get_db)):
    perfil = obter_perfil_candidato_db(db)

    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil do candidato não cadastrado")

    return recomendar_vagas_para_perfil(db, perfil)