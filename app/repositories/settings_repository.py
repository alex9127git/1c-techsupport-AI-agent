import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import Setting


class SettingsRepository:
    """Репозиторий настроек (key-value)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self._session.get(Setting, key)
        return row.value if row else default

    def set(self, key: str, value: str) -> None:
        row = self._session.get(Setting, key)
        if row is None:
            self._session.add(Setting(key=key, value=value))
        else:
            row.value = value
        self._session.commit()

    def get_json(self, key: str, default: object = None) -> object:
        raw = self.get(key)
        if raw is None:
            return default
        return json.loads(raw)

    def set_json(self, key: str, value: object) -> None:
        self.set(key, json.dumps(value, ensure_ascii=False))
