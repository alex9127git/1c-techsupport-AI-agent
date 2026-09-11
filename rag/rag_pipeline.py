import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import environ
from pathlib import Path

from dotenv import load_dotenv

from rag.chunking import extract_and_chunk
from rag.const import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, MAX_WORKERS
from rag.database import init_state_db, get_row, upsert_row, delete_row
from rag.fileutils import file_hash, discover_files
from rag.vectoring import VectorIndex


def plan_work(conn: sqlite3.Connection, files: list[Path]):
    to_process: list[tuple[Path, str]] = []
    to_delete: list[str] = []

    seen_paths = set()
    for p in files:
        seen_paths.add(str(p))
        stat = p.stat()
        row = get_row(conn, str(p))

        if row is None:
            to_process.append((p, file_hash(p)))
            continue

        stored_hash, stored_doc_id, stored_size, stored_mtime = row

        if stored_size == stat.st_size and abs(stored_mtime - stat.st_mtime) < 1e-6:
            continue

        new_hash = file_hash(p)
        if new_hash == stored_hash:
            upsert_row(conn, str(p), new_hash, stat.st_size, stat.st_mtime, stored_doc_id)
            continue

        to_delete.append(stored_doc_id)
        to_process.append((p, new_hash))

    for path, doc_id in conn.execute('SELECT path, doc_id FROM knowledge_data').fetchall():
        if path not in seen_paths:
            to_delete.append(doc_id)
            delete_row(conn, path)

    return to_process, to_delete


def run_pipeline(docs_dir) -> None:
    files = discover_files(docs_dir)

    print(f'Найдено файлов: {len(files)}')
    if input(f'Продолжить индексацию? [Y/n] ')[:1] not in 'Yy':
        print('Отменено.')
        return

    print('Инициализация подключения к базе данных...')

    conn = init_state_db()
    index = VectorIndex(CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL)

    print('Подключение к базе данных установлено.')

    to_process, to_delete = plan_work(conn, files)

    for doc_id in to_delete:
        index.delete_doc(doc_id)
    if to_delete:
        print(f'Удалено документов из индекса: {len(to_delete)}')

    if not to_process:
        print('Нет новых/изменённых файлов — индексация не требуется.')
        return

    print(f'К обработке: {len(to_process)} файлов')

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(extract_and_chunk, str(p)): (p, h) for p, h in to_process}

        for fut in as_completed(futures):
            p, h = futures[fut]
            result = fut.result()

            if result['error']:
                print(f'[ОШИБКА] {p}: {result['error']}')
                continue

            doc_id = result['doc_id']
            chunks = result['chunks']

            written = index.add_chunks(doc_id, str(p), chunks)
            stat = p.stat()
            upsert_row(conn, str(p), h, stat.st_size, stat.st_mtime, doc_id)

            print(f'[OK] {p.name}: {len(chunks)} блоков → {written} векторов')

    print('Индексация завершена.')


if __name__ == '__main__':
    print('Завершён импорт библиотек.')
    docs_dir = Path(input('Введите полный путь к папке с данными: '))
    load_dotenv(dotenv_path='../config/.env')
    HF_TOKEN = environ['HF_TOKEN']
    run_pipeline(docs_dir)