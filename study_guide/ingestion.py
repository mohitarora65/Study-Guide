from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any, Callable
from uuid import uuid4

from pypdf import PdfReader
import voyageai

from study_guide import database
from study_guide.embeddings import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    EmbeddingProviderError,
    InvalidEmbeddingResponse,
    embed_texts,
)
from study_guide.study_modes import validate_material_type, validate_study_scopes


MAX_PDF_BYTES = 25 * 1024 * 1024
LOW_TEXT_CHAR_LIMIT = 100
CHUNK_CHARS = 2_400
CHUNK_OVERLAP = 250
EMBEDDING_BATCH_TOKEN_LIMIT = 9_800
EMBEDDING_BATCH_ITEM_LIMIT = 128
EMBEDDING_BATCH_DELAY_SECONDS = 61

_VOYAGE_TOKENIZER = voyageai.Client()


class IngestionError(RuntimeError):
    """An operator-safe ingestion failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str
    character_count: int
    low_text: bool


@dataclass(frozen=True)
class Chunk:
    page_number: int
    chunk_order: int
    content: str
    content_hash: str


@dataclass(frozen=True)
class PreparedDocument:
    display_name: str
    content_hash: str
    file_size_bytes: int
    pages: tuple[ExtractedPage, ...]
    chunks: tuple[Chunk, ...]

    @property
    def low_text_pages(self) -> tuple[int, ...]:
        return tuple(page.page_number for page in self.pages if page.low_text)

    @property
    def extracted_character_count(self) -> int:
        return sum(page.character_count for page in self.pages)


@dataclass(frozen=True)
class IngestionOutcome:
    document_id: str
    display_name: str
    chunk_count: int
    duplicate: bool = False


def _safe_display_name(filename: str) -> str:
    name = PurePosixPath(filename.replace("\\", "/")).name.strip()
    if not name or not name.casefold().endswith(".pdf"):
        raise IngestionError("INVALID_FILE", "Choose a file with a .pdf extension.")
    return name


def _chunks_for_page(page_number: int, text: str) -> list[Chunk]:
    units = [
        unit.strip()
        for unit in re.split(
            r"\n\s*\n+|\n(?=\s*(?:[-*•]|\d+[.)])\s)|(?<=[.!?])\s+(?=\S)",
            text,
        )
        if unit.strip()
    ]
    bounded_units = [
        (unit[start : start + CHUNK_CHARS], len(unit) <= CHUNK_CHARS)
        for unit in units
        for start in range(0, len(unit), CHUNK_CHARS)
    ]
    contents: list[str] = []
    current: list[tuple[str, bool]] = []

    for unit, complete in bounded_units:
        if current and len(
            " ".join([text for text, _ in current] + [unit])
        ) > CHUNK_CHARS:
            contents.append(" ".join(text for text, _ in current))
            overlap: list[tuple[str, bool]] = []
            for trailing in reversed(current):
                if not trailing[1] or len(
                    " ".join([trailing[0]] + [text for text, _ in overlap])
                ) > CHUNK_OVERLAP:
                    break
                overlap.insert(0, trailing)
            current = overlap
            if current and len(
                " ".join([text for text, _ in current] + [unit])
            ) > CHUNK_CHARS:
                current = []
        current.append((unit, complete))

    if current:
        contents.append(" ".join(text for text, _ in current))

    return [
        Chunk(
            page_number=page_number,
            chunk_order=chunk_order,
            content=content,
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )
        for chunk_order, content in enumerate(contents)
    ]


def prepare_pdf(filename: str, mime_type: str | None, data: bytes) -> PreparedDocument:
    display_name = _safe_display_name(filename)
    if mime_type and mime_type.casefold() != "application/pdf":
        raise IngestionError("INVALID_FILE", "The selected file is not a PDF.")
    if not data:
        raise IngestionError("EMPTY_FILE", "The selected PDF is empty.")
    if len(data) > MAX_PDF_BYTES:
        raise IngestionError("FILE_TOO_LARGE", "PDFs must be 25 MiB or smaller.")
    if not data.startswith(b"%PDF-"):
        raise IngestionError("INVALID_FILE", "The selected file is not a readable PDF.")

    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise IngestionError("ENCRYPTED_PDF", "Encrypted PDFs are not supported.")
        source_pages = list(reader.pages)
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError("INVALID_PDF", "The selected PDF could not be read.") from exc

    if not source_pages:
        raise IngestionError("EMPTY_PDF", "The selected PDF has no pages.")

    pages: list[ExtractedPage] = []
    chunks: list[Chunk] = []
    try:
        for page_number, page in enumerate(source_pages, start=1):
            text = (page.extract_text() or "").replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()
            character_count = sum(not char.isspace() for char in text)
            pages.append(
                ExtractedPage(
                    page_number=page_number,
                    text=text,
                    character_count=character_count,
                    low_text=character_count < LOW_TEXT_CHAR_LIMIT,
                )
            )
            chunks.extend(_chunks_for_page(page_number, text))
    except Exception as exc:
        raise IngestionError("EXTRACTION_FAILED", "Text could not be extracted from this PDF.") from exc

    if not chunks:
        raise IngestionError(
            "NO_EXTRACTABLE_TEXT",
            "No extractable text was found. Scanned PDFs need OCR, which is not supported yet.",
        )

    return PreparedDocument(
        display_name=display_name,
        content_hash=hashlib.sha256(data).hexdigest(),
        file_size_bytes=len(data),
        pages=tuple(pages),
        chunks=tuple(chunks),
    )


def _is_transient(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    return status is None or status in {
        429,
        500,
        502,
        503,
        504,
    }


def _embedding_token_counts(texts: list[str]) -> list[int]:
    return [
        len(tokens)
        for tokens in _VOYAGE_TOKENIZER.tokenize(texts, model=EMBEDDING_MODEL)
    ]


def _embedding_batches(
    chunks: tuple[Chunk, ...],
    token_counter: Callable[[list[str]], list[int]],
) -> list[tuple[Chunk, ...]]:
    try:
        counts = token_counter([chunk.content for chunk in chunks])
    except Exception as exc:
        raise IngestionError(
            "EMBEDDING_TOKENIZATION_FAILED",
            "The document could not be prepared for embedding. Try again.",
        ) from exc
    if len(counts) != len(chunks) or any(
        not isinstance(count, int) or isinstance(count, bool) or count <= 0
        for count in counts
    ):
        raise IngestionError(
            "EMBEDDING_TOKENIZATION_FAILED",
            "The document could not be prepared for embedding. Try again.",
        )

    batches: list[tuple[Chunk, ...]] = []
    batch: list[Chunk] = []
    batch_tokens = 0
    for chunk, token_count in zip(chunks, counts, strict=True):
        if token_count > EMBEDDING_BATCH_TOKEN_LIMIT:
            raise IngestionError(
                "EMBEDDING_CHUNK_TOO_LARGE",
                "A document section is too large to embed safely.",
            )
        if batch and (
            batch_tokens + token_count > EMBEDDING_BATCH_TOKEN_LIMIT
            or len(batch) == EMBEDDING_BATCH_ITEM_LIMIT
        ):
            batches.append(tuple(batch))
            batch = []
            batch_tokens = 0
        batch.append(chunk)
        batch_tokens += token_count
    if batch:
        batches.append(tuple(batch))
    return batches


def embed_chunks(
    chunks: tuple[Chunk, ...],
    api_key: str,
    *,
    embedder: Callable[..., list[list[float]]] = embed_texts,
    sleep: Callable[[float], None] = time.sleep,
    token_counter: Callable[[list[str]], list[int]] = _embedding_token_counts,
) -> list[list[float]]:
    if not api_key:
        raise IngestionError("VOYAGE_NOT_CONFIGURED", "Voyage is not configured yet.")
    vectors: list[list[float]] = []

    for index, batch in enumerate(_embedding_batches(chunks, token_counter)):
        if index:
            # shortcut: one nearly full TPM batch per rate window.
            sleep(EMBEDDING_BATCH_DELAY_SECONDS)
        for attempt in range(2):
            try:
                vectors.extend(
                    embedder(
                        [chunk.content for chunk in batch],
                        api_key,
                        input_type="document",
                    )
                )
                break
            except InvalidEmbeddingResponse as exc:
                raise IngestionError(
                    "INVALID_EMBEDDING_RESPONSE",
                    "The embedding provider returned an invalid response.",
                ) from exc
            except EmbeddingProviderError as exc:
                if attempt == 0 and _is_transient(exc):
                    # shortcut: Voyage exposes no retry delay here; use one full rate window.
                    sleep(61 if exc.status_code == 429 else 1)
                    continue
                if exc.status_code == 429:
                    raise IngestionError(
                        "EMBEDDING_QUOTA_EXCEEDED",
                        "Voyage embedding allowance or rate limit was exceeded. Retry later or check the account.",
                    ) from exc
                raise IngestionError(
                    "EMBEDDING_FAILED", "The document could not be embedded. Try again."
                ) from exc

    return vectors


def _finish_ingestion(
    client: Any,
    prepared: PreparedDocument,
    api_key: str,
    document_id: str,
    version_id: str,
    run_id: str,
    progress: Callable[[str], None],
) -> IngestionOutcome:
    try:
        progress("Creating embeddings")
        vectors = embed_chunks(prepared.chunks, api_key)
        progress("Saving page-linked chunks")
        database.insert_chunks(
            client,
            [
                {
                    "id": str(uuid4()),
                    "version_id": version_id,
                    "page_number": chunk.page_number,
                    "chunk_order": chunk.chunk_order,
                    "content": chunk.content,
                    "content_hash": chunk.content_hash,
                    "voyage_embedding": vector,
                }
                for chunk, vector in zip(prepared.chunks, vectors, strict=True)
            ],
        )
        progress("Activating the completed version")
        database.activate_version(
            client,
            {
                "p_document_id": document_id,
                "p_version_id": version_id,
                "p_run_id": run_id,
                "p_page_count": len(prepared.pages),
                "p_low_text_pages": list(prepared.low_text_pages),
                "p_extracted_character_count": prepared.extracted_character_count,
                "p_processed_chunks": len(prepared.chunks),
                "p_embedding_model": EMBEDDING_MODEL,
                "p_embedding_dimension": EMBEDDING_DIMENSION,
            },
        )
    except (IngestionError, database.DatabaseError) as exc:
        safe_code = exc.code if isinstance(exc, IngestionError) else "INGESTION_FAILED"
        database.mark_version_failed(
            client, document_id, version_id, run_id, safe_code
        )
        if isinstance(exc, IngestionError):
            raise
        raise IngestionError(
            "INGESTION_FAILED", "The document could not be indexed. Try again."
        ) from exc

    return IngestionOutcome(
        document_id=document_id,
        display_name=prepared.display_name,
        chunk_count=len(prepared.chunks),
    )


def ingest_pdf(
    client: Any,
    api_key: str,
    filename: str,
    mime_type: str | None,
    data: bytes,
    *,
    material_type: str = "theory",
    study_scopes: tuple[str, ...] = ("mid_sem", "end_sem", "quiz"),
    progress: Callable[[str], None] = lambda _message: None,
) -> IngestionOutcome:
    try:
        material_type = validate_material_type(material_type)
        study_scopes = validate_study_scopes(study_scopes)
    except ValueError as exc:
        raise IngestionError("INVALID_CLASSIFICATION", str(exc)) from exc
    progress("Validating and extracting PDF text")
    prepared = prepare_pdf(filename, mime_type, data)
    existing = database.find_document_by_hash(client, prepared.content_hash)
    if existing:
        return IngestionOutcome(
            document_id=existing["id"],
            display_name=existing["display_name"],
            chunk_count=0,
            duplicate=True,
        )

    document_id = str(uuid4())
    version_id = str(uuid4())
    run_id = str(uuid4())
    object_path = f"documents/{document_id}/{prepared.content_hash}.pdf"

    progress("Uploading the private source PDF")
    database.upload_pdf(client, object_path, data)
    try:
        database.create_document_records(
            client,
            document={
                "id": document_id,
                "display_name": prepared.display_name,
                "object_path": object_path,
                "content_hash": prepared.content_hash,
                "file_size_bytes": prepared.file_size_bytes,
                "status": "processing",
                "material_type": material_type,
                "study_scopes": list(study_scopes),
            },
            version={
                "id": version_id,
                "document_id": document_id,
                "version_number": 1,
                "status": "processing",
                "embedding_model": EMBEDDING_MODEL,
                "embedding_dimension": EMBEDDING_DIMENSION,
            },
            run={
                "id": run_id,
                "document_id": document_id,
                "version_id": version_id,
                "retry_key": str(uuid4()),
                "status": "processing",
            },
        )
    except database.DatabaseError:
        database.remove_pdf(client, object_path)
        raise

    return _finish_ingestion(
        client, prepared, api_key, document_id, version_id, run_id, progress
    )


def retry_failed_document(
    client: Any,
    api_key: str,
    document_id: str,
    *,
    progress: Callable[[str], None] = lambda _message: None,
) -> IngestionOutcome:
    # A retry gets current provider metadata instead of reviving an incompatible failed version.
    return reindex_document(client, api_key, document_id, progress=progress)


def reindex_document(
    client: Any,
    api_key: str,
    document_id: str,
    *,
    progress: Callable[[str], None] = lambda _message: None,
) -> IngestionOutcome:
    document = database.get_document(client, document_id)
    progress("Loading and validating the private source PDF")
    data = database.download_pdf(client, document["object_path"])
    prepared = prepare_pdf(document["display_name"], "application/pdf", data)
    if prepared.content_hash != document["content_hash"]:
        raise IngestionError("SOURCE_CHANGED", "The stored source PDF failed validation.")

    version_id = str(uuid4())
    run_id = str(uuid4())
    database.create_version_records(
        client,
        version={
            "id": version_id,
            "document_id": document_id,
            "version_number": database.next_version_number(client, document_id),
            "status": "processing",
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION,
        },
        run={
            "id": run_id,
            "document_id": document_id,
            "version_id": version_id,
            "retry_key": str(uuid4()),
            "status": "processing",
        },
    )
    return _finish_ingestion(
        client, prepared, api_key, document_id, version_id, run_id, progress
    )


def delete_document(client: Any, document_id: str) -> None:
    object_path = database.begin_document_delete(client, document_id)
    database.remove_pdf(client, object_path)
    database.delete_document_record(client, document_id)
