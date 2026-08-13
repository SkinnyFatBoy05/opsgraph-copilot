"""Stable, heading-aware chunking for policy documents."""

import re
from hashlib import sha256

from opsgraph.retrieval.contracts import DocumentChunk, SourceDocument

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def chunk_document(
    document: SourceDocument,
    *,
    target_tokens: int = 600,
    overlap_tokens: int = 80,
) -> tuple[DocumentChunk, ...]:
    if target_tokens < 1:
        raise ValueError("target_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= target_tokens:
        raise ValueError("overlap_tokens must be smaller than target_tokens")

    sections = _markdown_sections(document.text)
    chunks: list[DocumentChunk] = []
    sequence = 0

    for heading, section_text in sections:
        tokens = section_text.split()
        if not tokens:
            continue
        start = 0
        while start < len(tokens):
            end = min(start + target_tokens, len(tokens))
            text = " ".join(tokens[start:end])
            identity = (
                f"{document.id}:{document.source_hash}:{heading}:{sequence}:{start}:{text}"
            )
            chunk_id = f"chunk-{sha256(identity.encode('utf-8')).hexdigest()}"
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    domain=document.domain,
                    text=text,
                    source_hash=document.source_hash,
                    heading=heading or None,
                    source_uri=document.source_uri,
                    version=document.version,
                    effective_date=document.effective_date,
                    owner=document.owner,
                    metadata=document.metadata,
                )
            )
            sequence += 1
            if end == len(tokens):
                break
            start = end - overlap_tokens

    return tuple(chunks)


def _markdown_sections(text: str) -> tuple[tuple[str, str], ...]:
    headings: list[str] = []
    current_heading = ""
    current_lines: list[str] = []
    sections: list[tuple[str, str]] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_heading, body))

    for line in text.splitlines():
        match = HEADING_PATTERN.match(line)
        if not match:
            current_lines.append(line)
            continue

        flush()
        current_lines = []
        level = len(match.group(1))
        title = match.group(2).strip()
        headings[level - 1 :] = [title]
        current_heading = " / ".join(headings)

    flush()
    return tuple(sections)
