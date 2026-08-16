"""
Chunk bit_jaipur_data.json into semantically-sized text chunks using
semantic_text_splitter's TextSplitter, tokenized against the OpenAI
gpt-3.5-turbo tiktoken encoding, preserving source metadata for each chunk.

Install:
    pip install semantic-text-splitter tiktoken

Usage:
    python chunk_data_tiktoken.py
"""

import json
import re
from pathlib import Path

import tiktoken
from semantic_text_splitter import TextSplitter

BASE_DIR = Path(__file__).parent
INPUT_PATH = BASE_DIR / "data" / "bit_jaipur_data.json"
OUTPUT_PATH = BASE_DIR / "data" / "bit_jaipur_chunks.json"

# Tokenizer model to size chunks against (matches the screenshot).
TOKENIZER_MODEL = "gpt-3.5-turbo"

# Max tokens allowed per chunk.
MAX_TOKENS = 1000

# Overlap between consecutive chunks, expressed as a fraction of
# MAX_TOKENS rather than a fixed number -- this way it automatically
# scales if you tune MAX_TOKENS later. 20% is a common default for
# RAG chunking (enough to preserve a sentence/fact split across a
# boundary, without duplicating most of the chunk).
OVERLAP_RATIO = 0.20
OVERLAP_TOKENS = int(MAX_TOKENS * OVERLAP_RATIO)

# Any chunk shorter than this (in words) is merged into a neighboring
# chunk instead of being emitted on its own. Prevents near-empty
# fragments (bare headings, stray URLs) that carry no retrievable
# meaning by themselves.
MIN_CHUNK_WORDS = 10

# Some source PDFs repeat a running header + "Page N of M" on every page
# (fee structure sheets, placement data, department publication lists,
# etc). Generic character/token splitting cuts straight through these,
# separating a section's identifying heading (e.g. "B.Tech. (CSE, AI ML)")
# from its own table/numbers -- which then looks nearly identical to
# every OTHER program's numbers-only fragment once embedded, causing
# retrieval to surface the wrong program. To prevent this, any document
# containing 2+ "Page N of M" markers is first split on those markers so
# each page's heading stays attached to its own content, before the
# normal token splitter is applied (only to individual sections that are
# still too long).
PAGE_MARKER_RE = re.compile(r"(?=Page\s+\d+\s+of\s+\d+)", re.IGNORECASE)

# A section is allowed to run up to this multiple of MAX_TOKENS before
# it gets subdivided further (by the normal token splitter, applied only
# within that section -- never crossing into a different page/program).
SECTION_MAX_TOKEN_MULTIPLIER = 1.5

try:
    _TOKEN_ENCODER = tiktoken.encoding_for_model(TOKENIZER_MODEL)
except Exception as e:
    # tiktoken downloads its encoding table over HTTP on first use and
    # caches it locally after -- if that fails (offline, blocked network),
    # fall back to a word-count approximation for the section-size check
    # below. This only affects the "is this section short enough to keep
    # whole" decision, not the actual token-precise chunking, which is
    # handled separately by semantic_text_splitter's bundled tokenizer.
    print(f"⚠️  Could not load tiktoken encoder ({e}); falling back to word-count approximation for section sizing.")
    _TOKEN_ENCODER = None


def count_tokens(text: str) -> int:
    if _TOKEN_ENCODER is not None:
        return len(_TOKEN_ENCODER.encode(text))
    return int(len(text.split()) * 1.3)  # rough words-to-tokens approximation


def split_into_page_sections(content: str) -> list[str]:
    """Split on 'Page N of M' markers so each page's heading stays with
    its own content. Returns [content] unchanged if there are fewer than
    2 markers (a single marker isn't a real multi-section pattern)."""
    positions = [m.start() for m in PAGE_MARKER_RE.finditer(content)]
    if len(positions) < 2:
        return [content]

    sections = []
    if positions[0] > 0:
        sections.append(content[:positions[0]])
    for i, start in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(content)
        sections.append(content[start:end])
    return [s for s in sections if s.strip()]


def build_splitter(model: str, max_tokens: int, overlap_tokens: int) -> TextSplitter:
    # from_tiktoken_model sizes chunks by actual token count for the
    # given OpenAI model's encoding, and tries to break on
    # paragraph/sentence/word boundaries before ever hard-cutting.
    return TextSplitter.from_tiktoken_model(model, max_tokens, overlap=overlap_tokens)


def merge_small_chunks(text_chunks: list[str], min_words: int) -> list[str]:
    """Merge any chunk with fewer than `min_words` words into a neighbor.

    Strategy: walk left-to-right. If a chunk is too small, glue it onto
    the *next* chunk (headings/short lead-ins usually precede their
    content), unless it's the last chunk, in which case glue it onto the
    previous one. No content is ever dropped.
    """
    if not text_chunks:
        return text_chunks

    merged: list[str] = []
    i = 0
    n = len(text_chunks)

    while i < n:
        current = text_chunks[i]

        if len(current.split()) < min_words:
            if i + 1 < n:
                text_chunks[i + 1] = current.rstrip() + "\n" + text_chunks[i + 1].lstrip()
                i += 1
                continue
            elif merged:
                merged[-1] = merged[-1].rstrip() + "\n" + current.lstrip()
                i += 1
                continue
            # else: it's the only chunk in the document -- keep it as-is.

        merged.append(current)
        i += 1

    return merged


def chunk_documents(
    input_path: Path,
    output_path: Path,
    model: str,
    max_tokens: int,
    overlap_tokens: int,
    min_chunk_words: int,
) -> None:
    with input_path.open("r", encoding="utf-8") as f:
        documents = json.load(f)

    splitter = build_splitter(model, max_tokens, overlap_tokens)
    chunks = []

    for doc in documents:
        content = doc.get("content", "")
        if not content.strip():
            continue

        sections = split_into_page_sections(content)
        text_chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if count_tokens(section) <= max_tokens * SECTION_MAX_TOKEN_MULTIPLIER:
                # Whole section fits comfortably in one chunk -- keep the
                # heading and its content together, don't split further.
                text_chunks.append(section)
            else:
                # Section is unusually long even on its own -- subdivide,
                # but only within this section, never crossing into a
                # different page/program.
                text_chunks.extend(splitter.chunks(section))

        text_chunks = merge_small_chunks(text_chunks, min_chunk_words)

        for i, chunk_text in enumerate(text_chunks):
            chunks.append(
                {
                    "chunk_id": f"{doc['relative_path']}::chunk_{i}",
                    "file_name": doc.get("file_name"),
                    "relative_path": doc.get("relative_path"),
                    "category": doc.get("category"),
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "content": chunk_text,
                }
            )

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(chunks)} chunks from {len(documents)} documents to {output_path}")


if __name__ == "__main__":
    chunk_documents(
        INPUT_PATH,
        OUTPUT_PATH,
        TOKENIZER_MODEL,
        MAX_TOKENS,
        OVERLAP_TOKENS,
        MIN_CHUNK_WORDS,
    )