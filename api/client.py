import json
import os
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from os import environ
from typing import Any

import api.web
from api.auth import ApiToken
from api.context import (
    Context,
    get_answer_with_confidence_context,
    get_empty_context,
    get_image_analysis_context,
    get_rewording_context,
)
from api.files import FileHandler
from api.web import get_message_from_response
from rag.database import init_state_db
from rag.vectoring import VectorIndex


def except_hook(cls, exc, trc):
    sys.__excepthook__(cls, exc, trc)


@dataclass
class AnswerResult:
    answer: str
    confidence: int | None = None
    sources: list[str] = field(default_factory=list)


class ModelError(Exception):
    """Сетевая/HTTP ошибка обращения к GigaChat."""


class ApiClient:
    auth_key: str
    token: ApiToken
    file_handler: FileHandler
    db: VectorIndex

    def __init__(self, auth_key, db_conn):
        self.auth_key = auth_key
        self.token = ApiToken()
        self.file_handler = FileHandler()
        self.update_token()
        self.db = db_conn

    def update_token(self):
        self.token.update(self.auth_key)

    def upload_file(self, filename):
        self.update_token()
        session = api.web.get_empty_session()
        request = api.web.get_model_attachment_template()
        request.headers['Authorization'] = f'Bearer {self.token}'
        with open(filename, 'rb') as f:
            file_content = f.read()
        return self._upload_bytes(request, filename, file_content)

    def _upload_bytes(self, request: Any, filename: str, file_content: bytes):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        request.files = {
            'file': (filename, file_content, mime_type),
            'purpose': (None, 'general')
        }
        prepared = api.web.get_empty_session().prepare_request(request)
        response = api.web.get_empty_session().send(prepared)
        if response.status_code != 200:
            return response.json()
        self.file_handler.add_file(json.loads(str(response.text))['id'])
        return response.json()

    def generate_response(self, context: Context, use_file_call: bool = True):
        self.update_token()
        session = api.web.get_empty_session()
        request = api.web.get_model_query_template()
        request.headers['Authorization'] = f'Bearer {self.token}'
        data = {
            'model': 'Gigachat-3-Pro',
            'messages': context.messages,
            'profanity_check': True,
            'response_format': context.response_format,
            'temperature': 0.1
        }
        if use_file_call and len(context.messages[-1].get('attachments', [])) > 0:
            data['function_call'] = {'name': 'get_file_content'}
            data['functions'] = [{'name': 'get_file_content'}]
        request.json = data
        prepared = session.prepare_request(request)
        response = session.send(prepared)
        return response

    def analyze_image(self, prompt: str, image_path: str) -> str:
        """
        Загружает изображение в хранилище GigaChat и возвращает анализ.
        Для изображений встроенная функция get_file_content не используется —
        attachments передаются как есть (см. документацию «Работа с файлами»).
        """
        self.update_token()
        upload = self.upload_file(image_path)
        if isinstance(upload, dict) and upload.get('id'):
            file_id = upload['id']
        else:
            raise ModelError(f'Не удалось загрузить изображение: {upload!r}')

        context = get_image_analysis_context()
        context.add_message('user', prompt, [file_id])

        response = self.generate_response(context, use_file_call=False)
        if response.status_code != 200:
            raise ModelError(f'{response.status_code} {response.text}')

        message = get_message_from_response(response)
        return message.get('content', '').strip()

    def generate_answer(self, prompt, history=None) -> tuple[Context, str, int | None]:
        """
        Двухфазный пайплайн: переформулирование вопроса (1 запрос) и
        ответ + оценка уверенности одним запросом (1 запрос) через json_schema.
        Возвращает контекст, текст ответа и процент уверенности.
        """
        history = history or []
        reword_context = get_rewording_context(history)
        reword_context.add_message('user', prompt)
        reword_response = self.generate_response(reword_context)
        reword_message = get_message_from_response(reword_response)
        reword_query = json.loads(reword_message['content'])['query']

        sources = []
        try:
            sources = self.db.search(reword_query, k=10, min_score=0.4)
        except Exception as e:
            print(f'[RAG] Ошибка поиска: {e!r}')

        source_text = '\n\n'.join(x['text'] for x in sources)
        attachments = []
        if source_text:
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.txt', encoding='utf-8', delete=False
                ) as tmp:
                    tmp.write(source_text)
                    tmp_path = tmp.name
                self.upload_file(tmp_path)
                attachments = self.file_handler.use()
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

        answer_context = get_answer_with_confidence_context(history)
        answer_context.add_message('user', prompt, attachments)

        response = self.generate_response(answer_context)
        if response.status_code != 200:
            raise ModelError(f'{response.status_code} {response.text}')

        message = get_message_from_response(response)
        content = json.loads(message['content'])
        answer = content.get('answer', '')
        confidence_raw = content.get('confidence_level')
        confidence = int(confidence_raw) if confidence_raw is not None else None
        return answer_context, answer, confidence

    def response_pipeline(self, prompt, context=None) -> tuple[Context, str, int | None]:
        """Обратно совместимая обёртка: принимает объект Context, отдаёт (context, answer, confidence)."""
        if prompt.startswith('upload'):
            response = self.upload_file(prompt[7:])
            return context, str(response), None
        history = context.messages[1:] if context is not None else None
        result_context, answer, confidence = self.generate_answer(prompt, history)
        return result_context, answer, confidence


if __name__ == '__main__':
    sys.excepthook = except_hook
    from dotenv import load_dotenv
    from pathlib import Path
    from rag.const import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL

    load_dotenv(dotenv_path='../config/.env')
    print('Инициализация подключения к базе данных...')
    conn = init_state_db()
    index = VectorIndex(CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL)
    print('Подключение к базе данных установлено.')
    client = ApiClient(environ["AUTH_KEY"], index)
    ctxt = None
    while question := input():
        try:
            ctxt, answer, confidence = client.response_pipeline(question, ctxt)
            print(answer)
            print(f'Уверенность: {confidence}%')
        except BaseException:
            traceback.print_exc()