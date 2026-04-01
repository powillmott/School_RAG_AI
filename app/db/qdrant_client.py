"""app/db/qdrant_client.py – Thin wrapper around the Qdrant vector store.

Provides a single `get_vector_store()` factory so the rest of the
application never imports qdrant-client directly and the underlying
implementation can be swapped easily.
"""
from functools import lru_cache

from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import settings

# Embedding dimension for the default "text-embedding-ada-002" model.
# Override EMBEDDING_DIM if you switch to a different embedding model.
EMBEDDING_DIM = 1536


def _ensure_collection(client: QdrantClient) -> None:
    """Create the Qdrant collection if it does not already exist."""
    existing = {c.name for c in client.get_collections().collections}
    if settings.vector_collection not in existing:
        client.create_collection(
            collection_name=settings.vector_collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Return a cached Qdrant HTTP client."""
    return QdrantClient(url=settings.vector_db_url)


def get_vector_store() -> Qdrant:
    """Return a LangChain Qdrant vector store backed by OpenAI embeddings.

    The embeddings are proxied through ``settings.llm_base_url`` so that
    Ollama (or any OpenAI-compatible endpoint) is used instead of the
    real OpenAI API.
    """
    client = get_qdrant_client()
    _ensure_collection(client)

    embeddings = OpenAIEmbeddings(
        base_url=settings.llm_base_url,
        # Use a dummy key; Ollama does not require a real key.
        api_key="ollama",
    )

    return Qdrant(
        client=client,
        collection_name=settings.vector_collection,
        embeddings=embeddings,
    )
