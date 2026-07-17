"""Keyword search over the local sales-enablement markdown files.

The corpus is ~8 short docs (~45KB total) — small enough that a simple
word-overlap ranking over header-delimited chunks is plenty, and it keeps
the whole thing dependency-free and inspectable (no embeddings/vector DB).
Swapping in real vector search is a documented follow-up, not a blocker
for a prototype this size.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ENABLEMENT_DIR = Path(__file__).resolve().parent.parent / "data" / "enablement"

_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass
class Chunk:
    source: str
    heading: str
    text: str


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _load_chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in ENABLEMENT_DIR.rglob("*.md"):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        doc_title = title_match.group(1).strip() if title_match else path.stem

        sections = re.split(r"^##\s+(.+)$", text, flags=re.MULTILINE)
        # sections[0] is preamble before the first "## " heading
        if sections[0].strip():
            chunks.append(Chunk(source=doc_title, heading="(intro)", text=sections[0].strip()))
        for i in range(1, len(sections), 2):
            heading = sections[i].strip()
            body = sections[i + 1].strip() if i + 1 < len(sections) else ""
            if body:
                chunks.append(Chunk(source=doc_title, heading=heading, text=body))
    return chunks


_CHUNKS_CACHE: list[Chunk] | None = None


def _chunks() -> list[Chunk]:
    global _CHUNKS_CACHE
    if _CHUNKS_CACHE is None:
        _CHUNKS_CACHE = _load_chunks()
    return _CHUNKS_CACHE


def search_enablement(query: str, top_k: int = 3) -> list[dict]:
    """Return the top_k chunks most relevant to the query, by word overlap."""
    query_words = _tokenize(query)
    if not query_words:
        return []

    scored = []
    for chunk in _chunks():
        chunk_words = _tokenize(f"{chunk.source} {chunk.heading} {chunk.text}")
        overlap = len(query_words & chunk_words)
        if overlap:
            scored.append((overlap, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {"source": c.source, "section": c.heading, "text": c.text}
        for _, c in scored[:top_k]
    ]
