from os import environ
from dotenv import load_dotenv
from rag.const import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL
from rag.database import init_state_db
from rag.vectoring import VectorIndex


if __name__ == '__main__':
    load_dotenv(dotenv_path='../config/.env')
    HF_TOKEN = environ['HF_TOKEN']
    print('Инициализация подключения к базе данных...')
    conn = init_state_db()
    index = VectorIndex(CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL)
    print('Подключение к базе данных установлено.')
    print('Введите промпт для тестирования функциональности поиска.')
    result = index.search(input(),
                          k=20,
                          min_score=0.4)
    for item in result:
        print(item)
        print()
