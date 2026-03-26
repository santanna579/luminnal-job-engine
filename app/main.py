from fastapi import FastAPI
from app.schemas import JobInput, JobAnalysisResponse
from app.services import analisar_vaga_texto

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


@app.post("/analisar-vaga", response_model=JobAnalysisResponse)
def analisar_vaga(job: JobInput):
    resultado = analisar_vaga_texto(job.descricao)
    return resultado