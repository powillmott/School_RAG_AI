"""app/services/rag_chain.py – LangChain RAG chain with source citations.

Builds a ``RetrievalQA`` chain that:
* Retrieves the most relevant chunks from Qdrant.
* Passes them to the LLM together with the student's question.
* Returns both the answer *and* the source documents so the UI can show
  "Read More" links pointing to the RACHEL server.
"""
from typing import Any, Dict, List

from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.db.qdrant_client import get_vector_store


def _build_chain() -> RetrievalQA:
    """Construct and return a fresh RetrievalQA chain."""
    llm = ChatOpenAI(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        # Ollama / local endpoints do not require a real key.
        api_key="ollama",
        temperature=0,
    )

    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )


def _format_citations(source_docs: List[Document]) -> List[Dict[str, Any]]:
    """Turn LangChain source documents into serialisable citation dicts."""
    seen: set[str] = set()
    citations: List[Dict[str, Any]] = []
    for doc in source_docs:
        meta = doc.metadata
        url = meta.get("rachel_url", meta.get("source", ""))
        if url in seen:
            continue
        seen.add(url)
        citations.append(
            {
                "title": meta.get("source", "Unknown source"),
                "page": meta.get("page", None),
                "url": url,
            }
        )
    return citations


def ask(question: str) -> Dict[str, Any]:
    """Run the RAG chain and return the answer with citations.

    Parameters
    ----------
    question:
        The student's question in plain text.

    Returns
    -------
    dict with keys:
        ``answer``    – The LLM's answer string.
        ``citations`` – List of dicts with ``title``, ``page``, and ``url``.
    """
    chain = _build_chain()
    result = chain.invoke({"query": question})

    return {
        "answer": result["result"],
        "citations": _format_citations(result.get("source_documents", [])),
    }
