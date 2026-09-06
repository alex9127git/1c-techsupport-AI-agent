from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Типизированная конфигурация приложения.

    Значения читаются из переменных окружения / .env. Смена БД на PostgreSQL
    выполняется заменой DATABASE_URL (e.g. postgresql+psycopg://user:pass@host/db)
    без изменения кода.
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / "config" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "1C Techsupport AI Agent"
    debug: bool = False

    database_url: str = "sqlite:///./app.db"

    confidence_threshold: int = 80
    escalation_strategy: str = "human_review"


def get_settings() -> Settings:
    return Settings()
