import os
import tempfile
import time

from app.providers.gigachat import GigaChatProvider, NotConfiguredError
from app.schemas.chat import ChatRequest, ChatResponse, ImageResponse, ResultStatus

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
MAX_IMAGE_MB = 15


class AgentService:
    """Сервис AI-агента.

    Оркестрирует ответ на вопрос пользователя: вызовы ядра (GigaChat + RAG),
    оценка уверенности, эскалация при низкой уверенности и запись метрик.
    """

    def __init__(
        self,
        provider: GigaChatProvider,
        settings_service,
        escalation_service,
        support_repo,
    ) -> None:
        self._provider = provider
        self._settings = settings_service
        self._escalations = escalation_service
        self._support = support_repo

    def answer_question(self, request: ChatRequest, channel: str = "chat") -> ChatResponse:
        if not self._provider.configured:
            return ChatResponse(
                answer=self._provider.status_text(),
                confidence=0,
                escalated=False,
                status=ResultStatus.NOT_CONFIGURED,
            )

        history = [{"role": m.role, "content": m.content} for m in request.history]

        started = time.perf_counter()
        try:
            result = self._provider.answer(request.message, history)
        except NotConfiguredError:
            return ChatResponse(status=ResultStatus.NOT_CONFIGURED)
        except Exception as exc:  # сеть, таймаут, парсинг — не роняем запрос
            return ChatResponse(
                answer=f"Ошибка при обращении к модели: {exc}",
                confidence=0,
                escalated=False,
                status=ResultStatus.ERROR,
            )
        response_ms = int((time.perf_counter() - started) * 1000)

        threshold = self._settings.get_threshold()
        confidence = result.confidence if result.confidence is not None else 0
        escalated = confidence < threshold
        escalation_id = None
        if escalated:
            escalation_id = self._escalations.escalate(request.message, result.answer, confidence)

        self._support.create(
            channel=channel,
            payload={
                "question": request.message,
                "answer": result.answer,
                "confidence": confidence,
                "sources": result.sources,
                "history": len(history),
            },
            status="escalated" if escalated else "answered",
            response_ms=response_ms,
        )

        return ChatResponse(
            answer=result.answer,
            confidence=confidence,
            escalated=escalated,
            escalation_id=escalation_id,
            sources=result.sources,
            status=ResultStatus.OK,
        )

    def analyze_image(self, file_storage, message: str | None = None) -> ImageResponse:
        filename = (file_storage.filename or "").lower()
        ext = os.path.splitext(filename)[1]
        if ext not in IMAGE_EXTENSIONS:
            return ImageResponse(
                accepted=False,
                analysis=None,
                error=f"Расширение '{ext or '—'}' не поддерживается. Разрешены: png, jpg, jpeg, tiff, bmp",
                status=ResultStatus.ERROR,
            )

        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell() if hasattr(file_storage.stream, "tell") else -1
        file_storage.stream.seek(0)
        if size > MAX_IMAGE_MB * 1024 * 1024:
            return ImageResponse(
                accepted=False,
                analysis=None,
                error=f"Размер изображения превышает {MAX_IMAGE_MB} МБ",
                status=ResultStatus.ERROR,
            )

        if not self._provider.configured:
            return ImageResponse(
                accepted=False, analysis=None, status=ResultStatus.NOT_CONFIGURED
            )

        prompt = (message or "").strip() or (
            "Опиши, что изображено на скриншоте, и подскажи, как пользователю "
            "техподдержки 1С устранить ошибку или разобраться в интерфейсе."
        )

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=ext, delete=False
            ) as tmp:
                tmp.write(file_storage.stream.read())
                tmp_path = tmp.name

            analysis = self._provider.analyze_image(prompt, tmp_path)
            if not analysis:
                return ImageResponse(
                    accepted=True, analysis=None, error="Модель не вернула текст анализа", status=ResultStatus.ERROR
                )
            return ImageResponse(accepted=True, analysis=analysis, status=ResultStatus.OK)
        except NotConfiguredError:
            return ImageResponse(
                accepted=False, analysis=None, status=ResultStatus.NOT_CONFIGURED
            )
        except Exception as exc:
            return ImageResponse(
                accepted=False,
                analysis=None,
                error=f"Ошибка анализа изображения: {exc}",
                status=ResultStatus.ERROR,
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass