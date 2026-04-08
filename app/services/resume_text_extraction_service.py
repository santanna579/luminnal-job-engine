import pdfplumber
from docx import Document
import tempfile


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    with pdfplumber.open(tmp_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    text = ""

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    doc = Document(tmp_path)

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return text.strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    filename = filename.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    if filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    raise ValueError("Formato de arquivo não suportado")