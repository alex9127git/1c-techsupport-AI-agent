from pathlib import Path

if __name__ == 'rag.chunking':
    print('Импортируются сплиттеры текста...')
from langchain_text_splitters import RecursiveCharacterTextSplitter
if __name__ == 'rag.chunking':
    print('Завершён импорт сплиттеров текста.')
from pypdf import PdfReader

from rag.fileutils import make_doc_id
from rag.const import CHUNK_SIZE, CHUNK_OVERLAP


def _extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return '\n\n'.join((page.extract_text() or '') for page in reader.pages)


def extract_and_chunk(path_str: str) -> dict:
    path = Path(path_str)
    try:
        if path.suffix.lower() == '.pdf':
            text = _extract_pdf(path)
        else:
            text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return {'path': path_str, 'error': repr(e), 'chunks': [], 'doc_id': None}

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = text_splitter.split_text(text)
    return {
        'path': str(path),
        'doc_id': make_doc_id(str(path)),
        'chunks': chunks,
        'error': None,
    }
