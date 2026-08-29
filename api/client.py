from typing import Any
from dotenv import load_dotenv
import api.web
from api.auth import ApiToken
import json

load_dotenv(dotenv_path='../config/auth.env')


class ApiClient:
    token: ApiToken

    def __init__(self):
        self.token = ApiToken()

    def update_token(self):
        self.token.update()

    def generate_response(self) -> dict[str, Any]:
        self.update_token()
        session = api.web.get_empty_session()
        response = session.send(session.prepare_request(api.web.get_model_query_request(self.token)))
        return json.loads(response.text)


if __name__ == '__main__':
    client = ApiClient()
    print(client.generate_response())
