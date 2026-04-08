from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/profile/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "message": "Upload recebido com sucesso"
    }