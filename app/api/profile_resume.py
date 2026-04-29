from io import BytesIO
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.ai.resume_parser import parse_resume
from app.database import get_db
from app.models import UserProfileModel

router = APIRouter()


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages_text = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages_text.append(page_text)

    return "\n".join(pages_text).strip()


@router.post("/profile/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        extracted_text = extract_text_from_pdf_bytes(file_bytes)

        print("\n========== TEXTO EXTRAÍDO ==========")
        print(extracted_text[:3000])
        print("========== FIM TEXTO EXTRAÍDO ==========\n")
        print(f"Tamanho do texto extraído: {len(extracted_text)}")

        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível extrair texto suficiente do PDF. Verifique se o currículo contém texto selecionável."
            )

        structured_data = parse_resume(extracted_text)

        return {
            "success": True,
            "structured_data": structured_data.model_dump()
        }

    except HTTPException:
        raise

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar currículo: {str(e)}"
        )


@router.post("/profile/save")
def save_profile(data: dict, db: Session = Depends(get_db)):
    try:
        user_id = 1  # MVP sem autenticação por enquanto

        active_profile = (
            db.query(UserProfileModel)
            .filter(
                UserProfileModel.user_id == user_id,
                UserProfileModel.snapshot_type == "active"
            )
            .first()
        )

        if active_profile:
            db.query(UserProfileModel).filter(
                UserProfileModel.user_id == user_id,
                UserProfileModel.snapshot_type == "previous"
            ).delete()

            active_profile.snapshot_type = "previous"

        clean_data = {
            key: value
            for key, value in data.items()
            if key != "resume_filename"
        }

        new_profile = UserProfileModel(
            user_id=user_id,
            profile_json=json.dumps(clean_data),
            resume_filename=data.get("resume_filename"),
            snapshot_type="active"
        )

        db.add(new_profile)
        db.commit()

        return {"success": True}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile")
def get_profile(user_id: int = 1, db: Session = Depends(get_db)):
    try:
        profile = (
            db.query(UserProfileModel)
            .filter(
                UserProfileModel.user_id == user_id,
                UserProfileModel.snapshot_type == "active"
            )
            .first()
        )

        if not profile:
            return {"profile": None, "resume_filename": None}

        return {
            "profile": json.loads(profile.profile_json),
            "resume_filename": profile.resume_filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))