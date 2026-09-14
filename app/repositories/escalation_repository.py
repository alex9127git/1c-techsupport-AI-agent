from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.knowledge import Escalation
from app.schemas.common import ResultStatus


class EscalationRepository:
    """Репозиторий эскалаций."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, question: str, answer: str, confidence: int) -> int:
        row = Escalation(question=question, answer=answer, confidence=confidence, status="open")
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return row.id

    def list_recent(self, limit: int = 100) -> list[dict]:
        rows = self._session.scalars(
            select(Escalation).order_by(Escalation.id.desc()).limit(limit)
        ).all()
        return [
            {
                "id": r.id,
                "question": r.question,
                "answer": r.answer,
                "confidence": r.confidence,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    def count_open(self) -> int:
        return self._session.scalar(
            select(func.count()).select_from(Escalation).where(Escalation.status == "open")
        ) or 0

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(Escalation)) or 0