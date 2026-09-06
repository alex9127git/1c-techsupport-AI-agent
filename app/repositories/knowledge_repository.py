from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDocument
from app.schemas.kb import KbDocumentIn


class KnowledgeRepository:
    """Репозиторий документов базы знаний.

    Сервисы зависят только от методов этого класса, а не от конкретного
    движка БД — переход SQLite -> PostgreSQL не затрагивает бизнес-логику.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[KnowledgeDocument]:
        return list(self._session.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.id)).all())

    def get(self, doc_id: int) -> KnowledgeDocument | None:
        return self._session.get(KnowledgeDocument, doc_id)

    def create(self, data: KbDocumentIn) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            title=data.title, content=data.content, tags=_to_json(data.tags)
        )
        self._session.add(doc)
        self._session.commit()
        self._session.refresh(doc)
        return doc

    def update(self, doc: KnowledgeDocument, data: KbDocumentIn) -> KnowledgeDocument:
        doc.title = data.title
        doc.content = data.content
        doc.tags = _to_json(data.tags)
        self._session.commit()
        self._session.refresh(doc)
        return doc

    def delete(self, doc: KnowledgeDocument) -> None:
        self._session.delete(doc)
        self._session.commit()


def _to_json(tags: list[str]) -> str:
    import json

    return json.dumps(tags, ensure_ascii=False)
