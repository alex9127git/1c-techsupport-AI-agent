FROM python:3.11-slim

WORKDIR /app

# torch/sentence-transformers требуют системных библиотек
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Точки монтирования данных (см. docker-compose.yml)
VOLUME ["/app/db", "/app/data/docs", "/app/.cache"]

ENV HF_HOME=/app/.cache/huggingface
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]