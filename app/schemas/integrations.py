from pydantic import BaseModel

from app.schemas.common import ResultStatus


class ChannelOut(BaseModel):
    channel: str
    enabled: bool = False


class IntegrationsOut(BaseModel):
    channels: list[ChannelOut]


class BitrixConnectIn(BaseModel):
    webhook_url: str
    chat_id: str | None = None


class RedmineConnectIn(BaseModel):
    url: str
    api_key: str
    project_id: str | None = None


class ConnectOut(BaseModel):
    status: ResultStatus = ResultStatus.NOT_IMPLEMENTED
