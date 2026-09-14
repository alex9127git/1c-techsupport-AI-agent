from app.repositories import EscalationRepository
from app.schemas.common import ResultStatus


class EscalationService:
    """Создание и управление эскалациями.

    Запись Escalation создаётся при ответе с низкой уверенностью
    (порог из SettingsService).
    """

    def __init__(self, repo: EscalationRepository) -> None:
        self._repo = repo

    def escalate(self, question: str, answer: str, confidence: int) -> int | None:
        return self._repo.create(question, answer, confidence)

    def notify(self, escalation_id: int) -> ResultStatus:
        # TODO(Фаза 4): уведомление оператора в интеграциях (Bitrix/Redmine).
        return ResultStatus.OK