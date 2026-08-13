"""Validated local policy loaders."""

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from opsgraph.contracts.evidence import DomainName
from opsgraph.retrieval.contracts import SourceDocument

MAX_DOCUMENT_BYTES = 1_000_000


def load_markdown_document(path: Path, domain: DomainName) -> SourceDocument:
    if path.suffix.casefold() not in {".md", ".txt"}:
        raise ValueError(f"unsupported document type: {path.suffix}")
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ValueError(f"document exceeds {MAX_DOCUMENT_BYTES} bytes")

    raw = path.read_text(encoding="utf-8")
    metadata, text = _split_front_matter(raw)
    if path.suffix.casefold() == ".md" and metadata.get("synthetic") is not True:
        raise ValueError(f"portfolio policy must declare synthetic: true: {path.name}")

    effective_date = metadata.get("effective_date")
    if isinstance(effective_date, str):
        effective_date = date.fromisoformat(effective_date)
    title = next(
        (line.removeprefix("# ").strip() for line in text.splitlines() if line.startswith("# ")),
        path.stem.replace("-", " ").title(),
    )
    document_id = str(metadata.get("document_id") or path.stem)

    return SourceDocument(
        id=document_id,
        domain=domain,
        text=text.strip(),
        title=title,
        source_uri=path.resolve().as_uri(),
        version=str(metadata["version"]) if "version" in metadata else None,
        effective_date=effective_date,
        owner=metadata.get("owner"),
        metadata={
            key: value.isoformat() if isinstance(value, date) else value
            for key, value in metadata.items()
            if key not in {"document_id", "version", "effective_date", "owner"}
        },
    )


def load_documents(directory: Path, domain: DomainName) -> tuple[SourceDocument, ...]:
    paths = sorted(path for path in directory.iterdir() if path.suffix.casefold() in {".md", ".txt"})
    return tuple(load_markdown_document(path, domain) for path in paths)


def _split_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) != 3:
        raise ValueError("invalid YAML front matter")
    loaded = yaml.safe_load(parts[1]) or {}
    if not isinstance(loaded, dict):
        raise ValueError("front matter must be a mapping")
    return loaded, parts[2]
