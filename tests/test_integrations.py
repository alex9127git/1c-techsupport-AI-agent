import pytest

from app.providers.bitrix24 import Bitrix24Client
from app.providers.redmine import RedmineClient
from app.repositories import ChannelRepository, SupportRequestRepository
from app.schemas.chat import ChatResponse
from app.schemas.common import ResultStatus
from app.schemas.integrations import BitrixConnectIn, RedmineConnectIn
from app.services.integrations import IntegrationsService


class FakeAgent:
    def __init__(self, answer: str = "Ответ ассистента", status: ResultStatus = ResultStatus.OK):
        self.calls: list[str] = []
        self.answer = answer
        self.status = status

    def answer_question(self, request, channel="chat"):
        self.calls.append(f"{channel}:{request.message}")
        return ChatResponse(answer=self.answer, confidence=95, escalated=False, status=self.status)


class RecordingSession:
    """Подставная requests.Session, которая записывает вызовы вместо сети."""

    def __init__(self):
        self.calls: list[tuple[str, str, dict]] = []

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url, json or {}))
        return _FakeResponse({"result": {"id": 1}})

    def put(self, url, json=None, headers=None, timeout=None):
        self.calls.append(("PUT", url, json or {}))
        return _FakeResponse({"issue": {"id": 1}})


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.fixture()
def service(app):
    from app.routes import get_container

    with app.app_context():
        container = get_container()
        session = container._new_session()
        agent = FakeAgent()
        srv = IntegrationsService(
            channel_repo=ChannelRepository(session),
            agent_service=agent,
        )
        return srv, session, agent


def test_list_channels_empty(service):
    srv, _, _ = service
    out = srv.list_channels()
    assert len(out.channels) == 2
    assert [c.channel for c in out.channels] == ["bitrix", "redmine"]
    assert all(c.enabled is False for c in out.channels)


def test_connect_bitrix_stores_config(service):
    srv, session, _ = service
    result = srv.connect_bitrix(BitrixConnectIn(webhook_url="https://portal.bitrix24.ru/rest/1/abc/", chat_id="5"))
    assert result.status == ResultStatus.OK
    out = srv.list_channels()
    bitrix = next(c for c in out.channels if c.channel == "bitrix")
    assert bitrix.enabled is True
    assert srv._channels.config("bitrix")["webhook_url"].startswith("https://portal.bitrix24.ru/rest/1/abc/")
    assert srv._channels.config("bitrix")["chat_id"] == "5"


def test_connect_redmine_stores_config(service):
    srv, _, _ = service
    result = srv.connect_redmine(RedmineConnectIn(url="https://redmine.example", api_key="k123", project_id="p1"))
    assert result.status == ResultStatus.OK
    redmine = next(c for c in srv.list_channels().channels if c.channel == "redmine")
    assert redmine.enabled is True
    assert srv._channels.config("redmine") == {
        "base_url": "https://redmine.example",
        "api_key": "k123",
        "project_id": "p1",
    }


def test_connect_bitrix_invalid_url_rejected(service):
    srv, _, _ = service
    result = srv.connect_bitrix(BitrixConnectIn(webhook_url="", chat_id=None))
    assert result.status == ResultStatus.ERROR


def test_process_bitrix_sends_answer(service):
    srv, _, agent = service
    srv.connect_bitrix(BitrixConnectIn(webhook_url="https://p.bitrix24.ru/rest/1/tok/", chat_id=None))
    session = RecordingSession()
    client = Bitrix24Client("https://p.bitrix24.ru/rest/1/tok/", session=session)

    def factory(config):
        return client

    srv._bitrix_factory = factory

    payload = {
        "event": "ONIMBOTV2MESSAGEADD",
        "data": {
            "bot": {"id": 42, "code": "support_bot"},
            "message": {"text": "как обновить 1С?", "id": 1},
            "chat": {"dialogId": "chat5", "id": 5},
            "user": {"id": 9, "name": "Иван"},
        },
    }
    result = srv.process_bitrix(payload)
    assert result["accepted"] is True
    assert agent.calls == ["bitrix:как обновить 1С?"]
    assert result["answer"] == "Ответ ассистента"
    assert session.calls and session.calls[0][1].endswith("/chat.message.add")


def test_process_bitrix_channel_disabled(service):
    srv, _, _ = service
    result = srv.process_bitrix({"data": {"message": {"text": "x"}, "chat": {"dialogId": "1"}}})
    assert result == {"accepted": False, "reason": "channel_disabled"}


def test_process_bitrix_empty_message(service):
    srv, _, _ = service
    srv.connect_bitrix(BitrixConnectIn(webhook_url="https://p.bitrix24.ru/rest/1/tok/", chat_id=None))
    result = srv.process_bitrix({"data": {"message": {"text": ""}, "chat": {"dialogId": "1"}}})
    assert result == {"accepted": False, "reason": "empty_message"}


def test_process_redmine_adds_comment(service, app):
    srv, _, _ = service
    srv.connect_redmine(RedmineConnectIn(url="https://rm.example", api_key="k", project_id="p"))
    session = RecordingSession()
    client = RedmineClient("https://rm.example", "k", session=session)
    srv._redmine_factory = lambda config: client

    payload = {
        "payload": {
            "action": "opened",
            "url": "https://rm.example/issues/191",
            "issue": {"id": 191, "subject": "Сломался отчёт", "description": "Не выводит данные"},
        }
    }
    result = srv.process_redmine(payload)
    assert result["accepted"] is True
    assert result["issue_id"] == 191
    assert session.calls and session.calls[0][1].endswith("/issues/191.json")
    assert session.calls[0][2] == {"issue": {"notes": "Ответ ассистента"}}


def test_process_redmine_parse_plain(service):
    parsed = RedmineClient.parse_payload({"issue": {"id": 7, "subject": "Тема", "description": "Описание"}})
    assert parsed["issue_id"] == 7
    assert parsed["subject"] == "Тема"


def test_bitrix_parse_v1_format():
    payload = {
        "event": "ONIMBOTMESSAGEADD",
        "data": {
            "BOT": {"567": {"BOT_ID": "567", "BOT_CODE": "BOT1"}},
            "PARAMS": {"MESSAGE": "Привет", "DIALOG_ID": "27"},
            "USER": {"ID": "27", "NAME": "Иван"},
        },
    }
    parsed = Bitrix24Client.parse_payload(payload)
    assert parsed["message"] == "Привет"
    assert parsed["dialog_id"] == "27"
    assert parsed["bot_id"] == "567"


def test_disconnect_disables_channel(service):
    srv, _, _ = service
    srv.connect_redmine(RedmineConnectIn(url="https://rm.example", api_key="k", project_id="p"))
    result = srv.disconnect("redmine")
    assert result.status == ResultStatus.OK
    redmine = next(c for c in srv.list_channels().channels if c.channel == "redmine")
    assert redmine.enabled is False


def test_connect_endpoints(client):
    resp = client.post(
        "/api/integrations/bitrix/webhook",
        json={"webhook_url": "https://p.bitrix24.ru/rest/1/tok/", "chat_id": "10"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    data = resp.get_json()["data"]
    assert data["status"] == "ok"


def test_redmine_receive_endpoint_when_disabled(client):
    resp = client.post("/api/integrations/redmine/receive", json={"issue": {"id": 5, "subject": "x"}})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    data = resp.get_json()["data"]
    assert data["accepted"] is False
    assert data["reason"] == "channel_disabled"


def test_redmine_connect_endpoint(client):
    resp = client.post(
        "/api/integrations/redmine/webhook",
        json={"url": "https://rm.example", "api_key": "k", "project_id": "p"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_list_endpoint_after_connect(client):
    client.post(
        "/api/integrations/bitrix/webhook",
        json={"webhook_url": "https://p.bitrix24.ru/rest/1/tok/", "chat_id": "10"},
    )
    resp = client.get("/api/integrations")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    bitrix = next(c for c in data["channels"] if c["channel"] == "bitrix")
    assert bitrix["enabled"] is True