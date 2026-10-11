from types import SimpleNamespace

import pytest

import study_guide.ingestion as ingestion
from study_guide import database
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
        self.pages = [Page("a" * 2_000), Page("short")]


def test_prepares_page_bounded_chunks_and_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ingestion, "PdfReader", Reader)

    prepared = prepare_pdf("folder/notes.PDF", "application/pdf", b"%PDF-example")

    assert prepared.display_name == "notes.PDF"
    assert len(prepared.pages) == 2
    assert prepared.low_text_pages == (2,)
    assert [chunk.page_number for chunk in prepared.chunks] == [1, 1, 2]
    assert [chunk.chunk_order for chunk in prepared.chunks] == [0, 1, 0]
    assert all(len(chunk.content) <= ingestion.CHUNK_CHARS for chunk in prepared.chunks)
    assert prepared.chunks[0].content[-ingestion.CHUNK_OVERLAP :] == prepared.chunks[1].content[: ingestion.CHUNK_OVERLAP]
    assert len(prepared.content_hash) == 64


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
    calls: list[dict[str, object]] = []

    class Models:
        def embed_content(self, **kwargs: object) -> object:
            calls.append(kwargs)
            contents = kwargs["contents"]
            return SimpleNamespace(
                embeddings=[SimpleNamespace(values=[0.1] * 768) for _ in contents]  # type: ignore[arg-type]
            )

    vectors = embed_chunks(
        tuple(_chunk(str(index)) for index in range(33)),
        "key",
        client=SimpleNamespace(models=Models()),
    )

    assert len(calls) == 2
    assert calls[0]["model"] == "gemini-embedding-2"
    assert calls[0]["config"].output_dimensionality == 768  # type: ignore[union-attr]
    assert len(vectors) == 33


def test_retries_one_transient_embedding_failure() -> None:
    attempts = 0

    class Models:
        def embed_content(self, **_kwargs: object) -> object:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise TimeoutError("provider detail")
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.1] * 768)])

    assert len(
        embed_chunks(
            (_chunk(),),
            "key",
            client=SimpleNamespace(models=Models()),
            sleep=lambda _seconds: None,
        )
    ) == 1
    assert attempts == 2


def test_invalid_embedding_dimension_fails_safely() -> None:
    class Models:
        def embed_content(self, **_kwargs: object) -> object:
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[1.0])])

    with pytest.raises(IngestionError, match="invalid response") as error:
        embed_chunks((_chunk(),), "key", client=SimpleNamespace(models=Models()))
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
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: _prepared())
    monkeypatch.setattr(database, "find_document_by_hash", lambda *_args: None)
    monkeypatch.setattr(database, "upload_pdf", lambda *_args: events.append("upload"))
    monkeypatch.setattr(
        database, "create_document_records", lambda *_args, **_kwargs: events.append("records")
    )
    monkeypatch.setattr(ingestion, "embed_chunks", lambda *_args: [[0.1] * 768])
    monkeypatch.setattr(
        database, "insert_chunks", lambda *_args: events.append("chunks")
    )
    monkeypatch.setattr(
        database, "activate_version", lambda *_args: events.append("activate")
    )

    result = ingest_pdf(object(), "key", "notes.pdf", "application/pdf", b"data")

    assert result.chunk_count == 1
    assert events == ["upload", "records", "chunks", "activate"]


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
    monkeypatch.setattr(ingestion, "embed_chunks", lambda *_args: [[0.1] * 768])
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


def test_retry_reuses_failed_version_and_run(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object()
    document = {
        "display_name": "notes.pdf",
        "object_path": "private/notes.pdf",
        "content_hash": "a" * 64,
    }
    monkeypatch.setattr(database, "get_document", lambda *_args: document)
    monkeypatch.setattr(database, "download_pdf", lambda *_args: b"stored")
    monkeypatch.setattr(ingestion, "prepare_pdf", lambda *_args: _prepared())
    monkeypatch.setattr(
        database, "get_failed_attempt", lambda *_args: ("failed-version", "failed-run")
    )
    finished: list[tuple[str, str]] = []
    monkeypatch.setattr(
        ingestion,
        "_finish_ingestion",
        lambda _client, _prepared_doc, _key, _document, version, run, _progress: (
            finished.append((version, run))
            or ingestion.IngestionOutcome("document", "notes.pdf", 1)
        ),
    )

    retry_failed_document(client, "key", "document")

    assert finished == [("failed-version", "failed-run")]


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
