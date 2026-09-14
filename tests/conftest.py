import os
import sys
from pathlib import Path

import pytest

# Обеспечиваем импорт пакета app из корня проекта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_app.db")
os.environ.setdefault("DOCS_DIR", "data/test_docs")

from app import create_app, create_all_tables  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_database(app):
    """Очищает таблицы перед каждым тестом (тестовая БД живёт между тестами)."""
    from app.db import Base, get_database

    with app.app_context():
        Base.metadata.drop_all(bind=get_database().engine)
        Base.metadata.create_all(bind=get_database().engine)
    yield


@pytest.fixture()
def app():
    app = create_app()
    app.config["TESTING"] = True
    create_all_tables()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
