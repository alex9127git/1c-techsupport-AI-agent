from flask import Flask

from app.db import get_database, get_session
from app.repositories import (
    EscalationRepository,
    KnowledgeRepository,
    SettingsRepository,
    SupportRequestRepository,
)
from app.services import (
    AgentService,
    EscalationService,
    KnowledgeBaseService,
    MetricsService,
    SettingsService,
)


class ServiceContainer:
    """Лёгкий контейнер зависимостей.

    Собирает репозитории и сервисы для каждого запроса (сессия БД живёт
    в рамках запроса). Заглушки при необходимости заменяются базовой
    реализацией без изменения маршрутов.
    """

    def __init__(self, app: Flask) -> None:
        self._app = app

    def session(self):
        return get_session()

    def settings_service(self) -> SettingsService:
        return SettingsService(SettingsRepository(self._new_session()))

    def agent_service(self) -> AgentService:
        return AgentService(
            provider=self.gigachat_provider(),
            settings_service=self.settings_service(),
            escalation_service=self.escalation_service(),
            support_repo=SupportRequestRepository(self._new_session()),
        )

    def knowledge_service(self) -> KnowledgeBaseService:
        return KnowledgeBaseService(
            repository=KnowledgeRepository(self._new_session()),
            indexer=self.gigachat_provider(),
        )

    def metrics_service(self) -> MetricsService:
        return MetricsService(
            support_repo=SupportRequestRepository(self._new_session()),
            escalation_repo=EscalationRepository(self._new_session()),
        )

    def escalation_service(self) -> EscalationService:
        return EscalationService(EscalationRepository(self._new_session()))

    def gigachat_provider(self):
        from app.providers.gigachat import GigaChatProvider

        if "gigachat" not in self._app.extensions:
            self._app.extensions["gigachat"] = GigaChatProvider(self._app)
        return self._app.extensions["gigachat"]

    def _new_session(self):
        return get_database().session()