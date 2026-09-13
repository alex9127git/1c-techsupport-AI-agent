import os.path
from os import path


BASE_DIR = path.join(path.dirname(os.path.abspath(__file__)), '..')
DB_PATH = path.join(BASE_DIR, './db/app.db')
CHROMA_DIR = path.join(BASE_DIR, './db/chroma_db')
COLLECTION_NAME = 'documents'
EMBED_MODEL = 'intfloat/multilingual-e5-base'
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
EMBED_BATCH = 64
MAX_WORKERS = 8
SUPPORTED_EXT = {'.pdf', '.txt', '.md'}
