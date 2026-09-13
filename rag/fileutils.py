import hashlib
from pathlib import Path

from rag.const import SUPPORTED_EXT


def file_hash(path: Path, block_size: int = 1 << 20) -> str:
    """SHA-256 по содержимому файла. Читаем блоками, чтобы не грузить всё в память."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def make_doc_id(path: str) -> str:
    """
    Стабильный ID документа. Привязан к пути, а не к содержимому:
    так при изменении файла мы легко удалим старые чанки по doc_id.
    """
    return hashlib.sha1(path.encode('utf-8')).hexdigest()[:16]


def discover_files(root: Path) -> list[Path]:
    return [
        p for p in root.rglob('*')
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXT
    ]
