from pydantic import BaseModel, Field

from app.schemas.common import ResultStatus


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str = ""
    confidence: int = Field(default=0, ge=0, le=100)
    escalated: bool = False
    escalation_id: int | None = None
    status: ResultStatus = ResultStatus.NOT_IMPLEMENTED


class ImageResponse(BaseModel):
    accepted: bool = True
    analysis: str | None = None
    status: ResultStatus = ResultStatus.NOT_IMPLEMENTED
