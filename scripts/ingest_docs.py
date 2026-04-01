"""scripts/ingest_docs.py – CLI script to ingest the RACHEL /library/.

Run this script (inside the container or on your laptop) to bulk-load all
PDFs from the school's RACHEL server into Qdrant:

    python scripts/ingest_docs.py --directory /path/to/rachel/library

When running via docker-compose the data directory is mounted at
/app/data, so the default path works without any flags:

    docker-compose run --rm ai-backend python scripts/ingest_docs.py
"""
import argparse
import sys
import os

# Ensure the project root is on sys.path so `app` can be imported directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.ingestor import ingest_directory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest PDF documents from the RACHEL library into Qdrant."
    )
    parser.add_argument(
        "--directory",
        default=settings.docs_path,
        help=(
            "Path to the folder containing PDF files to ingest. "
            f"Defaults to '{settings.docs_path}'."
        ),
    )
    args = parser.parse_args()

    print(f"Scanning '{args.directory}' for PDF files …")
    total_chunks = ingest_directory(args.directory)

    if total_chunks == 0:
        print("No PDF files found. Nothing was ingested.")
    else:
        print(f"Done! {total_chunks} text chunks stored in Qdrant.")


if __name__ == "__main__":
    main()
