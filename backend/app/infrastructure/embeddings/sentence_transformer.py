import asyncio
from functools import lru_cache

from app.config import settings


class SentenceTransformerEmbeddingService:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None
        self._lock = asyncio.Lock()

    async def _get_model(self):
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    loop = asyncio.get_event_loop()
                    self._model = await loop.run_in_executor(
                        None, lambda: SentenceTransformer(self._model_name)
                    )
        return self._model

    async def embed(self, text: str) -> list[float]:
        model = await self._get_model()
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(None, lambda: model.encode(text, normalize_embeddings=True))
        return vector.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = await self._get_model()
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            None, lambda: model.encode(texts, normalize_embeddings=True)
        )
        return [v.tolist() for v in vectors]


@lru_cache
def get_embedding_service() -> SentenceTransformerEmbeddingService:
    return SentenceTransformerEmbeddingService(settings.embedding_model)
