from __future__ import annotations

from dataclasses import dataclass, field
from flask import Flask


@dataclass
class AnswerResult:
    answer: str
    confidence: int | None = None
    sources: list[str] = field(default_factory=list)


class NotConfiguredError(RuntimeError):
    """Ядро не настроено: отсутствует AUTH_KEY."""


class GigaChatProvider:
    """Адаптер между Flask-сервисами и CLI-ядром (api/client.py + rag).

    Тяжёлые ресурсы (эмбеддинг-модель, клиент GigaChat) создаются один раз
    и переживают все запросы. Ядро импортируется лениво: приложение стартует
    даже без установленного sentence-transformers, пока не вызван answer().
    Хранится в app.extensions["gigachat"] и разделяется между запросами.
    """

    def __init__(self, app: Flask) -> None:
        self._app = app
        self._client = None
        self._index = None

    @property
    def configured(self) -> bool:
        return bool(self.auth_key)

    @property
    def auth_key(self) -> str | None:
        return self._app.config.get("AUTH_KEY")

    def _ensure_ready(self):
        if not self.configured:
            raise NotConfiguredError("AUTH_KEY не задан в config/.env")
        if self._client is not None:
            return
        from api.client import ApiClient
        from rag.vectoring import VectorIndex

        self._index = self.ensure_index()
        self._client = ApiClient(self.auth_key, self._index)

    def ensure_index(self):
        """Возвращает VectorIndex, создавая его при первом обращении.

        Требует только эмбеддинг-модель (без AUTH_KEY), поэтому загрузка
        документов в базу знаний работает даже без ключа GigaChat.
        """
        if self._index is not None:
            return self._index
        from rag.const import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL
        from rag.vectoring import VectorIndex

        self._index = VectorIndex(CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL)
        return self._index

    @property
    def docs_dir(self):
        from pathlib import Path

        base = Path(self._app.config.get("DOCS_DIR", "data/docs"))
        if not base.is_absolute():
            base = self._app.root_path.parent / base
        return base

    def index_document(self, path: str) -> int:
        """Извлекает текст из файла и добавляет чанки в векторный индекс.

        Возвращает количество записанных векторов; при ошибке парсинга — 0.
        """
        from rag.chunking import extract_and_chunk
        from rag.database import init_state_db, upsert_row
        from rag.fileutils import file_hash
        from pathlib import Path

        result = extract_and_chunk(path)
        if result["error"] or not result["chunks"]:
            return 0

        index = self.ensure_index()
        written = index.add_chunks(result["doc_id"], str(path), result["chunks"])

        conn = init_state_db()
        p = Path(path)
        stat = p.stat()
        upsert_row(conn, str(p), file_hash(p), stat.st_size, stat.st_mtime, result["doc_id"])
        return written

    def unindex_document(self, path: str) -> None:
        """Удаляет чанки документа из векторного индекса и state-базы."""
        from rag.fileutils import make_doc_id

        index = self.ensure_index()
        doc_id = make_doc_id(str(path))
        try:
            index.delete_doc(doc_id)
        except Exception:
            pass
        from rag.database import delete_row, init_state_db

        conn = init_state_db()
        delete_row(conn, str(path))

    def answer(self, message: str, history: list[dict[str, str]] | None = None) -> AnswerResult:
        """Возвращает ответ GigaChat с опорой на RAG-контекст и уверенность."""
        self._ensure_ready()
        if history is None:
            history = []
        context, answer, confidence = self._client.generate_answer(message, history)
        result = AnswerResult(answer=answer, confidence=confidence)
        if self._index is not None:
            searched = self._index.search(message, k=3)
            result.sources = [item["text"] for item in searched]
        return result

    def analyze_image(self, prompt: str, image_path: str) -> str:
        """Загружает изображение и возвращает анализ GigaChat."""
        self._ensure_ready()
        return self._client.analyze_image(prompt, image_path)

    def status_text(self) -> str:
        return "Не задан AUTH_KEY в config/.env"