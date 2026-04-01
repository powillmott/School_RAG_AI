"""app/services/ingestor.py – Ingest PDF documents into Qdrant.

Two responsibilities:
1. Load PDFs from a local folder (or a single file) and split them into
   chunks suitable for embedding.
2. Map local file paths to clickable RACHEL URLs so that citations point
   students to a page they can open in a browser.
"""
import os
from pathlib import Path
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.core.config import settings
from app.db.qdrant_client import get_vector_store

# ── Text splitter configuration ──────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", " ", ""],
)


# ── URL mapping ───────────────────────────────────────────────────────────────

def local_path_to_rachel_url(local_path: str) -> str:
    """Convert a local filesystem path to the equivalent RACHEL web URL.

    Example
    -------
    Local  : /app/data/maths/grade7.pdf
    RACHEL : http://rachel-server.local/library/maths/grade7.pdf

    The function strips the configured ``docs_path`` prefix and prepends
    the RACHEL base URL + library path so that every citation becomes a
    clickable link for students.
    """
    relative = os.path.relpath(local_path, settings.docs_path)
    return f"{settings.rachel_url}{settings.rachel_library_path}/{relative}"


# ── Core ingestor logic ───────────────────────────────────────────────────────

def _load_pdf(pdf_path: str) -> List[Document]:
    """Load a single PDF and attach source metadata (including RACHEL URL)."""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    rachel_url = local_path_to_rachel_url(pdf_path)
    for page in pages:
        page.metadata["source"] = pdf_path
        page.metadata["rachel_url"] = rachel_url
    return pages


def ingest_directory(directory: str | None = None) -> int:
    """Ingest all PDFs found recursively under *directory*.

    Parameters
    ----------
    directory:
        Filesystem path to scan.  Defaults to ``settings.docs_path``.

    Returns
    -------
    int
        The total number of document chunks stored in Qdrant.
    """
    directory = directory or settings.docs_path

    # Resolve both paths to absolute forms and verify the requested directory
    # is fully contained within the allowed data root.  Using relative_to()
    # raises ValueError on any path-traversal attempt, and reconstructing
    # safe_dir from the trusted allowed_root cuts the taint chain.
    allowed_root = Path(settings.docs_path).resolve()
    try:
        rel = Path(directory).resolve().relative_to(allowed_root)
    except ValueError:
        raise ValueError(
            f"Directory '{directory}' is outside the allowed data path '{settings.docs_path}'."
        )
    safe_dir = allowed_root / rel

    pdf_files = list(safe_dir.rglob("*.pdf"))

    if not pdf_files:
        return 0

    all_chunks: List[Document] = []
    for pdf_path in pdf_files:
        pages = _load_pdf(str(pdf_path))
        chunks = _splitter.split_documents(pages)
        all_chunks.extend(chunks)

    vector_store = get_vector_store()
    vector_store.add_documents(all_chunks)
    return len(all_chunks)


def ingest_file(pdf_path: str) -> int:
    """Ingest a single PDF file.

    Returns
    -------
    int
        The number of chunks stored.
    """
    pages = _load_pdf(pdf_path)
    chunks = _splitter.split_documents(pages)
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    return len(chunks)
