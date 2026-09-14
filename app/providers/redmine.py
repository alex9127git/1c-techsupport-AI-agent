from __future__ import annotations

import requests


class RedmineClient:
    """REST-клиент к Redmine (REST API).

    base_url — URL установки Redmine (например, https://redmine.example).
    add_comment добавляет заметку к задаче: PUT /issues/{id}.json
    с заголовком X-Redmine-API-Key (стандартный способ авторизации API).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or "").rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._session = session or requests.Session()

    def add_comment(self, issue_id: int | str, notes: str) -> dict:
        """Добавляет комментарий к задаче через REST API."""
        resp = self._session.put(
            f'{self.base_url}/issues/{issue_id}.json',
            headers={'X-Redmine-API-Key': self.api_key},
            json={'issue': {'notes': notes}},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def parse_payload(payload: dict) -> dict:
        """Разбирает вебхук плагина redmine_webhook.

        Плагин шлёт {"payload": {"action", "issue": {...}, "journal": {...}}}.
        Принимается и упрощённая форма {"issue": {...}}.
        """
        root = payload.get('payload') if isinstance(payload.get('payload'), dict) else payload
        issue = root.get('issue') if isinstance(root.get('issue'), dict) else {}
        action = root.get('action', 'updated')
        return {
            'action': action,
            'issue_id': int(issue.get('id')) if issue.get('id') is not None else None,
            'subject': (issue.get('subject') or '').strip(),
            'description': (issue.get('description') or '').strip(),
            'url': root.get('url', ''),
        }