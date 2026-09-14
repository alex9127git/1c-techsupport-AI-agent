from sqlalchemy import select, func
from sqlalchemy.orm import Session
import json

from app.models.knowledge import SupportRequest
from app.schemas.common import ResultStatus


class SupportRequestRepository:
    """Репозиторий запросов поддержки (метрики и логи)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, channel: str, payload: dict, status: str, response_ms: int | None) -> None:
        self._session.add(SupportRequest(
            channel=channel,
            payload=json.dumps(payload, ensure_ascii=False),
            status=status,
            response_ms=response_ms,
        ))
        self._session.commit()

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(SupportRequest)) or 0

    def count_status(self, status: str) -> int:
        return self._session.scalar(
            select(func.count()).select_from(SupportRequest).where(SupportRequest.status == status)
        ) or 0

    def avg_response_ms(self) -> float:
        return self._session.scalar(
            select(func.avg(SupportRequest.response_ms))
        ) or 0.0

    def list_recent(self, limit: int = 100) -> list[dict]:
        rows = self._session.scalars(
            select(SupportRequest).order_by(SupportRequest.id.desc()).limit(limit)
        ).all()
        items = []
        for r in rows:
            try:
                payload = json.loads(r.payload or "{}")
            except Exception:
                payload = {}
            items.append({
                "id": r.id,
                "channel": r.channel,
                "status": r.status,
                "response_ms": r.response_ms,
                "question": payload.get("question") or "",
                "answer": payload.get("answer") or "",
                "confidence": payload.get("confidence"),
                "sources": payload.get("sources") or [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return items