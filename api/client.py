import os
import traceback
import sys
from os import environ
from dotenv import load_dotenv
from requests import Response
import api.web
from api.auth import ApiToken
import json
from api.context import *
from api.context import Context
from api.files import FileHandler
import mimetypes
from api.web import get_message_from_response
from rag.const import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL
from rag.database import init_state_db
from rag.vectoring import VectorIndex


def except_hook(cls, exc, trc):
    sys.__excepthook__(cls, exc, trc)


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
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            request.files = {
                'file': (filename, file_content, mime_type),
                'purpose': (None, 'general')
            }
        prepared = session.prepare_request(request)
        response = session.send(prepared)
        if response.status_code != 200:
            return response.json()
        self.file_handler.add_file(json.loads(str(response.text))['id'])
        return response.json()

    def generate_response(self, context: Context) -> Response:
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
        if len(context.messages[-1].get('attachments', [])) > 0:
            data['function_call'] = {'name': 'get_file_content'}
            data['functions'] = [{'name': 'get_file_content'}]
        request.json = data
        prepared = session.prepare_request(request)
        response = session.send(prepared)
        return response

    def generate_answer(self, prompt, context=None) -> tuple[Context, Response]:
        if context is None:
            context = get_empty_context()
        reword_context = get_rewording_context(context.messages[1:])
        reword_context.add_message('user', prompt)
        reword_response = self.generate_response(reword_context)
        reword_message = get_message_from_response(reword_response)
        reword_query = json.loads(reword_message['content'])['query']
        sources = self.db.search(
            reword_query,
            k=10,
            min_score=0.4
        )
        with open('./tmp.txt', 'w') as f:
            source_text = '\n\n'.join(map(lambda x: x['text'], sources))
            f.write(source_text)
        self.upload_file("./tmp.txt")
        os.remove("./tmp.txt")
        context.add_message('user', prompt, self.file_handler.use())
        return context, self.generate_response(context)

    def response_pipeline(self, prompt, context=None):
        if prompt.startswith('upload'):
            response = self.upload_file(prompt[7:])
            return context, response
        result_context, response = self.generate_answer(prompt, context)
        if response.status_code != 200:
            return context, f'Ошибка :(\n{response.status_code} {response.json()}'
        prev_messages = json.loads(response.request.body)['messages'][1:]
        assistant_message = get_message_from_response(response)
        context = get_confidence_context([*prev_messages, assistant_message])
        retries = 0
        rating = 0
        other_rating_generated = False
        while retries < 3:
            rating_response = self.generate_response(context)
            if rating_response.status_code != 200:
                print(rating_response.json())
                rating_output = ''
            else:
                rating_output = get_message_from_response(rating_response)['content']
            if len(rating_output) > 0:
                rating = json.loads(rating_output)['confidence_level']
                other_rating_generated = True
                break
            retries += 1
        result_context.add_message(assistant_message['role'], assistant_message['content'])
        return (result_context,
                assistant_message['content'] + f'\n\nУровень уверенности: ' +
                (f'{rating}%' if other_rating_generated else 'не удалось получить'))


if __name__ == '__main__':
    sys.excepthook = except_hook
    load_dotenv(dotenv_path='../config/.env')
    HF_TOKEN = environ['HF_TOKEN']
    print('Инициализация подключения к базе данных...')
    conn = init_state_db()
    index = VectorIndex(CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL)
    print('Подключение к базе данных установлено.')
    client = ApiClient(environ["AUTH_KEY"], index)
    ctxt = None
    while question := input():
        try:
            ctxt, msg = client.response_pipeline(question, ctxt)
            print(msg)
            print(1 / 0)
        except BaseException:
            traceback.print_exc()
