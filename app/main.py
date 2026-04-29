from fastapi import FastAPI, HTTPException, Depends, Response, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db

from app.models_application_history import ApplicationStatusHistoryModel

from app.models import Base
from app.models_application import ApplicationModel
from app.models_application_history import ApplicationStatusHistoryModel

from app.core.config import settings

from datetime import datetime

from app.models_application import ApplicationModel
from app.models_application_history import ApplicationStatusHistoryModel

from app.services_old import (
    analisar_vaga_texto,
    analisar_com_perfil,
    salvar_perfil_candidato_db,
    obter_perfil_candidato_db,
    salvar_vaga_db,
    listar_vagas_db,
    obter_vaga_db,
    salvar_job_match_db,
    listar_job_matches_db,
    recomendar_vagas_para_perfil,
    salvar_perfil_candidato_raw_db,
    obter_perfil_candidato_raw_db,
    salvar_vaga_raw_db,
    obter_vaga_raw_db,
    processar_perfil_raw_db,
    processar_vaga_raw_db,
    processar_match_semantico_db,
    gerar_resumo_adaptado_db,
    gerar_pdf_curriculo_db,
    gerar_e_salvar_conteudo_db,
    listar_conteudos_gerados_db
)

from app.services.applications_service import (
    create_application_db,
    list_applications_db,
    update_application_status_db,
    delete_application_db,
)

from app.schemas_old import (
    JobInput,
    JobAnalysisResponse,
    JobWithProfileInput,
    CandidateProfile,
    JobCreate,
    JobResponse,
    JobMatchResponse,
    RecommendedJobResponse,
    CandidateProfileRawInput,
    CandidateProfileRawResponse,
    JobRawInput,
    JobRawResponse,
    CandidateProfileProcessedResponse,
    JobProcessedResponse,
    SemanticMatchResponse,
    ResumeAdaptadoResponse,
    GeneratedContentResponse
)

from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)

from app.api import profile_resume
from app.api.match import router as match_router

from app.services.dashboard_service import (
    get_dashboard_metrics_db,
    get_hot_jobs_ranked_db,
    get_follow_up_suggestions_db,
    get_funnel_analytics_db,
)

from app.core.dependencies import get_current_user_id
from app.api.jobs import router as jobs_router
from app.services.job_service import list_jobs_catalog_db

app = FastAPI(
    title=settings.app_name,
    description="API inicial do motor de vagas da Luminnal",
    version=settings.app_version,
)

app.include_router(match_router)
app.include_router(jobs_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://jadix.luminnal.com.br",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_resume.router)


Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def read_root():
    return {"message": "Luminnal Job Engine no ar"}


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


@app.post("/perfil-candidato/raw", response_model=CandidateProfileRawResponse)
def criar_perfil_candidato_raw(perfil: CandidateProfileRawInput, db: Session = Depends(get_db)):
    return salvar_perfil_candidato_raw_db(db, perfil.model_dump())


@app.get("/perfil-candidato/raw", response_model=CandidateProfileRawResponse)
def consultar_perfil_candidato_raw(db: Session = Depends(get_db)):
    perfil = obter_perfil_candidato_raw_db(db)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil do candidato não cadastrado")
    return perfil


@app.post("/vaga/raw", response_model=JobRawResponse)
def criar_vaga_raw(vaga: JobRawInput, db: Session = Depends(get_db)):
    return salvar_vaga_raw_db(db, vaga.model_dump())


@app.get("/vaga/{vaga_id}", response_model=JobRawResponse)
def consultar_vaga_raw(vaga_id: int, db: Session = Depends(get_db)):
    vaga = obter_vaga_raw_db(db, vaga_id)
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return vaga


@app.post("/perfil-candidato/processar-raw", response_model=CandidateProfileProcessedResponse)
def processar_perfil_candidato_raw(db: Session = Depends(get_db)):
    perfil = processar_perfil_raw_db(db)

    if not perfil:
        raise HTTPException(
            status_code=404,
            detail="Perfil do candidato com raw_resume_text não encontrado"
        )

    return perfil


@app.post("/vaga/processar-raw/{vaga_id}", response_model=JobProcessedResponse)
def processar_vaga_raw(vaga_id: int, db: Session = Depends(get_db)):
    vaga = processar_vaga_raw_db(db, vaga_id)

    if not vaga:
        raise HTTPException(
            status_code=404,
            detail="Vaga com descrição bruta não encontrada"
        )

    return vaga


@app.post("/match-semantico/{vaga_id}", response_model=SemanticMatchResponse)
def match_semantico(vaga_id: int, db: Session = Depends(get_db)):
    resultado = processar_match_semantico_db(db, vaga_id)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Perfil processado ou vaga processada não encontrados"
        )

    return resultado


@app.post("/gerar-resumo-adaptado/{vaga_id}", response_model=ResumeAdaptadoResponse)
def gerar_resumo_adaptado(vaga_id: int, db: Session = Depends(get_db)):
    resultado = gerar_resumo_adaptado_db(db, vaga_id)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Dados insuficientes para gerar resumo adaptado"
        )

    return resultado


@app.get("/gerar-curriculo-pdf/{vaga_id}")
def gerar_curriculo_pdf(vaga_id: int, db: Session = Depends(get_db)):
    file_path = gerar_pdf_curriculo_db(db, vaga_id)

    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="Dados insuficientes para gerar currículo em PDF"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"curriculo_vaga_{vaga_id}.pdf"
    )


@app.post("/gerar-e-salvar-conteudo/{vaga_id}", response_model=GeneratedContentResponse)
def gerar_e_salvar_conteudo(vaga_id: int, db: Session = Depends(get_db)):
    resultado = gerar_e_salvar_conteudo_db(db, vaga_id)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Dados insuficientes para gerar e salvar conteúdo"
        )

    return resultado


@app.get("/conteudos-gerados", response_model=list[GeneratedContentResponse])
def listar_conteudos_gerados(db: Session = Depends(get_db)):
    return listar_conteudos_gerados_db(db)


@app.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    application = create_application_db(db, payload.model_dump())

    if not application:
        raise HTTPException(
            status_code=409,
            detail="Esta vaga já foi salva nas candidaturas."
        )

    return application


@app.get("/applications")
def list_applications(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return list_applications_db(db, user_id=user_id)


@app.patch("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)):
    application = update_application_status_db(
        db=db,
        application_id=application_id,
        status=payload.status
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Candidatura não encontrada."
        )

    return application


@app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    deleted = delete_application_db(db, application_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Candidatura não encontrada."
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/applications/{application_id}/history")
def get_application_history(application_id: int, db: Session = Depends(get_db)):
    history = (
        db.query(ApplicationStatusHistoryModel)
        .filter(ApplicationStatusHistoryModel.application_id == application_id)
        .order_by(ApplicationStatusHistoryModel.changed_at.asc())
        .all()
    )

    return [
        {
            "from_status": item.from_status,
            "to_status": item.to_status,
            "changed_at": item.changed_at,
        }
        for item in history
    ]

@app.get("/applications/summary")
def get_applications_summary(db: Session = Depends(get_db)):
    applications = (
        db.query(ApplicationModel)
        .filter(ApplicationModel.user_id == 1)
        .all()
    )

    now = datetime.utcnow()
    result = []

    for app in applications:
        last_history = (
            db.query(ApplicationStatusHistoryModel)
            .filter(ApplicationStatusHistoryModel.application_id == app.id)
            .order_by(ApplicationStatusHistoryModel.changed_at.desc())
            .first()
        )

        reference_date = (
            last_history.changed_at
            if last_history and last_history.changed_at
            else app.created_at
        )

        days_without_update = 0
        if reference_date:
            days_without_update = (now - reference_date).days

        needs_action = (
            app.status in ["saved", "applied"]
            and days_without_update >= 3
        )

        is_hot = app.status in ["recruiter_contact", "interview_process", "offer"]

        result.append({
            "job_id": app.job_id,
            "status": app.status,
            "is_hot": is_hot,
            "needs_action": needs_action,
            "days_without_update": days_without_update,
        })

    return result

@app.get("/dashboard/metrics")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_dashboard_metrics_db(db=db, user_id=user_id)

@app.get("/dashboard/hot-jobs")
def get_dashboard_hot_jobs(
    limit: int = 5,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_hot_jobs_ranked_db(db=db, user_id=user_id, limit=limit)

@app.get("/dashboard/follow-ups")
def get_dashboard_follow_ups(
    limit: int = 5,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_follow_up_suggestions_db(db=db, user_id=user_id, limit=limit)

@app.get("/dashboard/funnel-analytics")
def get_dashboard_funnel_analytics(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return get_funnel_analytics_db(db=db, user_id=user_id)


# @app.post("/jobs/import")
# def import_jobs(
#     jobs: List[JobCreate],
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_current_user_id),
# ):
#     result = create_jobs_bulk_db(db=db, jobs=jobs, user_id=user_id)
# 
#     return {
#         "total_imported": len(result)
#     }

@app.get("/job-feed", response_model=list[JobResponse])
def job_feed(
    db: Session = Depends(get_db),
):
    return list_jobs_catalog_db(db=db)

#@app.post("/jobs/{job_id}/apply")
#def apply_to_job(
#    job_id: int,
#    db: Session = Depends(get_db),
#    user_id: int = Depends(get_current_user_id),
#):
#    result = apply_to_job_db(
#        db=db,
#        job_id=job_id,
#        user_id=user_id,
#    )
#
#    if not result:
#        return {"error": "Vaga não encontrada"}
#
#    return {
#        "application_id": result.id,
#        "status": result.status,
#    }