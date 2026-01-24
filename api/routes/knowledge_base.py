"""Knowledge base endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.dependencies import get_current_user
from api.models.knowledge_base import FileInfo, UploadResponse
from api.services.knowledge_base_service import (
    ingest_file,
    list_user_documents,
    save_user_document,
    store_uploaded_file,
    delete_user_document,
)


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
) -> UploadResponse:
    """Upload and ingest a file into the knowledge base."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name required")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    stored_path = store_uploaded_file(current_user["user_id"], file.filename, content)
    chunk_count = ingest_file(stored_path)

    doc_id = save_user_document(
        user_id=current_user["user_id"],
        filename=file.filename,
        file_path=str(stored_path),
        file_type=file.content_type,
        file_size=len(content),
        chunk_count=chunk_count,
    )

    return UploadResponse(doc_id=doc_id, filename=file.filename, chunk_count=chunk_count)


@router.get("/files", response_model=list[FileInfo])
def list_files(current_user: dict = Depends(get_current_user)) -> list[FileInfo]:
    """List user files."""
    files = list_user_documents(current_user["user_id"])
    return [FileInfo(**file_info) for file_info in files]


@router.delete("/files/{doc_id}")
def delete_file(doc_id: int, current_user: dict = Depends(get_current_user)) -> dict:
    """Delete a file."""
    if not delete_user_document(current_user["user_id"], doc_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return {"status": "ok"}
