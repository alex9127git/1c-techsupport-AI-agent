import json
from datetime import *
import api.web


class ApiToken:
    access_token: str = ''
    expires_at: float = 0

    def __init__(self):
        self.update()

    def __str__(self):
        return self.access_token

    def is_alive(self):
        return datetime.now(tz=timezone.utc).timestamp() * 1000 < self.expires_at

    def update(self):
        if self.is_alive():
            return
        session = api.web.get_empty_session()
        response = session.send(session.prepare_request(api.web.get_token_request()))
        response_json = json.loads(response.text)
        self.access_token = response_json['access_token']
        self.expires_at = response_json['expires_at']

