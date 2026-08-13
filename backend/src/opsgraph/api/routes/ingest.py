"""Authenticated local-only document ingestion."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile
from pypdf import PdfReader

from opsgraph.api.dependencies import (
    AppServices,
    get_services,
    get_settings_from_request,
)
from opsgraph.api.schemas import IngestionResponse
from opsgraph.config import Settings
from opsgraph.retrieval.contracts import SourceDocument

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


@router.post("/bankops/ingest", response_model=IngestionResponse)
async def ingest_bankops(
    file: UploadFile,
    x_local_admin_token: str | None = Header(default=None),
    services: AppServices = Depends(get_services),
    settings: Settings = Depends(get_settings_from_request),
) -> IngestionResponse:
    if x_local_admin_token != settings.local_admin_token:
        raise HTTPException(status_code=401, detail="Invalid local administration token")

    filename = Path(file.filename or "upload.txt").name
    suffix = Path(filename).suffix.casefold()
    if suffix not in {".md", ".txt", ".pdf"}:
        raise HTTPException(status_code=415, detail="Only Markdown, text, and PDF are accepted")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Document is too large")

    if suffix == ".pdf":
        try:
            reader = PdfReader(BytesIO(content))
        except Exception as error:
            raise HTTPException(status_code=422, detail="PDF could not be parsed") from error
        if len(reader.pages) > settings.max_pdf_pages:
            raise HTTPException(status_code=413, detail="PDF has too many pages")
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise HTTPException(status_code=422, detail="Text must be UTF-8") from error

    if not text.strip():
        raise HTTPException(status_code=422, detail="Document contains no extractable text")
    source_hash = sha256(content).hexdigest()
    source_id = f"upload-{source_hash[:20]}"
    chunk_count = await services.ingest(
        SourceDocument(
            id=source_id,
            domain="bankops",
            text=text,
            title=Path(filename).stem,
            source_uri=f"local-upload://{source_id}/{filename}",
            metadata={"synthetic": True, "uploaded": True},
        )
    )
    return IngestionResponse(
        source_id=source_id,
        source_hash=source_hash,
        chunk_count=chunk_count,
    )
