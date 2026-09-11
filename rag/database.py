import sqlite3
from datetime import datetime, timezone

from rag.const import DB_PATH


def init_state_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_data (
            path       TEXT PRIMARY KEY,
            hash       TEXT NOT NULL,
            size       INTEGER,
            mtime      REAL,
            doc_id     TEXT NOT NULL,
            indexed_at TEXT
        )
    ''')
    conn.commit()
    return conn


def get_row(conn, path: str):
    return conn.execute(
        'SELECT hash, doc_id, size, mtime FROM knowledge_data WHERE path = ?',
        (path,),
    ).fetchone()


def upsert_row(conn, path: str, h: str, size: int, mtime: float, doc_id: str):
    conn.execute('''
        INSERT INTO knowledge_data (path, hash, size, mtime, doc_id, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            hash       = excluded.hash,
            size       = excluded.size,
            mtime      = excluded.mtime,
            doc_id     = excluded.doc_id,
            indexed_at = excluded.indexed_at
    ''', (path, h, size, mtime, doc_id, datetime.now(timezone.utc).isoformat()))
    conn.commit()


def delete_row(conn, path: str):
    conn.execute('DELETE FROM files WHERE path = ?', (path,))
    conn.commit()
