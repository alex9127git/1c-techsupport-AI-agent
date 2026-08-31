import os
import sys
from pathlib import Path

import pytest

# Обеспечиваем импорт пакета app из корня проекта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_app.db")

from app import create_app, create_all_tables  # noqa: E402


@pytest.fixture()
def app():
    app = create_app()
    app.config["TESTING"] = True
    create_all_tables()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
