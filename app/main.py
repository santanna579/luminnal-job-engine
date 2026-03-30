from fastapi import FastAPI, HTTPException
from app.schemas import JobInput, JobAnalysisResponse, JobWithProfileInput, CandidateProfile
from app.services import (
    analisar_vaga_texto,
    analisar_com_perfil,
    salvar_perfil_candidato,
    obter_perfil_candidato
)

app = FastAPI(
    title="Luminnal Job Engine",
    description="API inicial do motor de vagas da Luminnal",
    version="0.1.0"
)


@app.get("/")
def read_root():
    return {"message": "Luminnal Job Engine no ar"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/perfil-candidato", response_model=CandidateProfile)
def criar_perfil_candidato(perfil: CandidateProfile):
    return salvar_perfil_candidato(perfil.model_dump())


@app.get("/perfil-candidato", response_model=CandidateProfile)
def consultar_perfil_candidato():
    perfil = obter_perfil_candidato()
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil do candidato não cadastrado")
    return perfil


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