"""Chunk cleaned review documents into a JSON file for downstream use.

Reads every .txt file in the `documents/` folder, splits each on a line
containing only `---`, drops chunks shorter than 20 words, and writes the
result to `data/chunks.json`.
"""

import json
import random
from pathlib import Path

# Resolve paths relative to this script so it runs from anywhere.
ROOT = Path(__file__).resolve().parent
DOCUMENTS_DIR = ROOT / "documents"
OUTPUT_PATH = ROOT / "data" / "chunks.json"

MIN_WORDS = 20
SEPARATOR = "---"
NUM_SAMPLES = 5


def strip_file_headers(text):
    """Drop file-level boilerplate header lines (single `#`) from a chunk.

    Keeps `##`/`###` lines such as "## ESE 224 — Professor Doboli" because the
    course context is useful for retrieval; removes lines like
    "# Source: ..." / "# Overall Quality: ..." that are per-document boilerplate.
    """
    kept_lines = [
        line
        for line in text.splitlines()
        if not (line.lstrip().startswith("#") and not line.lstrip().startswith("##"))
    ]
    return "\n".join(kept_lines).strip()


def load_chunks():
    """Build the list of chunk dicts from all .txt files in documents/."""
    chunks = []

    for txt_path in sorted(DOCUMENTS_DIR.glob("*.txt")):
        filename = txt_path.stem  # filename without extension, e.g. "dobolirmp_cleaned"
        text = txt_path.read_text(encoding="utf-8")

        # Split on lines that contain only the separator.
        raw_chunks = text.split(f"\n{SEPARATOR}\n")

        kept = 0
        for raw in raw_chunks:
            chunk_text = strip_file_headers(raw.strip())
            if len(chunk_text.split()) < MIN_WORDS:
                continue  # too short to be meaningful

            kept += 1
            chunks.append(
                {
                    "text": chunk_text,
                    "source": txt_path.name,
                    "chunk_id": f"{filename}_{kept:03d}",
                }
            )

    return chunks


def main():
    chunks = load_chunks()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Summary
    counts = {}
    for chunk in chunks:
        counts[chunk["source"]] = counts.get(chunk["source"], 0) + 1

    print(f"Total chunks produced: {len(chunks)}")
    print(f"Saved to: {OUTPUT_PATH}")
    print("\nChunks per source file:")
    for source in sorted(counts):
        print(f"  {source}: {counts[source]}")

    # Random sample for verification (per the inspection checkpoint).
    print("\n" + "=" * 70)
    print(f"{NUM_SAMPLES} RANDOM SAMPLE CHUNKS")
    print("=" * 70)
    sample = random.sample(chunks, min(NUM_SAMPLES, len(chunks)))
    for chunk in sample:
        print(f"\n[{chunk['chunk_id']}]  (source: {chunk['source']})")
        print("-" * 70)
        print(chunk["text"])


if __name__ == "__main__":
    main()
