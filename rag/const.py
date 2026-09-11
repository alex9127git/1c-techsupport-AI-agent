from pathlib import Path

DB_PATH = Path('../db/app.db')
CHROMA_DIR = Path('./chroma_db')
COLLECTION_NAME = 'documents'
EMBED_MODEL = 'intfloat/multilingual-e5-base'
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
EMBED_BATCH = 64
MAX_WORKERS = 8
SUPPORTED_EXT = {'.pdf', '.txt', '.md'}
