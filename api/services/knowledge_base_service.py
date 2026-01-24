"""Knowledge base helpers for file management."""

from pathlib import Path
from typing import List, Dict, Any

from database import get_db_connection
from knowledge_base import ingest_user_file, remove_file_from_kb


UPLOAD_ROOT = Path("./data/uploads")


def save_user_document(user_id: str, filename: str, file_path: str, file_type: str, file_size: int, chunk_count: int) -> int:
    """Record a user document in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_documents (user_id, filename, file_path, file_type, file_size, chunk_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, filename, file_path, file_type, file_size, chunk_count),
        )
        return cursor.lastrowid


def list_user_documents(user_id: str) -> List[Dict[str, Any]]:
    """List documents uploaded by a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT doc_id, filename, file_path, file_type, file_size, uploaded_at, chunk_count
            FROM user_documents
            WHERE user_id = ?
            ORDER BY uploaded_at DESC
            """,
            (user_id,),
        )
        documents = []
        for row in cursor.fetchall():
            documents.append(
                {
                    "doc_id": row[0],
                    "filename": row[1],
                    "file_path": row[2],
                    "file_type": row[3],
                    "file_size": row[4],
                    "uploaded_at": row[5],
                    "chunk_count": row[6],
                }
            )
        return documents


def delete_user_document(user_id: str, doc_id: int) -> bool:
    """Delete a user document and remove from vector store."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT filename, file_path
            FROM user_documents
            WHERE user_id = ? AND doc_id = ?
            """,
            (user_id, doc_id),
        )
        row = cursor.fetchone()
        if not row:
            return False

        filename, file_path = row[0], row[1]
        cursor.execute(
            "DELETE FROM user_documents WHERE user_id = ? AND doc_id = ?",
            (user_id, doc_id),
        )

    if filename:
        remove_file_from_kb(filename)
    if file_path:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    return True


def store_uploaded_file(user_id: str, filename: str, content: bytes) -> Path:
    """Persist uploaded file to disk under user folder."""
    user_dir = UPLOAD_ROOT / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    target_path = user_dir / filename
    target_path.write_bytes(content)
    return target_path


def ingest_file(file_path: Path) -> int:
    """Ingest file into knowledge base."""
    return ingest_user_file(str(file_path))
