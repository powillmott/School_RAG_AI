"""app/core/config.py – Centralised settings loaded from environment variables.

All URLs default to the local docker-compose service names so that
`docker-compose up` works on a laptop with zero configuration.
Swap the values in a `.env` file (never committed) or via environment
variables when deploying to a different server.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM endpoint (Ollama locally, or DGX Spark IP in India)
    llm_base_url: str = "http://ollama-service:11434/v1"
    llm_model: str = "llama3"

    # Qdrant vector database
    vector_db_url: str = "http://qdrant:6333"
    vector_collection: str = "school_docs"

    # RACHEL server that hosts the school's digital library
    rachel_url: str = "http://rachel-server.local"
    rachel_library_path: str = "/library"

    # Path inside the container where PDFs are mounted
    docs_path: str = "/app/data"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
