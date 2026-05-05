from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.config import settings
from services.ev_catalog import build_vehicle_text, load_excel_as_documents, save_documents
from services.embeddings import embed_texts
from services.faiss_store import FaissStore


def main() -> None:
    skip_embeddings = "--skip-embeddings" in sys.argv
    documents = load_excel_as_documents(settings.EV_EXCEL_PATH)
    if not documents:
        raise RuntimeError("No vehicle rows were parsed from the Excel dataset.")

    print(f"Loaded {len(documents)} vehicles from Excel")
    save_documents(documents, settings.EV_JSON_PATH)
    print(f"Saved structured JSON to {settings.EV_JSON_PATH}")

    if skip_embeddings:
        print("Skipped embedding and FAISS rebuild; existing index files were left unchanged.")
        return

    payloads = [document.content or build_vehicle_text(document) for document in documents]
    vectors = embed_texts(payloads)
    print(f"Generated {len(vectors)} local embeddings using BAAI/bge-small-en-v1.5")

    store = FaissStore.build(vectors=vectors, ids=[document.id for document in documents])
    store.save(settings.EV_FAISS_INDEX_PATH, settings.EV_FAISS_META_PATH)
    print(f"Saved FAISS index to {settings.EV_FAISS_INDEX_PATH}")
    print(f"Saved index metadata to {settings.EV_FAISS_META_PATH}")


if __name__ == "__main__":
    main()
