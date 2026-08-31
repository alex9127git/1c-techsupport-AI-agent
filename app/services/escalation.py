from app.schemas.chat import ChatRequest
from app.schemas.common import ResultStatus


class EscalationService:
    """Создание и управление эскалациями.

    TODO(Фаза 1): при confidence < порога (SettingsService) создавать
    запись Escalation в БД. На 0-й фазе — валидные контракты-заглушки.
    """

    def escalate(self, request: ChatRequest, confidence: int) -> int | None:
        return None

    def notify(self, escalation_id: int) -> ResultStatus:
        return ResultStatus.NOT_IMPLEMENTED
