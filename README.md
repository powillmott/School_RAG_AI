# School RAG AI

A **Retrieval-Augmented Generation (RAG)** backend that connects a school's
[RACHEL](https://rachel.worldpossible.org/) digital library to a local LLM
(Ollama on a laptop, or a DGX Spark in production) via a Qdrant vector
database.  Students ask questions and receive answers that are grounded in
the school's own textbooks, with clickable "Read More" links pointing back
to the source document on the RACHEL server.

---

## Project Structure

```
school-ai-project/
├── app/
│   ├── main.py          # FastAPI entry point
│   ├── api/
│   │   └── routes.py    # API routes: /ask, /ingest/directory, /ingest/file
│   ├── core/
│   │   └── config.py    # URL & env-var configs (LLM, Qdrant, RACHEL)
│   ├── services/
│   │   ├── ingestor.py  # PDF loading, text splitting, URL mapping
│   │   └── rag_chain.py # LangChain RetrievalQA chain with citations
│   └── db/
│       └── qdrant_client.py  # Vector DB connection & collection setup
├── scripts/
│   └── ingest_docs.py   # CLI script to bulk-ingest the RACHEL library
├── data/                # Mount your sample PDFs here (git-ignored)
├── Dockerfile
├── docker-compose.yml   # Starts ai-backend, Qdrant, and Ollama in one command
├── requirements.txt
└── README.md
```

---

## Quick Start (Laptop / Local Development)

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
* No other setup required – Docker pulls everything else automatically

### 1 – Clone and configure

```bash
git clone https://github.com/powillmott/School_RAG_AI.git
cd School_RAG_AI

# (Optional) override defaults in a local .env file – never commit this file
cp .env.example .env   # edit as needed
```

### 2 – Add sample PDFs

Drop any PDF textbooks into the `data/` folder.  They will be mounted into
the container at `/app/data`.

### 3 – Start all services

```bash
docker-compose up --build
```

This starts:
| Service | What it does | Default port |
|---|---|---|
| `ai-backend` | FastAPI + LangChain RAG app | 8000 |
| `qdrant` | Vector database | 6333 |
| `ollama-service` | Local LLM inference | 11434 |

### 4 – Pull a model into Ollama

```bash
docker-compose exec ollama-service ollama pull llama3
```

### 5 – Ingest your documents

```bash
# Ingest everything in data/
docker-compose exec ai-backend python scripts/ingest_docs.py

# Or POST to the API
curl -X POST http://localhost:8000/api/v1/ingest/directory
```

### 6 – Ask a question

```bash
curl -X POST http://localhost:8000/api/v1/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What is photosynthesis?"}'
```

**Response:**

```json
{
  "answer": "Photosynthesis is the process by which plants …",
  "citations": [
    {
      "title": "/app/data/biology/grade8.pdf",
      "page": 42,
      "url": "http://rachel-server.local/library/biology/grade8.pdf"
    }
  ]
}
```

### Interactive API docs

Open <http://localhost:8000/docs> in your browser for the full Swagger UI.

---

## Deploying to India (DGX Spark / RACHEL server)

### Swapping the LLM endpoint

When the DGX Spark is available, update one environment variable in
`docker-compose.yml` (or your `.env` file):

```yaml
- LLM_BASE_URL=http://<DGX_SPARK_IP>:11434/v1
```

The `ollama-service` container can then be removed from `docker-compose.yml`
since inference runs on the Spark.

### Offline USB-drive installation

If the internet is unreliable, save all Docker images before you leave:

```bash
# Save images to a tar file (run on your laptop before the trip)
docker save \
  $(docker-compose config --images) \
  -o school_ai_images.tar

# On the school server – load from USB
docker load -i school_ai_images.tar
docker-compose up -d
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `POST` | `/api/v1/ask` | Answer a question with citations |
| `POST` | `/api/v1/ingest/directory` | Ingest all PDFs in `data/` |
| `POST` | `/api/v1/ingest/file` | Upload and ingest a single PDF |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_BASE_URL` | `http://ollama-service:11434/v1` | OpenAI-compatible LLM endpoint |
| `LLM_MODEL` | `llama3` | Model name passed to the LLM |
| `VECTOR_DB_URL` | `http://qdrant:6333` | Qdrant server URL |
| `VECTOR_COLLECTION` | `school_docs` | Qdrant collection name |
| `RACHEL_URL` | `http://rachel-server.local` | Base URL of the RACHEL server |
| `RACHEL_LIBRARY_PATH` | `/library` | Library sub-path on RACHEL |
| `DOCS_PATH` | `/app/data` | Local path where PDFs are stored |

---

## .gitignore Highlights

The following are **never** committed:

* `qdrant_storage/` – vector database files
* `data/*.pdf` – school documents
* `.env` – secrets and API keys
* `__pycache__/` – Python bytecode
