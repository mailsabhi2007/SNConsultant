"""Knowledge base request/response models."""

from typing import Optional

from pydantic import BaseModel


class FileInfo(BaseModel):
    doc_id: int
    filename: str
    file_type: Optional[str] = None
    file_size: int
    uploaded_at: str
    chunk_count: int


class UploadResponse(BaseModel):
    doc_id: int
    filename: str
    chunk_count: int
