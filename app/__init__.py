from flask import Flask
from flask_cors import CORS

from app.config import Settings, get_settings
from app.db import Base, configure_database


def create_app(settings: Settings | None = None) -> Flask:
    """Фабрика приложения.

    Собирает конфигурацию, инициализирует БД и регистрирует blueprints.
    """
    settings = settings or get_settings()

    from app.db import get_database

    app = Flask(__name__)
    app.config.from_mapping(
        DEBUG=settings.debug,
        DATABASE_URL=settings.database_url,
        CONFIDENCE_THRESHOLD=settings.confidence_threshold,
        ESCALATION_STRATEGY=settings.escalation_strategy,
    )

    CORS(app)

    configure_database(settings.database_url)
    app.extensions["database"] = get_database()

    from app.models import __all__ as _model_names  # noqa: F401  (регистрация моделей в Base.metadata)
    from app.routes import register_blueprints

    register_blueprints(app)

    return app


def create_all_tables() -> None:
    """Создаёт все таблицы из метаданных моделей (для тестов/быстрого старта)."""
    from app.db import get_database

    Base.metadata.create_all(bind=get_database().engine)
