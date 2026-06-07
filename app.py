"""Generation + interface (Milestone 5).

Pipeline stage: Retrieval -> LLM Generation (Groq + sources), see planning.md.

Ties the Milestone 4 retriever to Groq's llama-3.3-70b-versatile. The LLM is
instructed to answer ONLY from the retrieved student reviews; the source list
is assembled programmatically from the retrieved chunks' metadata (never left
to the model to invent). Exposes a Gradio interface.

    python app.py            # launch the web interface
    python app.py --cli      # run the planning.md eval questions in the terminal
"""

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from embed_and_retrieve import retrieve, EVAL_QUESTIONS, TOP_K

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

# Friendly source labels (from the planning.md Documents table) so attribution
# reads as a source name rather than a raw filename. Falls back to the filename.
SOURCE_LABELS = {
    "dobolirmp_cleaned.txt": "Rate My Professors",
    "doboliese124_cleaned.txt": "SBU Course Evaluation — ESE 124",
    "doboliese224_cleaned.txt": "SBU Course Evaluation — ESE 224",
    "doboliese344_cleaned.txt": "SBU Course Evaluation — ESE 344",
    "doboliclasses_cleaned.txt": "Reddit r/SBU — single-student review",
    "dobolireddit1_cleaned.txt": "Reddit r/SBU — teacher rating thread",
    "dobolireddit2_cleaned.txt": "Reddit r/SBU — \"Dear Alex Doboli\" thread",
    "doboliredditgood.txt": "Reddit r/SBU — \"The new ESE 124 Professor\" thread",
    "doboliredditneutral.txt": "Reddit r/SBU — \"ESE124 — Doboli\" thread",
    "alexdooli.txt": "SBU Faculty Page",
}

SYSTEM_PROMPT = """You are an assistant that answers questions about Professor \
Alex Doboli's courses (ESE 124, 224, 344) at Stony Brook University.

Rules:
- Answer using ONLY the student reviews provided in the context. Do not use any \
outside or prior knowledge.
- If the provided reviews do not contain enough information to answer, say exactly: \
"I don't have enough information in the reviews to answer that."
- Be balanced: when the reviews disagree, reflect both the positive and negative \
opinions instead of picking one side.
- Refer to the reviews by their bracketed numbers (e.g. [2]) when you use them.
- Be concise and directly address the question. Do not invent quotes, ratings, \
or sources."""

_client = None


def get_client():
    """Create the Groq client once, validating the API key is present."""
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
                "Groq API key (get one free at https://console.groq.com)."
            )
        _client = Groq(api_key=api_key)
    return _client


def build_context(chunks):
    """Render retrieved chunks as a numbered context block for the prompt."""
    lines = []
    for i, c in enumerate(chunks, start=1):
        label = SOURCE_LABELS.get(c["source"], c["source"])
        lines.append(f"[{i}] (source: {label})\n{c['text']}")
    return "\n\n".join(lines)


def format_sources(chunks):
    """Build the source list programmatically from chunk metadata.

    Numbering matches the [N] markers in the prompt context so the reader can
    trace each cited review back to its document.
    """
    lines = []
    for i, c in enumerate(chunks, start=1):
        label = SOURCE_LABELS.get(c["source"], c["source"])
        # distance is cosine distance (lower = more relevant); show similarity.
        similarity = 1 - c["distance"]
        lines.append(
            f"{i}. **{label}** "
            f"(`{c['chunk_id']}`, relevance {similarity:.2f})"
        )
    return "\n".join(lines)


def answer_question(query, k=TOP_K):
    """Retrieve, generate a grounded answer, and attach the source list.

    Returns (answer_text, sources_markdown, chunks).
    """
    query = (query or "").strip()
    if not query:
        return "Please enter a question.", "", []

    chunks = retrieve(query, k=k)
    if not chunks:
        return "No reviews are indexed yet. Run `python embed_and_retrieve.py` first.", "", []

    context = build_context(chunks)
    user_message = (
        f"Context — student reviews:\n\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer using only the reviews above."
    )

    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    answer = response.choices[0].message.content.strip()

    # Source attribution is guaranteed here, independent of the model output.
    sources_md = format_sources(chunks)
    return answer, sources_md, chunks


# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------

def _gradio_fn(query):
    """Adapter for Gradio: returns (answer, sources) as markdown strings."""
    try:
        answer, sources_md, _ = answer_question(query)
    except RuntimeError as e:
        return f"⚠️ {e}", ""
    sources_block = f"### Sources\n{sources_md}" if sources_md else ""
    return answer, sources_block


def launch_app():
    import gradio as gr

    with gr.Blocks(title="The Unofficial Guide — Professor Doboli") as demo:
        gr.Markdown(
            "# The Unofficial Guide: Professor Alex Doboli\n"
            "Ask about ESE 124 / 224 / 344 with Professor Doboli. Answers are "
            "grounded **only** in real student reviews from Rate My Professors, "
            "SBU course evaluations, and Reddit — with sources cited."
        )
        with gr.Row():
            question = gr.Textbox(
                label="Your question",
                placeholder="e.g. Is ESE 124 with Doboli beginner-friendly?",
                lines=2,
                scale=4,
            )
            ask = gr.Button("Ask", variant="primary", scale=1)

        answer_out = gr.Markdown(label="Answer")
        sources_out = gr.Markdown(label="Sources")

        gr.Examples(examples=[[q] for q in EVAL_QUESTIONS], inputs=question)

        ask.click(_gradio_fn, inputs=question, outputs=[answer_out, sources_out])
        question.submit(_gradio_fn, inputs=question, outputs=[answer_out, sources_out])

    demo.launch()


def run_cli():
    """Run the planning.md evaluation questions through the full pipeline."""
    for q in EVAL_QUESTIONS:
        print("\n" + "=" * 90)
        print(f"Q: {q}")
        print("=" * 90)
        try:
            answer, sources_md, _ = answer_question(q)
        except RuntimeError as e:
            print(f"ERROR: {e}")
            return
        print(answer)
        print("\nSources:")
        print(sources_md)


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        launch_app()
