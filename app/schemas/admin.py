from pydantic import BaseModel

from app.schemas.common import ResultStatus


class DashboardOut(BaseModel):
    total_requests: int = 0
    success_rate: float = 0.0
    avg_response_ms: int = 0
    escalations: int = 0


class SettingsOut(BaseModel):
    confidence_threshold: int
    escalation_strategy: str


class SettingsIn(BaseModel):
    confidence_threshold: int | None = None
    escalation_strategy: str | None = None


class EscalationOut(BaseModel):
    id: int | None = None
    question: str = ""
    answer: str = ""
    confidence: int = 0
    status: str = ""


class EscalationsOut(BaseModel):
    items: list[dict] = []
    total: int = 0


class LogsOut(BaseModel):
    items: list[dict] = []
    total: int = 0


class MutateOut(BaseModel):
    ok: bool = True
    status: ResultStatus = ResultStatus.OK
