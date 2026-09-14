import pytest

from app.db import get_database
from app.providers.gigachat import AnswerResult, NotConfiguredError
from app.repositories import (
    EscalationRepository,
    SettingsRepository,
    SupportRequestRepository,
)
from app.schemas.chat import ChatRequest
from app.schemas.common import ResultStatus
from app.services import AgentService, EscalationService, SettingsService


class FakeProvider:
    configured = True

    def __init__(self, confidence=90, answer="Ответ из теста"):
        self.confidence = confidence
        self.answer_text = answer

    def answer(self, message, history=None):
        return AnswerResult(answer=self.answer_text, confidence=self.confidence)

    def status_text(self):
        return "AUTH_KEY не задан"


class NotConfiguredFakeProvider(FakeProvider):
    configured = False


def build_agent(app, provider):
    session = get_database().session()
    try:
        return AgentService(
            provider=provider,
            settings_service=SettingsService(SettingsRepository(session)),
            escalation_service=EscalationService(EscalationRepository(session)),
            support_repo=SupportRequestRepository(session),
        )
    finally:
        session.close()


def test_high_confidence_no_escalation(app):
    agent = build_agent(app, FakeProvider(confidence=90))
    resp = agent.answer_question(ChatRequest(message="как закрыть месяц?"))
    assert resp.status == ResultStatus.OK
    assert resp.answer == "Ответ из теста"
    assert resp.confidence == 90
    assert resp.escalated is False
    assert resp.escalation_id is None


def test_low_confidence_escalation(app):
    agent = build_agent(app, FakeProvider(confidence=30))
    resp = agent.answer_question(ChatRequest(message="что за ошибка 80040e14?"))
    assert resp.status == ResultStatus.OK
    assert resp.escalated is True
    assert resp.escalation_id is not None


def test_not_configured(app):
    agent = build_agent(app, NotConfiguredFakeProvider())
    resp = agent.answer_question(ChatRequest(message="привет"))
    assert resp.status == ResultStatus.NOT_CONFIGURED
    assert resp.escalated is False
    assert resp.escalation_id is None


def test_provider_error_returns_error_status(app):
    class ThrowingProvider(FakeProvider):
        def answer(self, message, history=None):
            raise RuntimeError("network down")

    agent = build_agent(app, ThrowingProvider())
    resp = agent.answer_question(ChatRequest(message="привет"))
    assert resp.status == ResultStatus.ERROR
    assert "Ошибка" in resp.answer


def test_metrics_after_requests(app):
    session = get_database().session()
    try:
        from app.services.metrics import MetricsService

        metrics = MetricsService(
            support_repo=SupportRequestRepository(session),
            escalation_repo=EscalationRepository(session),
        )
        before_dash = metrics.dashboard()

        low_agent = build_agent(app, FakeProvider(confidence=20))
        high_agent = build_agent(app, FakeProvider(confidence=95))
        low_agent.answer_question(ChatRequest(message="вопрос 1"))
        high_agent.answer_question(ChatRequest(message="вопрос 2"))

        dash = metrics.dashboard()
        assert dash.total_requests == before_dash.total_requests + 2
        assert dash.escalations == before_dash.escalations + 1
        assert metrics.logs().total == before_dash.total_requests + 2
        assert metrics.escalations().total == before_dash.escalations + 1
    finally:
        session.close()