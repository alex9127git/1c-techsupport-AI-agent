from app.providers.bitrix24 import Bitrix24Client
from app.providers.redmine import RedmineClient
from app.repositories.channels_repository import ChannelRepository
from app.schemas.chat import ChatRequest
from app.schemas.common import ResultStatus
from app.schemas.integrations import (
    BitrixConnectIn,
    ChannelOut,
    ConnectOut,
    IntegrationsOut,
    RedmineConnectIn,
)

CHANNEL_BITRIX = "bitrix"
CHANNEL_REDMINE = "redmine"


class IntegrationsService:
    """Настройка и приём вебхуков внешних каналов (Bitrix24, Redmine).

    Каналы хранятся в таблице channels (JSON-конфиг). При получении события
    вопрос прогоняется через AgentService (тот же RAG-пайплайн и эскалация),
    ответ отправляется обратно в исходный канал.
    """

    def __init__(
        self,
        channel_repo: ChannelRepository,
        agent_service,
        bitrix_client_factory=None,
        redmine_client_factory=None,
    ) -> None:
        self._channels = channel_repo
        self._agent = agent_service
        self._bitrix_factory = bitrix_client_factory or self._default_bitrix
        self._redmine_factory = redmine_client_factory or self._default_redmine

    # --- чтение/запись конфигурации --------------------------------------

    def list_channels(self) -> IntegrationsOut:
        rows = {row.name: row.enabled for row in self._channels.list_all()}
        order = [CHANNEL_BITRIX, CHANNEL_REDMINE]
        channels = [
            ChannelOut(channel=name, enabled=bool(rows.get(name)))
            for name in order
        ]
        return IntegrationsOut(channels=channels)

    def connect_bitrix(self, data: BitrixConnectIn) -> ConnectOut:
        config = {
            "webhook_url": Bitrix24Client.normalize_webhook_url(data.webhook_url),
            "chat_id": data.chat_id,
        }
        if not config["webhook_url"]:
            return ConnectOut(status=ResultStatus.ERROR)
        self._channels.upsert(CHANNEL_BITRIX, config, enabled=True)
        return ConnectOut(status=ResultStatus.OK)

    def connect_redmine(self, data: RedmineConnectIn) -> ConnectOut:
        config = {
            "base_url": (data.url or "").rstrip("/"),
            "api_key": data.api_key,
            "project_id": data.project_id,
        }
        if not config["base_url"] or not config["api_key"]:
            return ConnectOut(status=ResultStatus.ERROR)
        self._channels.upsert(CHANNEL_REDMINE, config, enabled=True)
        return ConnectOut(status=ResultStatus.OK)

    def disconnect(self, channel: str) -> ConnectOut:
        self._channels.set_enabled(channel, enabled=False)
        return ConnectOut(status=ResultStatus.OK)

    # --- обработка входящих вебхуков -------------------------------------

    def process_bitrix(self, payload: dict) -> dict:
        parsed = Bitrix24Client.parse_payload(payload)
        message = parsed["message"]
        if not message:
            return {"accepted": False, "reason": "empty_message"}
        dialog_id = parsed["dialog_id"]
        if not dialog_id:
            return {"accepted": False, "reason": "empty_dialog"}

        channel = self._channels.get(CHANNEL_BITRIX)
        if channel is None or not channel.enabled:
            return {"accepted": False, "reason": "channel_disabled"}
        config = _channel_config(channel)

        response = self._agent.answer_question(ChatRequest(message=message))
        if response.status != ResultStatus.OK:
            return {"accepted": False, "reason": response.status.value}

        client = self._bitrix_factory(config)
        client.send_message(dialog_id, response.answer)
        return {
            "accepted": True,
            "question": message,
            "answer": response.answer,
            "confidence": response.confidence,
            "dialog_id": dialog_id,
        }

    def process_redmine(self, payload: dict) -> dict:
        parsed = RedmineClient.parse_payload(payload)
        issue_id = parsed["issue_id"]
        subject = parsed["subject"]
        description = parsed["description"]
        if issue_id is None:
            return {"accepted": False, "reason": "no_issue_id"}
        if not subject and not description:
            return {"accepted": False, "reason": "empty_issue"}

        channel = self._channels.get(CHANNEL_REDMINE)
        if channel is None or not channel.enabled:
            return {"accepted": False, "reason": "channel_disabled"}
        config = _channel_config(channel)

        question = f"{subject}\n\n{description}".strip()
        response = self._agent.answer_question(ChatRequest(message=question))
        if response.status != ResultStatus.OK:
            return {"accepted": False, "reason": response.status.value}

        client = self._redmine_factory(config)
        client.add_comment(issue_id, response.answer)
        return {
            "accepted": True,
            "issue_id": issue_id,
            "answer": response.answer,
            "confidence": response.confidence,
        }

    # --- фабрики клиентов --------------------------------------------------

    def _default_bitrix(self, config: dict) -> Bitrix24Client:
        return Bitrix24Client(webhook_url=config.get("webhook_url", ""))

    def _default_redmine(self, config: dict) -> RedmineClient:
        return RedmineClient(
            base_url=config.get("base_url", ""),
            api_key=config.get("api_key", ""),
        )


def _channel_config(channel) -> dict:
    import json

    try:
        return json.loads(channel.config or "{}")
    except Exception:
        return {}