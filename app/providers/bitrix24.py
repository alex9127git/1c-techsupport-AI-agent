from __future__ import annotations

import json
from urllib.parse import urlparse, urlunparse

import requests


class Bitrix24Client:
    """REST-клиент к вебхуку Bitrix24.

    webhook_url вида https://{portal}/rest/{user_id}/{webhook_token}/.
    Отправка поддерживает два стиля:
      * классический `chat.message.add` (CHAT_ID, без bot),
      * imbot.v2 `imbot.v2.Chat.Message.send` (botId/botToken), если заданы
        bot_id и bot_token — используется в связке с демо-ботом.
    """

    def __init__(
        self,
        webhook_url: str,
        bot_id: str | None = None,
        bot_token: str | None = None,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.webhook_url = self.normalize_webhook_url(webhook_url)
        self.bot_id = bot_id
        self.bot_token = bot_token
        self.timeout = timeout
        self._session = session or requests.Session()

    def _call(self, method: str, params: dict) -> dict | list:
        resp = self._session.post(f'{self.webhook_url}{method}', json=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def send_message(self, dialog_id: str, message: str) -> dict | list:
        """Отправляет сообщение в диалог ({userId} или chat{chatId})."""
        if self.bot_id and self.bot_token:
            params = {
                'botId': self.bot_id,
                'botToken': self.bot_token,
                'dialogId': dialog_id,
                'fields': {'message': message},
            }
            return self._call('imbot.v2.Chat.Message.send', params)
        return self._call('chat.message.add', {'CHAT_ID': dialog_id, 'MESSAGE': message})

    @staticmethod
    def parse_payload(payload: dict) -> dict:
        """Разбирает событие ONIMBOTV2MESSAGEADD / ONIMBOTMESSAGEADD.

        Поддерживает как JSON от imbot.v2 (data.bot/message/chat), так и
        старый формат (data.BOT / data.PARAMS), включая форму из
        form-urlencoded (PHP-ключи data[bot][id] уже преобразованы в dict).
        """
        event = payload.get('event', '')
        data = payload.get('data') or {}

        bot, message, chat = _v2_fields(data)
        if bot is None and message is None and chat is None:
            bot, message, chat = _v1_fields(data)

        return {
            'event': event,
            'message': (message.get('text') or message.get('MESSAGE') or '').strip(),
            'dialog_id': str(chat.get('dialogId') or message.get('DIALOG_ID') or ''),
            'bot_id': str(bot.get('id') or '') if bot else '',
            'application_token': _deep_get(payload, 'auth', 'application_token', default=''),
            'ts': payload.get('ts'),
        }

    @staticmethod
    def normalize_webhook_url(raw: str) -> str:
        """Приводит URL к виду https://{domain}/rest/{user}/{token}/."""
        value = (raw or '').strip()
        if not value:
            return ''
        parsed = urlparse(value)
        if not parsed.scheme:
            value = 'https://' + value
            parsed = urlparse(value)
        path = parsed.path.rstrip('/')
        if '/rest/' not in path:
            path = path + '/rest/'
        elif not path.endswith('/rest/'):
            path = path + '/'
        return urlunparse(('https' if parsed.scheme != 'http' else 'http', parsed.netloc, path, '', '', ''))


def _v2_fields(data: dict) -> tuple[dict | None, dict | None, dict | None]:
    bot = data.get('bot') if isinstance(data.get('bot'), dict) else None
    message = data.get('message') if isinstance(data.get('message'), dict) else None
    chat = data.get('chat') if isinstance(data.get('chat'), dict) else None
    if bot is None and message is None and chat is None:
        return None, None, None
    return bot, message, chat


def _v1_fields(data: dict) -> tuple[dict | None, dict | None, dict | None]:
    """Поддержка старого формата: data.BOT[bot_id] + data.PARAMS."""
    bots = data.get('BOT')
    bot = {}
    if isinstance(bots, dict) and bots:
        first = next(iter(bots.values()))
        if isinstance(first, dict):
            bot = {'id': first.get('BOT_ID') or first.get('bot_id')}
    params = data.get('PARAMS') if isinstance(data.get('PARAMS'), dict) else {}
    message = {'text': params.get('MESSAGE'), 'DIALOG_ID': params.get('DIALOG_ID')}
    chat = {'dialogId': params.get('DIALOG_ID')}
    return bot, message, chat


def _deep_get(obj: dict, *keys: str, default: str = '') -> str:
    cursor = obj
    for key in keys:
        if not isinstance(cursor, dict) or key not in cursor:
            return default
        cursor = cursor[key]
    return cursor if isinstance(cursor, str) else str(cursor)


def _coerce_scalar(value: str):
    try:
        return json.loads(value)
    except Exception:
        return value