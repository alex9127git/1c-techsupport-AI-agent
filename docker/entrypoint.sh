#!/bin/sh
set -e

echo "[entrypoint] Применяю миграции БД..."
alembic upgrade head

echo "[entrypoint] Наполняю БД начальными настройками..."
python -m scripts.seed

echo "[entrypoint] Запускаю gunicorn на 0.0.0.0:5000..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 --access-logfile - wsgi:app