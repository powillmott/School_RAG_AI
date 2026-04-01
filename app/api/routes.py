"""app/api/routes.py – FastAPI routers for /ask and /ingest."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services import ingestor, rag_chain

router = APIRouter()


# ── /ask ─────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str


class Citation(BaseModel):
    title: str
    page: int | None = None
    url: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]


@router.post("/ask", response_model=AskResponse)
def ask_question(body: AskRequest) -> AskResponse:
    """Answer a student's question using the RAG pipeline.

    The response includes the LLM's answer and a list of citations that
    link back to the original documents on the RACHEL server.
    """
    if not body.question.strip():
        raise HTTPException(status_code=422, detail="Question must not be empty.")
    result = rag_chain.ask(body.question)
    return AskResponse(**result)


# ── /ingest ───────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    message: str
    chunks_stored: int


@router.post("/ingest/directory", response_model=IngestResponse)
def ingest_directory() -> IngestResponse:
    """Trigger ingestion of all PDFs in the configured data directory.

    The data directory is set via the ``DOCS_PATH`` environment variable
    (default: ``/app/data``).  To ingest a custom path, use the CLI script
    ``scripts/ingest_docs.py --directory <path>`` instead.
    """
    chunks = ingestor.ingest_directory()
    return IngestResponse(
        message=f"Ingestion complete. {chunks} chunks stored.",
        chunks_stored=chunks,
    )


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)) -> IngestResponse:
    """Upload and ingest a single PDF file.

    The file is saved temporarily, processed, then the temp copy is removed.
    """
    import os
    import shutil
    import tempfile

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        chunks = ingestor.ingest_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    return IngestResponse(
        message=f"File '{file.filename}' ingested. {chunks} chunks stored.",
        chunks_stored=chunks,
    )
