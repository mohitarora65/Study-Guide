import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from study_guide.embeddings import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    MAX_EMBEDDING_RESPONSE_BYTES,
    VOYAGE_BASE_URL,
    EmbeddingProviderError,
    InvalidEmbeddingResponse,
    embed_texts,
)


class Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self.body


def test_voyage_request_uses_bounded_native_embedding_contract() -> None:
    captured: dict[str, object] = {}
    body = json.dumps(
        {
            "data": [
                {"index": 1, "embedding": [0.2] * EMBEDDING_DIMENSION},
                {"index": 0, "embedding": [0.1] * EMBEDDING_DIMENSION},
            ]
        }
    ).encode()

    def opener(request: object, *, timeout: int) -> Response:
        captured["url"] = request.full_url  # type: ignore[attr-defined]
        captured["auth"] = request.get_header("Authorization")  # type: ignore[attr-defined]
        captured["payload"] = json.loads(request.data)  # type: ignore[attr-defined]
        captured["timeout"] = timeout
        return Response(body)

    vectors = embed_texts(
        ["first", "second"], "secret-not-logged", input_type="document", opener=opener
    )

    assert captured["url"] == f"{VOYAGE_BASE_URL}/embeddings"
    assert captured["auth"] == "Bearer secret-not-logged"
    assert captured["timeout"] == 30
    assert captured["payload"] == {
        "input": ["first", "second"],
        "model": EMBEDDING_MODEL,
        "input_type": "document",
        "output_dimension": EMBEDDING_DIMENSION,
        "output_dtype": "float",
        "truncation": False,
    }
    assert vectors[0][0] == 0.1
    assert vectors[1][0] == 0.2


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        json.dumps({"data": []}).encode(),
        json.dumps({"data": [{"index": 0, "embedding": [1.0]}]}).encode(),
        json.dumps({"data": [{"index": 0, "embedding": [0.0] * EMBEDDING_DIMENSION}]}).encode(),
        json.dumps({"data": [{"index": 0, "embedding": [float("nan")] * EMBEDDING_DIMENSION}]}).encode(),
    ],
)
def test_voyage_rejects_invalid_responses(body: bytes) -> None:
    with pytest.raises(InvalidEmbeddingResponse):
        embed_texts(
            ["text"], "v" * 32, input_type="query", opener=lambda *_args, **_kwargs: Response(body)
        )


def test_voyage_rejects_oversized_response() -> None:
    with pytest.raises(InvalidEmbeddingResponse):
        embed_texts(
            ["text"],
            "v" * 32,
            input_type="query",
            opener=lambda *_args, **_kwargs: Response(b"x" * (MAX_EMBEDDING_RESPONSE_BYTES + 1)),
        )


def test_voyage_preserves_http_status_but_redacts_provider_detail() -> None:
    def opener(request: object, *, timeout: int) -> object:
        raise HTTPError(request.full_url, 429, "private detail", {}, BytesIO())  # type: ignore[attr-defined]

    with pytest.raises(EmbeddingProviderError) as error:
        embed_texts(["text"], "v" * 32, input_type="query", opener=opener)

    assert error.value.status_code == 429
    assert "private detail" not in str(error.value)


@pytest.mark.parametrize(
    ("texts", "input_type"),
    [([], "query"), (["text"], "invalid")],
)
def test_voyage_rejects_invalid_local_request(texts: list[str], input_type: str) -> None:
    with pytest.raises(ValueError):
        embed_texts(texts, "v" * 32, input_type=input_type)
