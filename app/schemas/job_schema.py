from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    titulo: str
    empresa: str
    descricao: str
    localizacao: Optional[str] = None
    origem: Optional[str] = "linkedin"
    url: Optional[str] = None
    raw_description: Optional[str] = None
    job_json: Optional[str] = None
    job_summary: Optional[str] = None


class JobCatalogItemResponse(BaseModel):
    id: int
    titulo: str
    empresa: str
    descricao: str
    localizacao: Optional[str] = None
    origem: str
    url: Optional[str] = None
    criado_em: datetime
    created_by_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class JobImportResponse(BaseModel):
    created_count: int
    skipped_count: int


class JobApplyResponse(BaseModel):
    application_id: int
    status: str
    already_exists: bool