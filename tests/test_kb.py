from io import BytesIO
from pathlib import Path

import pytest

from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.knowledge import KnowledgeBaseService
from app.schemas.common import ResultStatus


class FakeIndexer:
    def __init__(self, docs_dir: Path) -> None:
        self.docs_dir = docs_dir
        self.indexed: list[str] = []
        self.unindexed: list[str] = []

    def index_document(self, path: str) -> int:
        self.indexed.append(str(path))
        return 3

    def unindex_document(self, path: str) -> None:
        self.unindexed.append(str(path))


@pytest.fixture()
def kb_service(app, tmp_path):
    docs_dir = tmp_path / "docs"
    indexer = FakeIndexer(docs_dir)
    from app.routes import get_container

    with app.app_context():
        container = get_container()
        session = container._new_session()
        service = KnowledgeBaseService(
            repository=KnowledgeRepository(session), indexer=indexer
        )
        return service, docs_dir


def test_upload_md_indexes_and_creates_row(kb_service):
    service, docs_dir = kb_service
    stream = BytesIO("# Заголовок\n\nТекст документа по 1С.".encode("utf-8"))
    result = service.upload_file("doc1.md", stream)
    assert result.accepted is True
    assert result.status == ResultStatus.OK
    assert result.indexed is True
    assert service.list_documents().total == 1

    posted = service.list_documents().items[0]
    assert posted["source_file"] == "doc1.md"
    assert posted["indexed"] is True
    assert (docs_dir / "doc1.md").exists()
    assert service._indexer.indexed == [str(docs_dir / "doc1.md")]


def test_upload_unsupported_extension_rejected(kb_service):
    service, _ = kb_service
    stream = BytesIO(b"evil")
    result = service.upload_file("malware.exe", stream)
    assert result.accepted is False
    assert result.status == ResultStatus.ERROR
    assert service.list_documents().total == 0


def test_upload_missing_indexer_returns_not_configured(app):
    from app.routes import get_container

    with app.app_context():
        container = get_container()
        session = container._new_session()
        service = KnowledgeBaseService(
            repository=KnowledgeRepository(session), indexer=None
        )
        stream = BytesIO("текст".encode("utf-8"))
        result = service.upload_file("doc.md", stream)
        assert result.accepted is False
        assert result.status == ResultStatus.NOT_CONFIGURED


def test_delete_document_unindexes_and_removes_file(kb_service):
    service, docs_dir = kb_service
    stream = BytesIO("# Doc\n\nТекст.".encode("utf-8"))
    created = service.upload_file("gone.md", stream)
    assert created.accepted is True

    result = service.delete_document(created.id)
    assert result.ok is True
    assert service.list_documents().total == 0
    assert not (docs_dir / "gone.md").exists()
    assert service._indexer.unindexed == [str(docs_dir / "gone.md")]


def test_kb_crud_roundtrip(app):
    from app.routes import get_container
    from app.schemas.kb import KbDocumentIn

    with app.app_context():
        container = get_container()
        session = container._new_session()
        service = KnowledgeBaseService(repository=KnowledgeRepository(session))

        created = service.create_document(
            KbDocumentIn(title="Ручной документ", content="текст", tags=["1с"])
        )
        assert created.accepted is True
        assert created.status == ResultStatus.OK

        out = service.get_document(created.id)
        assert out.title == "Ручной документ"
        assert out.status == ResultStatus.OK
        assert out.tags == ["1с"]

        updated = service.update_document(
            created.id, KbDocumentIn(title="Иной", content="x")
        )
        assert updated.ok is True
        assert service.get_document(created.id).title == "Иной"

        deleted = service.delete_document(created.id)
        assert deleted.ok is True
        assert service.get_document(created.id).status == ResultStatus.ERROR


def test_upload_endpoint(app, client, tmp_path):
    from app.routes import get_container

    docs_dir = tmp_path / "docs"
    indexer = FakeIndexer(docs_dir)
    with app.app_context():
        container = get_container()

        def fake_service():
            session = container._new_session()
            return KnowledgeBaseService(
                repository=KnowledgeRepository(session), indexer=indexer
            )

        container.knowledge_service = fake_service

        resp = client.post(
            "/api/kb/upload",
            data={
                "file": (BytesIO("текст".encode("utf-8")), "doc.md")
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["ok"] is True
        data = payload["data"]
        assert data["accepted"] is True
        assert data["status"] == "ok"
        assert data["indexed"] is True


def test_upload_endpoint_missing_file(client):
    resp = client.post("/api/kb/upload", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False