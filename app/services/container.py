from flask import Flask

from app.db import get_database, get_session
from app.repositories import KnowledgeRepository, SettingsRepository
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
        return AgentService()

    def knowledge_service(self) -> KnowledgeBaseService:
        return KnowledgeBaseService(KnowledgeRepository(self._new_session()))

    def metrics_service(self) -> MetricsService:
        return MetricsService()

    def escalation_service(self) -> EscalationService:
        return EscalationService()

    def _new_session(self):
        return get_database().session()
