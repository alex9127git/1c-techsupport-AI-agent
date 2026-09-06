from app.schemas.kb import (
    KbCreateOut,
    KbDocumentIn,
    KbDocumentOut,
    KbListOut,
    KbMutateOut,
)
from app.schemas.common import ResultStatus


class KnowledgeBaseService:
    """Управление базой знаний.

    TODO(Фаза 4): реальный CRUD через KnowledgeRepository + RAG-индексация.
    На 0-й фазе отдаёт валидные контракты со статусом NOT_IMPLEMENTED.
    """

    def __init__(self, repository=None) -> None:
        self._repo = repository

    def list_documents(self) -> KbListOut:
        return KbListOut(items=[], total=0)

    def get_document(self, doc_id: int) -> KbDocumentOut:
        return KbDocumentOut(id=doc_id, status=ResultStatus.NOT_IMPLEMENTED)

    def create_document(self, data: KbDocumentIn) -> KbCreateOut:
        return KbCreateOut(accepted=True, status=ResultStatus.NOT_IMPLEMENTED)

    def update_document(self, doc_id: int, data: KbDocumentIn) -> KbMutateOut:
        return KbMutateOut(ok=True, status=ResultStatus.NOT_IMPLEMENTED)

    def delete_document(self, doc_id: int) -> KbMutateOut:
        return KbMutateOut(ok=True, status=ResultStatus.NOT_IMPLEMENTED)
