#!/bin/sh
set -e

echo "[entrypoint] ÐŸÑ€Ð¸Ð¼ÐµÐ½ÑÑŽ Ð¼Ð¸Ð³Ñ€Ð°Ñ†Ð¸Ð¸ Ð‘Ð”..."
alembic upgrade head

echo "[entrypoint] ÐÐ°Ð¿Ð¾Ð»Ð½ÑÑŽ Ð‘Ð” Ð½Ð°Ñ‡Ð°Ð»ÑŒÐ½Ñ‹Ð¼Ð¸ Ð½Ð°ÑÑ‚Ñ€Ð¾Ð¹ÐºÐ°Ð¼Ð¸..."
python -m scripts.seed

echo "[entrypoint] Ð—Ð°Ð¿ÑƒÑÐºÐ°ÑŽ gunicorn Ð½Ð° 0.0.0.0:5000..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 --access-logfile - wsgi:app