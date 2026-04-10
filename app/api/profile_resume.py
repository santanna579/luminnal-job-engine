from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader

from app.ai.resume_parser import parse_resume

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
        # 1) Lê os bytes reais do arquivo enviado
        file_bytes = await file.read()

        # 2) Extrai texto real do PDF
        extracted_text = extract_text_from_pdf_bytes(file_bytes)

        print("\n========== TEXTO EXTRAÍDO ==========")
        print(extracted_text[:3000])
        print("========== FIM TEXTO EXTRAÍDO ==========\n")
        print(f"Tamanho do texto extraído: {len(extracted_text)}")

        # 3) Impede parse com texto insuficiente
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível extrair texto suficiente do PDF. Verifique se o currículo contém texto selecionável."
            )

        # 4) Chama o parser com o texto extraído
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
        raise HTTPException(status_code=500, detail=f"Erro ao processar currículo: {str(e)}")