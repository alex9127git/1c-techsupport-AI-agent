import json
from datetime import *
import api.web


class TokenUpdateException(BaseException):
    pass


class ApiToken:
    access_token: str = ''
    expires_at: float = 0

    def __str__(self):
        return self.access_token

    def is_alive(self):
        return datetime.now(tz=timezone.utc).timestamp() * 1000 < self.expires_at

    def update(self, auth_key):
        if self.is_alive():
            return
        session = api.web.get_empty_session()
        request = session.prepare_request(api.web.get_token_request())
        request.headers['Authorization'] = f'Basic {auth_key}'
        response = session.send(request)
        if response.status_code != 200:
            raise TokenUpdateException(f'Error code {response.status_code}')
        response_json = json.loads(response.text)
        self.access_token = response_json['access_token']
        self.expires_at = response_json['expires_at']

