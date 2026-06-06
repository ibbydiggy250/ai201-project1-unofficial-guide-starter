"""Embed the review chunks and serve top-k retrieval from ChromaDB.

Pipeline stage: Embedding + Vector Store -> Retrieval (see planning.md).

- Embeds every chunk in data/chunks.json with all-MiniLM-L6-v2.
- Stores them in a persistent ChromaDB collection with metadata
  (source filename + the chunk's position within its document).
- Exposes retrieve(query, k=5) which returns the top-k most relevant
  chunks with their text, source, position, and cosine distance.

Run directly to (re)build the index and see retrieval on the planning.md
evaluation questions:  python embed_and_retrieve.py
"""

import os

# transformers tries to import TensorFlow/Keras on startup; Keras 3 is
# incompatible with this transformers version. Force the PyTorch backend.
os.environ.setdefault("USE_TF", "0")

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent
CHUNKS_PATH = ROOT / "data" / "chunks.json"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "doboli_reviews"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5

# Cache the model so we don't reload it per call.
_model = None


def get_model():
    """Load the embedding model once and reuse it."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def position_in_document(chunk_id):
    """Recover a chunk's position within its source doc from its id.

    chunk_id is formatted as "<filename>_NNN" (e.g. "dobolirmp_cleaned_005"),
    so the trailing number is the 1-based position within that document.
    """
    tail = chunk_id.rsplit("_", 1)[-1]
    return int(tail) if tail.isdigit() else -1


def build_index():
    """Embed all chunks and (re)build the ChromaDB collection from scratch."""
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    model = get_model()

    texts = [c["text"] for c in chunks]
    # Normalize so cosine distance behaves nicely in Chroma.
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Drop any prior collection so re-runs are deterministic.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {
                "source": c["source"],
                "chunk_id": c["chunk_id"],
                "position": position_in_document(c["chunk_id"]),
            }
            for c in chunks
        ],
    )

    print(f"Indexed {collection.count()} chunks into '{COLLECTION_NAME}' at {CHROMA_DIR}")
    return collection


def get_collection():
    """Open the persisted collection (assumes build_index has been run)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION_NAME)


def retrieve(query, k=TOP_K, collection=None):
    """Return the top-k most relevant chunks for a query.

    Each result is a dict with: text, source, chunk_id, position, distance
    (cosine distance — lower is more similar).
    """
    if collection is None:
        collection = get_collection()
    model = get_model()

    query_embedding = model.encode([query], normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=query_embedding, n_results=k)

    results = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append(
            {
                "text": doc,
                "source": meta["source"],
                "chunk_id": meta["chunk_id"],
                "position": meta["position"],
                "distance": dist,
            }
        )
    return results


# Evaluation questions from planning.md, used as a smoke test.
EVAL_QUESTIONS = [
    "What are students' general opinion on Professor Doboli?",
    "Is ESE 124 with Doboli beginner-friendly?",
    "What are the biggest complaints about Professor Doboli's classes?",
    "How do students compare ESE 224 and 124 with Professor Doboli?",
    "What is valuable about ESE 124 with Professor Doboli?",
]


def _preview(text, width=160):
    text = " ".join(text.split())  # collapse newlines for a compact preview
    return text if len(text) <= width else text[: width - 1] + "…"


def main():
    collection = build_index()

    for question in EVAL_QUESTIONS:
        print("\n" + "=" * 90)
        print(f"QUERY: {question}")
        print("=" * 90)
        for rank, r in enumerate(retrieve(question, collection=collection), start=1):
            print(
                f"{rank}. [{r['source']} #{r['position']}]  "
                f"distance={r['distance']:.4f}  id={r['chunk_id']}"
            )
            print(f"   {_preview(r['text'])}")


if __name__ == "__main__":
    main()
