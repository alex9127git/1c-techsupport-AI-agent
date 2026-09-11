from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from rag.const import EMBED_BATCH


class VectorIndex:
    """Обёртка над Chroma: батчевый upsert и удаление по doc_id."""

    def __init__(self, persist_dir: Path, collection_name: str, model_name: str):
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={'hnsw:space': 'cosine'},
        )
        # Модель держим в памяти главного процесса.
        self.model = SentenceTransformer(model_name)

    def delete_doc(self, doc_id: str) -> None:
        """Удаляет все чанки документа по метаданным."""
        self.collection.delete(where={'doc_id': doc_id})

    def add_chunks(self, doc_id: str, source: str, chunks: list[str]) -> int:
        if not chunks:
            return 0
        written = 0
        for i in range(0, len(chunks), EMBED_BATCH):
            batch = chunks[i : i + EMBED_BATCH]
            ids = [f'{doc_id}:{i + j}' for j in range(len(batch))]
            metadata = [
                {'doc_id': doc_id, 'source': source, 'chunk_index': i + j}
                for j in range(len(batch))
            ]
            # normalize_embeddings=True — косинусное сходство работает корректно.
            embeddings = self.model.encode(
                batch,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).tolist()

            self.collection.upsert(
                ids=ids,
                documents=batch,
                metadatas=metadata,
                embeddings=embeddings,
            )
            written += len(batch)
        return written
