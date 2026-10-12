import pytest

import study_guide.ingestion as ingestion
from study_guide import database
from study_guide.embeddings import EmbeddingProviderError, InvalidEmbeddingResponse
from study_guide.ingestion import (
    Chunk,
    ExtractedPage,
    IngestionError,
    PreparedDocument,
    delete_document,
    embed_chunks,
    ingest_pdf,
    prepare_pdf,
    reindex_document,
    retry_failed_document,
)


class Page:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class Reader:
    def __init__(self, _stream: object, *, strict: bool) -> None:
        assert strict is False
        self.is_encrypted = False
        self.pages = [Page("a" * 3_000), Page("short")]


def test_prepares_page_bounded_chunks_and_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "PdfReader", Reader)

    prepared = prepare_pdf("folder/notes.PDF", "application/pdf", b"%PDF-example")

    assert prepared.display_name == "notes.PDF"
    assert len(prepared.pages) == 2
    assert prepared.low_text_pages == (2,)
    assert [chunk.page_number for chunk in prepared.chunks] == [1, 1, 2]
    assert [chunk.chunk_order for chunk in prepared.chunks] == [0, 1, 0]
    assert all(len(chunk.content) <= ingestion.CHUNK_CHARS for chunk in prepared.chunks)
    assert "".join(chunk.content for chunk in prepared.chunks[:2]) == "a" * 3_000
    assert len(prepared.content_hash) == 64


def test_structural_chunks_preserve_complete_sentence_overlap() -> None:
    sentences = [f"Sentence {index} " + "x" * 90 + "." for index in range(30)]

    chunks = ingestion._chunks_for_page(7, " ".join(sentences))

    assert len(chunks) == 2
    assert all(chunk.page_number == 7 for chunk in chunks)
    assert all(len(chunk.content) <= ingestion.CHUNK_CHARS for chunk in chunks)
    assert chunks[0].content.endswith(".")
    assert chunks[1].content.endswith(".")
    overlap_length = max(
        length
        for length in range(1, ingestion.CHUNK_OVERLAP + 1)
        if chunks[0].content.endswith(chunks[1].content[:length])
    )
    overlap = chunks[1].content[:overlap_length]
    assert overlap.startswith("Sentence")
    assert overlap.endswith(".")


def test_structural_chunks_hard_split_oversized_unbroken_text() -> None:
    text = "x" * (ingestion.CHUNK_CHARS * 2 + 5)

    chunks = ingestion._chunks_for_page(1, text)

    assert [len(chunk.content) for chunk in chunks] == [
        ingestion.CHUNK_CHARS,
        ingestion.CHUNK_CHARS,
        5,
    ]
    assert "".join(chunk.content for chunk in chunks) == text


@pytest.mark.parametrize(
    ("filename", "mime", "data", "code"),
    [
        ("notes.txt", "application/pdf", b"%PDF-x", "INVALID_FILE"),
        ("notes.pdf", "text/plain", b"%PDF-x", "INVALID_FILE"),
        ("notes.pdf", "application/pdf", b"", "EMPTY_FILE"),
        ("notes.pdf", "application/pdf", b"not-pdf", "INVALID_FILE"),
        ("notes.pdf", "application/pdf", b"%PDF-" + b"x" * ingestion.MAX_PDF_BYTES, "FILE_TOO_LARGE"),
    ],
)
def test_rejects_invalid_uploads(filename: str, mime: str, data: bytes, code: str) -> None:
    with pytest.raises(IngestionError) as error:
        prepare_pdf(filename, mime, data)
    assert error.value.code == code


def test_rejects_encrypted_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    class EncryptedReader(Reader):
        def __init__(self, stream: object, *, strict: bool) -> None:
            super().__init__(stream, strict=strict)
            self.is_encrypted = True

    monkeypatch.setattr(ingestion, "PdfReader", EncryptedReader)
    with pytest.raises(IngestionError) as error:
        prepare_pdf("notes.pdf", "application/pdf", b"%PDF-x")
    assert error.value.code == "ENCRYPTED_PDF"


def test_rejects_pdf_without_extractable_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class EmptyReader(Reader):
        def __init__(self, stream: object, *, strict: bool) -> None:
            super().__init__(stream, strict=strict)
            self.pages = [Page("   ")]

    monkeypatch.setattr(ingestion, "PdfReader", EmptyReader)
    with pytest.raises(IngestionError) as error:
        prepare_pdf("notes.pdf", None, b"%PDF-x")
    assert error.value.code == "NO_EXTRACTABLE_TEXT"


def _chunk(text: str = "course text") -> Chunk:
    return Chunk(1, 0, text, "hash")


def test_embeds_in_fixed_batches_and_dimension() -> None:
    calls: list[tuple[list[str], str, str]] = []

    def embedder(
        texts: list[str], api_key: str, *, input_type: str
    ) -> list[list[float]]:
        calls.append((texts, api_key, input_type))
        return [[0.1] * 1024 for _ in texts]

    vectors = embed_chunks(
        tuple(_chunk(str(index)) for index in range(33)),
        "key",
        embedder=embedder,
    )

    assert len(calls) == 2
    assert calls[0][1:] == ("key", "document")
    assert len(vectors[0]) == 1024
    assert len(vectors) == 33


def test_retries_one_transient_embedding_failure() -> None:
    attempts = 0

    def embedder(*_args: object, **_kwargs: object) -> list[list[float]]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise EmbeddingProviderError()
        return [[0.1] * 1024]

    assert len(
        embed_chunks(
            (_chunk(),),
            "key",
            embedder=embedder,
            sleep=lambda _seconds: None,
        )
    ) == 1
    assert attempts == 2


def test_reports_exhausted_embedding_quota_after_retry() -> None:
    attempts = 0
    delays: list[float] = []

    def embedder(*_args: object, **_kwargs: object) -> list[list[float]]:
        nonlocal attempts
        attempts += 1
        raise EmbeddingProviderError(status_code=429)

    with pytest.raises(IngestionError) as error:
        embed_chunks(
            (_chunk(),),
            "key",
            embedder=embedder,
            sleep=delays.append,
        )

    assert attempts == 2
    assert delays == [61]
    assert error.value.code == "EMBEDDING_QUOTA_EXCEEDED"
    assert "private provider detail" not in str(error.value)


def test_does_not_retry_non_transient_embedding_failure() -> None:
    attempts = 0

    def embedder(*_args: object, **_kwargs: object) -> list[list[float]]:
        nonlocal attempts
        attempts += 1
        raise EmbeddingProviderError(status_code=401)

    with pytest.raises(IngestionError) as error:
        embed_chunks((_chunk(),), "key", embedder=embedder)

    assert attempts == 1
    assert error.value.code == "EMBEDDING_FAILED"


def test_invalid_embedding_dimension_fails_safely() -> None:
    def embedder(*_args: object, **_kwargs: object) -> list[list[float]]:
        raise InvalidEmbeddingResponse()

    with pytest.raises(IngestionError, match="invalid response") as error:
        embed_chunks((_chunk(),), "key", embedder=embedder)
    assert str(error.value) == "The embedding provider returned an invalid response."


def _prepared() -> PreparedDocument:
    return PreparedDocument(
        display_name="notes.pdf",
        content_hash="a" * 64,
        file_size_bytes=10,
        pages=(ExtractedPage(1, "course text", 10, True),),
        chunks=(_chunk(),),
    )


def test_duplicate_upload_does_not_create_or_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: _prepared())
    monkeypatch.setattr(
        database,
        "find_document_by_hash",
        lambda *_args: {"id": "existing", "display_name": "notes.pdf", "status": "ready"},
    )
    monkeypatch.setattr(
        database,
        "upload_pdf",
        lambda *_args: pytest.fail("duplicate must not be uploaded"),
    )

    result = ingest_pdf(object(), "key", "notes.pdf", "application/pdf", b"data")

    assert result.duplicate is True
    assert result.document_id == "existing"


def test_completed_ingestion_activates_only_after_chunks_are_stored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    stored: dict[str, object] = {}
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: _prepared())
    monkeypatch.setattr(database, "find_document_by_hash", lambda *_args: None)
    monkeypatch.setattr(database, "upload_pdf", lambda *_args: events.append("upload"))
    monkeypatch.setattr(
        database, "create_document_records", lambda *_args, **_kwargs: events.append("records")
    )
    monkeypatch.setattr(ingestion, "embed_chunks", lambda *_args: [[0.1] * 1024])
    def insert_chunks(_client: object, rows: list[dict[str, object]]) -> None:
        stored["rows"] = rows
        events.append("chunks")

    monkeypatch.setattr(database, "insert_chunks", insert_chunks)
    monkeypatch.setattr(
        database, "activate_version", lambda *_args: events.append("activate")
    )

    result = ingest_pdf(object(), "key", "notes.pdf", "application/pdf", b"data")

    assert result.chunk_count == 1
    assert events == ["upload", "records", "chunks", "activate"]
    rows = stored["rows"]
    assert isinstance(rows, list)
    assert len(rows[0]["voyage_embedding"]) == 1024  # type: ignore[arg-type,index]
    assert "embedding" not in rows[0]


def test_ingestion_persists_material_classification(monkeypatch: pytest.MonkeyPatch) -> None:
    saved: dict[str, object] = {}
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: _prepared())
    monkeypatch.setattr(database, "find_document_by_hash", lambda *_args: None)
    monkeypatch.setattr(database, "upload_pdf", lambda *_args: None)
    monkeypatch.setattr(
        database,
        "create_document_records",
        lambda *_args, **kwargs: saved.update(kwargs["document"]),
    )
    monkeypatch.setattr(
        ingestion,
        "_finish_ingestion",
        lambda *_args: ingestion.IngestionOutcome("id", "notes.pdf", 1),
    )

    ingest_pdf(
        object(), "key", "notes.pdf", "application/pdf", b"data",
        material_type="questions", study_scopes=("mid_sem", "quiz"),
    )

    assert saved["material_type"] == "questions"
    assert saved["study_scopes"] == ["mid_sem", "quiz"]


def test_ingestion_rejects_empty_coverage_before_processing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: pytest.fail("must validate first"))
    with pytest.raises(IngestionError) as error:
        ingest_pdf(
            object(), "key", "notes.pdf", "application/pdf", b"data",
            study_scopes=(),
        )
    assert error.value.code == "INVALID_CLASSIFICATION"


def test_failed_ingestion_records_safe_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    failures: list[str] = []
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: _prepared())
    monkeypatch.setattr(database, "find_document_by_hash", lambda *_args: None)
    monkeypatch.setattr(database, "upload_pdf", lambda *_args: None)
    monkeypatch.setattr(database, "create_document_records", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(ingestion, "embed_chunks", lambda *_args: [[0.1] * 1024])
    monkeypatch.setattr(
        database,
        "insert_chunks",
        lambda *_args: (_ for _ in ()).throw(database.DatabaseError("private detail")),
    )
    monkeypatch.setattr(
        database,
        "mark_version_failed",
        lambda _client, _document, _version, _run, code: failures.append(code),
    )

    with pytest.raises(IngestionError, match="could not be indexed") as error:
        ingest_pdf(object(), "key", "notes.pdf", "application/pdf", b"data")

    assert failures == ["INGESTION_FAILED"]
    assert "private detail" not in str(error.value)


def test_delete_makes_document_unavailable_before_storage_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        database,
        "begin_document_delete",
        lambda *_args: events.append("unavailable") or "private/path.pdf",
    )
    monkeypatch.setattr(database, "remove_pdf", lambda *_args: events.append("storage"))
    monkeypatch.setattr(
        database, "delete_document_record", lambda *_args: events.append("record")
    )

    delete_document(object(), "document")

    assert events == ["unavailable", "storage", "record"]


def test_retry_creates_a_current_provider_version(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def reindex(
        client: object, api_key: str, document_id: str, *, progress: object
    ) -> ingestion.IngestionOutcome:
        captured.update(client=client, api_key=api_key, document_id=document_id, progress=progress)
        return ingestion.IngestionOutcome(document_id, "notes.pdf", 1)

    monkeypatch.setattr(ingestion, "reindex_document", reindex)
    progress = lambda _message: None

    result = retry_failed_document(object(), "key", "document", progress=progress)

    assert result.document_id == "document"
    assert captured["api_key"] == "key"
    assert captured["progress"] is progress


def test_reindex_creates_one_new_version_before_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = object()
    document = {
        "display_name": "notes.pdf",
        "object_path": "private/notes.pdf",
        "content_hash": "a" * 64,
    }
    monkeypatch.setattr(database, "get_document", lambda *_args: document)
    monkeypatch.setattr(database, "download_pdf", lambda *_args: b"stored")
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: _prepared())
    monkeypatch.setattr(database, "next_version_number", lambda *_args: 2)
    records: list[tuple[dict[str, object], dict[str, object]]] = []
    monkeypatch.setattr(
        database,
        "create_version_records",
        lambda _client, *, version, run: records.append((version, run)),
    )
    monkeypatch.setattr(
        ingestion,
        "_finish_ingestion",
        lambda _client, _prepared_doc, _key, document_id, version_id, run_id, _progress: ingestion.IngestionOutcome(
            document_id, "notes.pdf", 1
        ),
    )

    reindex_document(client, "key", "document")

    assert len(records) == 1
    version, run = records[0]
    assert version["version_number"] == 2
    assert version["status"] == "processing"
    assert run["version_id"] == version["id"]
    assert run["status"] == "processing"
