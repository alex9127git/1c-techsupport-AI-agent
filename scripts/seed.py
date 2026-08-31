"""Seed дефолтных настроек в БД.

Схема управляется Alembic-миграциями; данные — этим скриптом.
Запуск: python -m scripts.seed
"""

from app.config import get_settings
from app.db import configure_database, get_database
from app.models.setting import Setting

DEFAULTS = {
    "confidence_threshold": "80",
    "escalation_strategy": "human_review",
}


def seed() -> None:
    settings = get_settings()
    configure_database(settings.database_url)
    session = get_database().session()
    try:
        for key, value in DEFAULTS.items():
            if session.get(Setting, key) is None:
                session.add(Setting(key=key, value=value))
        session.commit()
        print("Seed completed.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
