import json

import pytest

from study_guide.answering import (
    AI_STAR_BASE_URL,
    AI_STAR_FALLBACK_MODEL,
    AI_STAR_FINAL_FALLBACK_MODEL,
    AI_STAR_MODEL,
    AnsweringError,
    INSUFFICIENT_MATERIAL,
    MAX_QUESTION_CHARS,
    answer_question,
    _call_ai_star,
    embed_question,
    retrieve_evidence,
    validate_generated_answer,
    validate_question,
)
from study_guide.answering import MAX_GENERATIONS_IN_FLIGHT, _generation_slots


def test_question_is_trimmed_and_bounded() -> None:
    assert validate_question("  What is a basis? ") == "What is a basis?"
    with pytest.raises(AnsweringError):
        validate_question("x" * (MAX_QUESTION_CHARS + 1))


def test_query_embedding_uses_voyage_query_mode_and_dimension() -> None:
    def embedder(texts: list[str], api_key: str, *, input_type: str) -> list[list[float]]:
        assert texts == ["What is a basis?"]
        assert api_key == "v" * 32
        assert input_type == "query"
        return [[0.1] * 1024]

    vector = embed_question("What is a basis?", "v" * 32, embedder=embedder)
    assert len(vector) == 1024


def test_query_embedding_rejects_invalid_dimension_without_provider_detail() -> None:
    with pytest.raises(AnsweringError, match="temporarily unavailable"):
        embed_question(
            "Question", "v" * 32,
            embedder=lambda *_args, **_kwargs: [[1.0]],
        )


def test_query_embedding_rejects_zero_vector() -> None:
    with pytest.raises(AnsweringError, match="temporarily unavailable"):
        embed_question(
            "Question", "v" * 32,
            embedder=lambda *_args, **_kwargs: [[0.0] * 1024],
        )


def test_retrieval_uses_bounded_active_chunk_search() -> None:
    class Rpc:
        def execute(self) -> object:
            return type("Result", (), {"data": [{"chunk_id": "c1"}]})()

    class Client:
        def rpc(self, name: str, args: dict[str, object]) -> Rpc:
            assert name == "match_chunks_voyage"
            assert len(args["query_embedding"]) == 1024  # type: ignore[arg-type]
            assert args["match_count"] == 8
            assert args["min_similarity"] == 0.46
            return Rpc()

    assert retrieve_evidence(Client(), [0.1] * 1024) == [{"chunk_id": "c1"}]


def test_retrieval_uses_study_scope_when_selected() -> None:
    class Rpc:
        def execute(self) -> object:
            return type("Result", (), {"data": []})()

    class Client:
        def rpc(self, name: str, args: dict[str, object]) -> Rpc:
            assert name == "match_chunks_voyage_by_scope"
            assert args["study_scope"] == "mid_sem"
            return Rpc()

    assert retrieve_evidence(Client(), [0.1] * 1024, "mid_sem") == []


def test_answer_citations_are_mapped_only_from_retrieved_metadata() -> None:
    rows = [
        {
            "document_id": "doc-1",
            "version_id": "version-1",
            "chunk_id": "chunk-1",
            "display_name": "Linear Algebra.pdf",
            "page_number": 25,
            "content": "basis definition",
        }
    ]
    result = validate_generated_answer(
        json.dumps({"answer": "A basis is ...", "cited_chunk_ids": ["chunk-1"]}),
        rows,
    )
    assert result.citations == (
        {
            "document_id": "doc-1",
            "version_id": "version-1",
            "chunk_id": "chunk-1",
            "display_name": "Linear Algebra.pdf",
            "page_number": 25,
        },
    )


def test_answer_rejects_fabricated_citation_or_missing_citations() -> None:
    rows = [{"chunk_id": "real", "document_id": "d", "version_id": "v", "display_name": "n.pdf", "page_number": 1}]
    with pytest.raises(AnsweringError):
        validate_generated_answer('{"answer":"x","cited_chunk_ids":["fake"]}', rows)
    with pytest.raises(AnsweringError):
        validate_generated_answer('{"answer":"x","cited_chunk_ids":[]}', rows)


def test_ai_star_request_uses_selected_model_and_json_contract() -> None:
    captured: dict[str, object] = {}

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return b'{"choices":[{"finish_reason":"stop","message":{"content":"{}"}}]}'

    def opener(request: object, *, timeout: int) -> Response:
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        captured["auth"] = request.get_header("Authorization")  # type: ignore[attr-defined]
        captured["body"] = json.loads(request.data)  # type: ignore[attr-defined]
        captured["timeout"] = timeout
        return Response()

    assert _call_ai_star("secret-value-not-logged", [{"role": "user", "content": "test"}], opener=opener) == "{}"
    assert captured["url"] == f"{AI_STAR_BASE_URL}/chat/completions"
    assert captured["auth"] == "Bearer secret-value-not-logged"
    assert captured["timeout"] == 30
    assert captured["body"]["model"] == AI_STAR_MODEL  # type: ignore[index]
    assert captured["body"]["response_format"] == {"type": "json_object"}  # type: ignore[index]


def test_ai_star_provider_errors_are_redacted() -> None:
    from urllib.error import URLError

    def opener(*_args: object, **_kwargs: object) -> object:
        raise URLError("sensitive-provider-detail")

    with pytest.raises(AnsweringError, match="temporarily unavailable") as error:
        _call_ai_star("a" * 32, [], opener=opener)
    assert "sensitive-provider-detail" not in str(error.value)


def test_ai_star_uses_fallback_once_after_transient_failure() -> None:
    models: list[str] = []

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return b'{"choices":[{"finish_reason":"stop","message":{"content":"{}"}}]}'

    def opener(request: object, *, timeout: int) -> Response:
        models.append(json.loads(request.data)["model"])  # type: ignore[attr-defined]
        if len(models) == 1:
            raise TimeoutError("primary busy")
        return Response()

    assert _call_ai_star("a" * 32, [], opener=opener) == "{}"
    assert models == [AI_STAR_MODEL, AI_STAR_FALLBACK_MODEL]


def test_answer_generation_reaches_composer_after_two_transient_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from io import BytesIO
    from urllib.error import HTTPError
    import study_guide.answering as answering

    monkeypatch.setattr(answering, "embed_question", lambda *_args: [0.1] * 1024)
    evidence = [{
        "document_id": "d", "version_id": "v", "chunk_id": "c",
        "display_name": "notes.pdf", "page_number": 3,
        "content": "A basis is linearly independent and spans the space.",
    }]
    monkeypatch.setattr(answering, "retrieve_evidence", lambda *_args: evidence)
    models: list[str] = []

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return json.dumps({
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps({
                    "answer": "A basis is independent and spanning.",
                    "cited_chunk_ids": ["c"],
                })}}]
            }).encode()

    def opener(request: object, *, timeout: int) -> Response:
        model = json.loads(request.data)["model"]  # type: ignore[attr-defined]
        models.append(model)
        if len(models) == 1:
            raise HTTPError(request.full_url, 503, "provider busy", {}, BytesIO())  # type: ignore[attr-defined]
        if len(models) == 2:
            raise TimeoutError("fallback busy")
        return Response()

    result = answer_question(
        "What is a basis?",
        voyage_api_key="v" * 32,
        ai_star_api_key="a" * 32,
        database_client=object(),
        user_key="composer-fallback-test-user",
        opener=opener,
    )

    assert result.text == "A basis is independent and spanning."
    assert result.citations[0]["page_number"] == 3
    assert models == [AI_STAR_MODEL, AI_STAR_FALLBACK_MODEL, AI_STAR_FINAL_FALLBACK_MODEL]


@pytest.mark.parametrize("status", [429, 503])
def test_ai_star_uses_fallback_after_retryable_http_error(status: int) -> None:
    from io import BytesIO
    from urllib.error import HTTPError

    models: list[str] = []

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return b'{"choices":[{"finish_reason":"stop","message":{"content":"{}"}}]}'

    def opener(request: object, *, timeout: int) -> Response:
        models.append(json.loads(request.data)["model"])  # type: ignore[attr-defined]
        if len(models) == 1:
            raise HTTPError(request.full_url, status, "provider busy", {}, BytesIO())  # type: ignore[attr-defined]
        return Response()

    assert _call_ai_star("a" * 32, [], opener=opener) == "{}"
    assert models == [AI_STAR_MODEL, AI_STAR_FALLBACK_MODEL]


def test_ai_star_does_not_fallback_after_non_retryable_http_error() -> None:
    from io import BytesIO
    from urllib.error import HTTPError

    calls = 0

    def opener(request: object, *, timeout: int) -> object:
        nonlocal calls
        calls += 1
        raise HTTPError(request.full_url, 401, "secret provider detail", {}, BytesIO())  # type: ignore[attr-defined]

    with pytest.raises(AnsweringError, match="temporarily unavailable") as error:
        _call_ai_star("a" * 32, [], opener=opener)
    assert calls == 1
    assert "secret provider detail" not in str(error.value)


def test_ai_star_tries_all_models_after_invalid_responses() -> None:
    calls = 0

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return b"not json"

    def opener(*_args: object, **_kwargs: object) -> Response:
        nonlocal calls
        calls += 1
        return Response()

    with pytest.raises(AnsweringError, match="temporarily unavailable"):
        _call_ai_star("a" * 32, [], opener=opener)
    assert calls == 3


def test_ai_star_falls_back_after_truncated_response() -> None:
    models: list[str] = []

    class Response:
        def __init__(self, finish_reason: str) -> None:
            self.finish_reason = finish_reason

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return json.dumps({
                "choices": [{"finish_reason": self.finish_reason, "message": {"content": "{}"}}]
            }).encode()

    def opener(request: object, *, timeout: int) -> Response:
        models.append(json.loads(request.data)["model"])  # type: ignore[attr-defined]
        return Response("length" if len(models) == 1 else "stop")

    assert _call_ai_star("a" * 32, [], opener=opener) == "{}"
    assert models == [AI_STAR_MODEL, AI_STAR_FALLBACK_MODEL]


def test_answer_question_repairs_invalid_output_once(monkeypatch: pytest.MonkeyPatch) -> None:
    import study_guide.answering as answering

    monkeypatch.setattr(answering, "embed_question", lambda *_args: [0.1] * 1024)
    evidence = [
        {
            "document_id": "d",
            "version_id": "v",
            "chunk_id": "c",
            "display_name": "notes.pdf",
            "page_number": 3,
            "content": "A basis is linearly independent and spans the space.",
        }
    ]
    monkeypatch.setattr(answering, "retrieve_evidence", lambda *_args: evidence)
    outputs = iter([
        "not json",
        '{"answer":"A basis is independent and spanning.","cited_chunk_ids":["c"]}',
    ])
    requests: list[dict[str, object]] = []

    class Response:
        def __init__(self, content: str) -> None:
            self.content = content

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": self.content}}]}).encode()

    def opener(request: object, *, timeout: int) -> Response:
        requests.append(json.loads(request.data)["messages"])  # type: ignore[attr-defined]
        return Response(next(outputs))

    result = answer_question(
        "What is a basis?",
        voyage_api_key="v" * 32,
        ai_star_api_key="a" * 32,
        database_client=object(),
        user_key="repair-test-user",
        history=[{"role": "user", "content": "Why is that?"}],
        opener=opener,
    )

    assert result.text == "A basis is independent and spanning."
    assert result.citations[0]["page_number"] == 3
    assert len(requests) == 2
    system_prompt = requests[0][0]["content"]  # type: ignore[index]
    assert "untrusted quoted data" in system_prompt
    assert "Streamlit-compatible Markdown" in system_prompt
    assert "lead with the direct answer" in system_prompt
    assert "display mathematics in $$ on separate lines" in system_prompt
    assert "under 400 words and use simple English" in system_prompt
    assert "Do not include citations, references or a sources section" in system_prompt
    request_data = json.loads(requests[0][1]["content"])  # type: ignore[index]
    assert request_data["recent_conversation"] == [{"role": "user", "content": "Why is that?"}]


def test_answer_validation_accepts_only_the_fixed_empty_citation_refusal() -> None:
    assert validate_generated_answer(
        json.dumps({"answer": INSUFFICIENT_MATERIAL, "cited_chunk_ids": []}),
        [{"chunk_id": "c"}],
    ).citations == ()


def test_answer_question_refuses_without_generation_when_evidence_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import study_guide.answering as answering

    monkeypatch.setattr(answering, "embed_question", lambda *_args: [0.1] * 1024)
    monkeypatch.setattr(answering, "retrieve_evidence", lambda *_args: [])
    result = answer_question(
        "Question outside course material",
        voyage_api_key="v" * 32,
        ai_star_api_key="a" * 32,
        database_client=object(),
        user_key="empty-evidence-user",
        opener=lambda *_args, **_kwargs: pytest.fail("generation must not run"),
    )
    assert result.text == INSUFFICIENT_MATERIAL
    assert result.citations == ()


def test_answer_question_rate_limits_by_user(monkeypatch: pytest.MonkeyPatch) -> None:
    import study_guide.answering as answering

    monkeypatch.setattr(answering, "embed_question", lambda *_args: [0.1] * 1024)
    monkeypatch.setattr(answering, "retrieve_evidence", lambda *_args: [])
    for _ in range(5):
        answer_question(
            "Question",
            voyage_api_key="v" * 32,
            ai_star_api_key="a" * 32,
            database_client=object(),
            user_key="rate-limit-test-user",
        )
    with pytest.raises(AnsweringError, match="wait a minute"):
        answer_question(
            "Question",
            voyage_api_key="v" * 32,
            ai_star_api_key="a" * 32,
            database_client=object(),
            user_key="rate-limit-test-user",
        )


def test_answer_question_rejects_when_generation_is_at_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import study_guide.answering as answering

    monkeypatch.setattr(answering, "embed_question", lambda *_args: [0.1] * 1024)
    monkeypatch.setattr(
        answering,
        "retrieve_evidence",
        lambda *_args: [{"content": "course text", "chunk_id": "c"}],
    )
    acquired = [_generation_slots.acquire(blocking=False) for _ in range(MAX_GENERATIONS_IN_FLIGHT)]
    assert all(acquired)
    try:
        with pytest.raises(AnsweringError, match="busy"):
            answer_question(
                "Question",
                voyage_api_key="v" * 32,
                ai_star_api_key="a" * 32,
                database_client=object(),
                user_key="busy-test-user",
                opener=lambda *_args, **_kwargs: pytest.fail("generation must not run"),
            )
    finally:
        for _ in acquired:
            _generation_slots.release()
