from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


class Database:
    """Фабрика движка БД и сессий.

    Движок создаётся из database_url (см. app.config.Settings). Абстракция
    позволяет переключаться между SQLite и PostgreSQL без изменения кода.
    """

    def __init__(self, database_url: str) -> None:
        connect_args = (
            {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        )
        self._engine = create_engine(database_url, connect_args=connect_args)
        self._session_factory = sessionmaker(
            bind=self._engine, expire_on_commit=False, autoflush=False
        )

    @property
    def engine(self):
        return self._engine

    def session(self) -> Session:
        return self._session_factory()

    def __call__(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()


_database: Database | None = None


def configure_database(database_url: str) -> Database:
    global _database
    _database = Database(database_url)
    return _database


def get_database() -> Database:
    if _database is None:
        raise RuntimeError("Database not configured. Call configure_database() first.")
    return _database


def get_session() -> Iterator[Session]:
    yield from get_database()()
