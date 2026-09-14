# 1C Techsupport AI Agent

Intelligent AI-agent для автоматизации технической поддержки пользователей 1С.

## Требования

- Python 3.11+
- Команды ниже приведены для Windows PowerShell

## Быстрый старт (локалхост)

```powershell
# 1. Создание виртуального окружения и установка зависимостей
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Конфигурация
Copy-Item config\.env.example config\.env
# Отредактируйте config\.env при необходимости (см. таблицу ниже)

# 3. Применение миграций базы данных
alembic upgrade head

# 4. Начальное наполнение БД
python -m scripts.seed

# 5. Запуск сервера
python wsgi.py
```

После запуска откройте в браузере: `http://127.0.0.1:5000`

### Индексация базы знаний (RAG)

Документы для RAG берутся из папки `DOCS_DIR` (по умолчанию `data/docs`).
Поддерживаются форматы: Markdown (`.md`), текст (`.txt`), PDF (`.pdf`).

```powershell
# Пакетная индексация папки с документами (идемпотентна: меняет только изменившиеся)
python -m scripts.index_docs data/docs

# Например, для спарсенной документации 1С из папки out/
python -m scripts.index_docs out
```

Загрузка файлов через панель («База знаний 1С» → «Загрузить новый файл»)
сохраняет документ в `DOCS_DIR` и сразу индексирует его в векторное хранилище.
Удаление документа из панели вычищает и запись, и файл, и вектора.

### Переменные окружения (`config\.env`)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | Строка подключения к БД. Для PostgreSQL: `postgresql+psycopg://user:pass@host:5432/db` | `sqlite:///./app.db` |
| `CONFIDENCE_THRESHOLD` | Порог уверенности для автоответа AI, % | `80` |
| `ESCALATION_STRATEGY` | Стратегия эскалации | `human_review` |
| `AUTH_KEY` | Ключ доступа к GigaChat (обязателен для реальных ответов AI) | — |
| `HF_TOKEN` | Токен Hugging Face для модели эмбеддингов RAG (опционален, модель публичная) | — |
| `DOCS_DIR` | Папка с документами для RAG-индексации | `data/docs` |

`AUTH_KEY` нужен для реальных ответов AI. Без него панель и API работают,
но `/api/chat` отвечает статусом `not_configured` с пояснением. `HF_TOKEN`
опционален, т.к. модель эмбеддингов публичная.

## Маршруты

- `/` — панель администратора
- `/dev` — dev-консоль для проверки API
- `/api/*` — JSON API

## Тесты

```powershell
python -m pytest -q tests
```

## Структура проекта

```
app/       Flask-приложение: routes, services, repositories, models, schemas,
           templates (панель), static (css/js), db
api/       Ядро на GigaChat: клиент, контексты, авторизация, файлы
rag/       RAG-пайплайн: индексация документов и векторный поиск (Chroma)
config/    Конфигурация (.env) и сертификаты
scripts/   Вспомогательные скрипты (seed.py — наполнение БД)
tests/     Тесты на pytest
wsgi.py    Точка входа приложения
```