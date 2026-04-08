"""app/main.py – FastAPI application entry point."""
from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="School RAG AI",
    description=(
        "A Retrieval-Augmented Generation (RAG) backend that connects the "
        "RACHEL digital library to a local LLM (Ollama / DGX Spark) via "
        "a Qdrant vector database."
    ),
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    """Simple liveness probe used by Docker and monitoring tools."""
    return {"status": "ok"}
