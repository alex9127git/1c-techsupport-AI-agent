import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import Channel


class ChannelRepository:
    """Репозиторий каналов интеграций (Bitrix24, Redmine).

    Конфигурация канала хранится в колонке config в виде JSON-строки.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, name: str) -> Channel | None:
        return self._session.get(Channel, name)

    def list_all(self) -> list[Channel]:
        return list(self._session.scalars(select(Channel).order_by(Channel.name)).all())

    def config(self, name: str) -> dict:
        row = self.get(name)
        if row is None:
            return {}
        try:
            return json.loads(row.config or "{}")
        except Exception:
            return {}

    def upsert(self, name: str, config: dict, enabled: bool = True) -> Channel:
        payload = json.dumps(config, ensure_ascii=False)
        row = self.get(name)
        if row is None:
            row = Channel(name=name, enabled=enabled, config=payload)
            self._session.add(row)
        else:
            row.enabled = enabled
            row.config = payload
        self._session.commit()
        self._session.refresh(row)
        return row

    def set_enabled(self, name: str, enabled: bool) -> Channel | None:
        row = self.get(name)
        if row is None:
            return None
        row.enabled = enabled
        self._session.commit()
        self._session.refresh(row)
        return row