"""Пакетная индексация спарсенной документации.

Запуск:
    python -m scripts.index_docs <путь_к_папке_с_документами>
    python -m scripts.index_docs out

Формат команды повторяет интерактивный rag_pipeline.run_pipeline, но без
подтверждения. Индексация идемпотентна: изменённые файлы переиндексируются,
удалённые — вычищаются из Chroma и state-базы.
"""
import sys
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    docs_dir = Path(sys.argv[1])
    if not docs_dir.is_dir():
        print(f"Папка не найдена: {docs_dir}")
        sys.exit(1)

    from rag.rag_pipeline import run_pipeline

    run_pipeline(docs_dir, confirm=False)