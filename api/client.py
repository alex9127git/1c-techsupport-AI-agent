from os import environ
from typing import Any

from dotenv import load_dotenv
from requests import Response
import api.web
from api.auth import ApiToken
import json
from api.context import *


class ApiClient:
    auth_key: str
    token: ApiToken

    def __init__(self, auth_key):
        self.auth_key = auth_key
        self.token = ApiToken()
        self.update_token()

    def update_token(self):
        self.token.update(self.auth_key)

    def generate_response(self, context: Context) -> Response:
        self.update_token()
        session = api.web.get_empty_session()
        request = session.prepare_request(api.web.get_model_query_template())
        request.headers['Authorization'] = f'Bearer {self.token}'
        data = {
            'model': 'Gigachat-2',
            'messages': context.messages,
            'profanity_check': True,
            'response_format': context.response_format,
            'temperature': 0.1
        }
        request.body = json.dumps(data)
        request.headers['Content-Length'] = str(len(request.body))
        response = session.send(request)
        return response

    def generate_answer(self, prompt, context=None) -> Response:
        if context is None:
            context = get_empty_context()
            context.add_message('user', prompt)
        return self.generate_response(context)

    def response_pipeline(self, prompt, context=None):
        response = self.generate_answer(prompt, context)
        if response.status_code != 200:
            return f'Ошибка :(\n{response.status_code} {response.content}'
        prev_messages = json.loads(response.request.body)['messages'][1:]
        agent_output = json.loads(json.loads(response.text)['choices'][0]['message']['content'])
        self_rating = agent_output['confidence_level']
        assistant_message = {
            'role': 'assistant',
            'content': agent_output['output']
        }
        context = get_confidence_context([*prev_messages, assistant_message])
        retries = 0
        other_rating = 0
        other_rating_generated = False
        while retries < 3:
            rating_output = json.loads(self.generate_response(context).text)['choices'][0]['message']['content']
            if len(rating_output) > 0:
                other_rating = json.loads(rating_output)['confidence_level']
                other_rating_generated = True
                break
            retries += 1
        if not other_rating_generated:
            other_rating = self_rating
        return (assistant_message['content'] + f'\n\nУровень уверенности: {self_rating}%/{other_rating}%' +
                ('' if other_rating_generated else ' (уровень оценки не удалось получить)'))


if __name__ == '__main__':
    load_dotenv(dotenv_path='../config/auth.env')
    client = ApiClient(environ["AUTH_KEY"])
    question = input()
    print(client.response_pipeline(question))
