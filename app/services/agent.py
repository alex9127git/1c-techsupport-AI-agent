from app.schemas.chat import ChatRequest, ChatResponse, ImageResponse, ResultStatus


class AgentService:
    """Сервис AI-агента.

    TODO(Фаза 1): подключить реальное ядро (app.providers.gigachat) поверх
    api/client.py.response_pipeline. До подключения возвращает валидный
    контракт с честным статусом NOT_IMPLEMENTED.
    """

    def answer_question(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            answer="",
            confidence=0,
            escalated=False,
            status=ResultStatus.NOT_IMPLEMENTED,
        )

    def analyze_image(self, message: str | None = None) -> ImageResponse:
        return ImageResponse(accepted=True, analysis=None, status=ResultStatus.NOT_IMPLEMENTED)
