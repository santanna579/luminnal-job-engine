from fastapi import APIRouter, UploadFile, File
from app.services.resume_text_extraction_service import extract_text

router = APIRouter()

@router.post("/profile/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        extracted_text = extract_text(file_bytes, file.filename)

        return {
            "filename": file.filename,
            "text_preview": extracted_text[:1000],  # preview só
            "full_text": extracted_text
        }

    except Exception as e:
        return {
            "error": str(e)
        }