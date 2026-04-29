from fastapi import APIRouter, HTTPException

from app.schemas.match import (
    MatchPreviewRequest,
    MatchPreviewResponse,
    MatchBatchRequest,
    MatchBatchResponse,
    MatchBatchItemResponse,
)
from app.services.match_engine import calculate_match

router = APIRouter(prefix="/match", tags=["Match"])


@router.post("/preview", response_model=MatchPreviewResponse)
def preview_match(payload: MatchPreviewRequest):
    try:
        result = calculate_match(payload.profile, payload.job)
        return MatchPreviewResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular match: {str(exc)}")


@router.post("/batch", response_model=MatchBatchResponse)
def batch_match(payload: MatchBatchRequest):
    try:
        items = []

        for job in payload.jobs:
            result = calculate_match(payload.profile, job)

            items.append(
                MatchBatchItemResponse(
                    job_id=job.id,
                    score=result["score"],
                    summary=result["summary"],
                    strengths=result["strengths"],
                    gaps=result["gaps"],
                    suggestions=result["suggestions"],
                    details=result["details"],
                )
            )

        return MatchBatchResponse(items=items)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular match em lote: {str(exc)}")