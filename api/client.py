from os import environ
from dotenv import load_dotenv
from requests import Response
import api.web
from api.auth import ApiToken
import json
from api.context import get_empty_context


class ApiClient:
    auth_key: str
    token: ApiToken

    def __init__(self, auth_key):
        self.auth_key = auth_key
        self.token = ApiToken()
        self.update_token()

    def update_token(self):
        self.token.update(self.auth_key)

    def generate_response(self, prompt) -> Response:
        self.update_token()
        session = api.web.get_empty_session()
        request = session.prepare_request(api.web.get_model_query_template())
        request.headers['Authorization'] = f'Bearer {self.token}'
        context = get_empty_context()
        context.add_message('user', prompt)
        data = {
            'model': 'Gigachat-2',
            'messages': context.messages,
            'profanity_check': True
        }
        request.body = json.dumps(data)
        request.headers['Content-Length'] = str(len(request.body))
        response = session.send(request)
        return response

    def extract_message(self, response):
        response_json = json.loads(response.text)
        if response.status_code == 200:
            return response_json['choices'][0]['message']['content']
        else:
            return response_json


if __name__ == '__main__':
    load_dotenv(dotenv_path='../config/auth.env')
    client = ApiClient(environ["AUTH_KEY"])
    question = input()
    prompt_response = client.generate_response(question)
    print(client.extract_message(prompt_response))
