import json

from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.common import ResultStatus
from app.schemas.kb import (
    KbCreateOut,
    KbDocumentIn,
    KbDocumentOut,
    KbListOut,
    KbMutateOut,
)


class KnowledgeBaseService:
    """Управление базой знаний: CRUD документов и RAG-индексация файлов."""

    def __init__(self, repository: KnowledgeRepository, indexer=None) -> None:
        self._repo = repository
        self._indexer = indexer

    def list_documents(self) -> KbListOut:
        docs = self._repo.list_all()
        items = [self._to_out(doc).model_dump() for doc in docs]
        return KbListOut(items=items, total=len(items))

    def get_document(self, doc_id: int) -> KbDocumentOut:
        doc = self._repo.get(doc_id)
        if doc is None:
            return KbDocumentOut(id=doc_id, status=ResultStatus.ERROR)
        return self._to_out(doc)

    def create_document(self, data: KbDocumentIn) -> KbCreateOut:
        doc = self._repo.create(data)
        return KbCreateOut(id=doc.id, accepted=True, status=ResultStatus.OK)

    def upload_file(self, filename: str, stream, title: str = "") -> KbCreateOut:
        """Сохраняет файл в docs_dir и индексирует его в векторное хранилище."""
        if self._indexer is None or self._indexer.docs_dir is None:
            return KbCreateOut(accepted=False, status=ResultStatus.NOT_CONFIGURED)
        if not filename or not _is_supported(filename):
            return KbCreateOut(accepted=False, status=ResultStatus.ERROR)

        docs_dir = self._indexer.docs_dir
        docs_dir.mkdir(parents=True, exist_ok=True)
        # Обезопасим имя: только имя файла, без путей.
        safe_name = _sanitize_name(filename)
        dest = docs_dir / safe_name

        if not safe_name or dest.exists():
            return KbCreateOut(accepted=False, status=ResultStatus.ERROR)

        dest.write_bytes(stream.read())

        written = self._indexer.index_document(str(dest))
        if written == 0:
            try:
                dest.unlink(missing_ok=True)
            except Exception:
                pass
            return KbCreateOut(accepted=False, status=ResultStatus.ERROR)

        data = KbDocumentIn(
            title=title or safe_name,
            content="",
            tags=[],
        )
        doc = self._repo.create(data, source_file=safe_name)
        return KbCreateOut(id=doc.id, accepted=True, status=ResultStatus.OK, indexed=True)

    def update_document(self, doc_id: int, data: KbDocumentIn) -> KbMutateOut:
        doc = self._repo.get(doc_id)
        if doc is None:
            return KbMutateOut(ok=False, status=ResultStatus.ERROR)
        self._repo.update(doc, data)
        return KbMutateOut(ok=True, status=ResultStatus.OK)

    def delete_document(self, doc_id: int) -> KbMutateOut:
        doc = self._repo.get(doc_id)
        if doc is None:
            return KbMutateOut(ok=False, status=ResultStatus.NOT_IMPLEMENTED)

        if doc.source_file and self._indexer is not None:
            try:
                self._indexer.unindex_document(str(self._indexer.docs_dir / doc.source_file))
            except Exception:
                pass
            try:
                (self._indexer.docs_dir / doc.source_file).unlink(missing_ok=True)
            except Exception:
                pass

        self._repo.delete(doc)
        return KbMutateOut(ok=True, status=ResultStatus.OK)

    def _to_out(self, doc) -> KbDocumentOut:
        try:
            tags: list[str] = json.loads(doc.tags or "[]")
        except Exception:
            tags = []
        return KbDocumentOut(
            id=doc.id,
            title=doc.title,
            content=doc.content,
            tags=tags,
            status=ResultStatus.OK,
            source_file=doc.source_file,
            indexed=bool(doc.source_file),
        )


def _is_supported(filename: str) -> bool:
    from rag.const import SUPPORTED_EXT

    import os

    return os.path.splitext(filename.lower())[1] in SUPPORTED_EXT


def _sanitize_name(filename: str) -> str:
    import os

    name = os.path.basename(filename.replace("\\", "/"))
    if not name or name in {".", ".."}:
        return ""
    # Отсекаем скрытые/резервные файлы ОС.
    if name.startswith(".") or name.endswith("~"):
        return ""
    import re

    return re.sub(r"[^\w.\- ]", "_", name)