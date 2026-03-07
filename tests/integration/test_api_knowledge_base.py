"""
Knowledge base endpoint tests.

ingest_file (ChromaDB + embeddings) is mocked so no vector DB is needed.
store_uploaded_file writes a real temp file — that's intentional to verify
the upload path works end-to-end up to the ingestion step.
"""

import pytest


# ── Module-level mock: patch ingest_file for every test in this file ──────────

@pytest.fixture(autouse=True)
def mock_ingest(monkeypatch):
    """Patch ingest_file and remove_file_from_kb so no ChromaDB calls are made.

    Both must be patched at the call site (the module that imported them with
    `from X import Y`), not at the source module — Python's `from X import Y`
    creates a local binding that isn't affected by patching the source.
    """
    # ingest_file is called in api/routes/knowledge_base.py via `from ...service import ingest_file`
    monkeypatch.setattr(
        "api.routes.knowledge_base.ingest_file",
        lambda _path: 3,  # pretend 3 chunks were created
    )
    # remove_file_from_kb is called inside knowledge_base_service.delete_user_document
    # which imported it with `from knowledge_base import ..., remove_file_from_kb`
    monkeypatch.setattr(
        "api.services.knowledge_base_service.remove_file_from_kb",
        lambda _filename: None,
    )


# ── Upload tests ──────────────────────────────────────────────────────────────

class TestUpload:
    def test_upload_text_file_returns_200(self, funded_client):
        r = funded_client.post(
            "/api/kb/upload",
            files={"file": ("policy.txt", b"ServiceNow policy content here.", "text/plain")},
        )
        assert r.status_code == 200

    def test_upload_response_has_required_fields(self, funded_client):
        r = funded_client.post(
            "/api/kb/upload",
            files={"file": ("guide.txt", b"Some guide content.", "text/plain")},
        )
        data = r.json()
        assert "doc_id" in data
        assert "filename" in data
        assert "chunk_count" in data
        assert data["filename"] == "guide.txt"
        assert data["chunk_count"] == 3  # matches our mock

    def test_upload_assigns_unique_doc_ids(self, funded_client):
        r1 = funded_client.post(
            "/api/kb/upload",
            files={"file": ("file1.txt", b"Content one.", "text/plain")},
        )
        r2 = funded_client.post(
            "/api/kb/upload",
            files={"file": ("file2.txt", b"Content two.", "text/plain")},
        )
        assert r1.json()["doc_id"] != r2.json()["doc_id"]

    def test_upload_empty_file_rejected(self, funded_client):
        r = funded_client.post(
            "/api/kb/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert r.status_code == 400

    def test_upload_requires_auth(self, anon_client):
        r = anon_client.post(
            "/api/kb/upload",
            files={"file": ("secret.txt", b"Some content.", "text/plain")},
        )
        assert r.status_code in (401, 403)


# ── List tests ────────────────────────────────────────────────────────────────

class TestListFiles:
    def test_list_returns_200_and_array(self, funded_client):
        r = funded_client.get("/api/kb/files")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_uploaded_file_appears_in_list(self, funded_client):
        funded_client.post(
            "/api/kb/upload",
            files={"file": ("listed.txt", b"List me please.", "text/plain")},
        )
        files = funded_client.get("/api/kb/files").json()
        filenames = [f["filename"] for f in files]
        assert "listed.txt" in filenames

    def test_list_item_has_required_fields(self, funded_client):
        funded_client.post(
            "/api/kb/upload",
            files={"file": ("fields_check.txt", b"Check my fields.", "text/plain")},
        )
        files = funded_client.get("/api/kb/files").json()
        assert len(files) > 0
        item = files[0]
        assert "doc_id" in item
        assert "filename" in item
        assert "file_size" in item
        assert "chunk_count" in item
        assert "uploaded_at" in item

    def test_list_is_user_scoped(self, funded_client, superadmin_client):
        """Files uploaded by funded_client must not appear in superadmin's list."""
        funded_client.post(
            "/api/kb/upload",
            files={"file": ("user_private.txt", b"User-only content.", "text/plain")},
        )
        superadmin_files = superadmin_client.get("/api/kb/files").json()
        super_filenames = [f["filename"] for f in superadmin_files]
        assert "user_private.txt" not in super_filenames

    def test_list_requires_auth(self, anon_client):
        r = anon_client.get("/api/kb/files")
        assert r.status_code in (401, 403)


# ── Delete tests ──────────────────────────────────────────────────────────────

class TestDeleteFile:
    def test_delete_own_file_returns_200(self, funded_client):
        upload = funded_client.post(
            "/api/kb/upload",
            files={"file": ("to_delete.txt", b"Delete me.", "text/plain")},
        )
        doc_id = upload.json()["doc_id"]

        r = funded_client.delete(f"/api/kb/files/{doc_id}")
        assert r.status_code == 200

    def test_deleted_file_absent_from_list(self, funded_client):
        upload = funded_client.post(
            "/api/kb/upload",
            files={"file": ("gone.txt", b"I will be gone.", "text/plain")},
        )
        doc_id = upload.json()["doc_id"]
        funded_client.delete(f"/api/kb/files/{doc_id}")

        files = funded_client.get("/api/kb/files").json()
        remaining_ids = [f["doc_id"] for f in files]
        assert doc_id not in remaining_ids

    def test_delete_nonexistent_file_returns_404(self, funded_client):
        r = funded_client.delete("/api/kb/files/999999")
        assert r.status_code == 404

    def test_cannot_delete_another_users_file(self, funded_client, superadmin_client):
        """funded_client uploads a file; superadmin cannot delete it."""
        upload = funded_client.post(
            "/api/kb/upload",
            files={"file": ("protected.txt", b"Protected content.", "text/plain")},
        )
        doc_id = upload.json()["doc_id"]

        r = superadmin_client.delete(f"/api/kb/files/{doc_id}")
        assert r.status_code == 404  # scoped by user_id — returns 404, not 403

    def test_delete_requires_auth(self, anon_client):
        r = anon_client.delete("/api/kb/files/1")
        assert r.status_code in (401, 403)
