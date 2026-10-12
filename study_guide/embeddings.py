from __future__ import annotations

import json
import math
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


VOYAGE_BASE_URL = "https://api.voyageai.com/v1"
EMBEDDING_MODEL = "voyage-4-lite"
EMBEDDING_DIMENSION = 1024
MAX_EMBEDDING_RESPONSE_BYTES = 4_000_000


class EmbeddingProviderError(RuntimeError):
    """A provider failure whose private detail must not reach the UI."""

    def __init__(self, *, status_code: int | None = None) -> None:
        super().__init__("embedding provider failed")
        self.status_code = status_code


class InvalidEmbeddingResponse(EmbeddingProviderError):
    """The provider returned a response outside the embedding contract."""


def embed_texts(
    texts: list[str],
    api_key: str,
    *,
    input_type: str,
    opener: Any = None,
) -> list[list[float]]:
    if not api_key or not texts or input_type not in {"document", "query"}:
        raise ValueError("invalid embedding request")
    request = Request(
        f"{VOYAGE_BASE_URL}/embeddings",
        data=json.dumps(
            {
                "input": texts,
                "model": EMBEDDING_MODEL,
                "input_type": input_type,
                "output_dimension": EMBEDDING_DIMENSION,
                "output_dtype": "float",
                "truncation": False,
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with (opener or urlopen)(request, timeout=30) as response:
            raw = response.read(MAX_EMBEDDING_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise EmbeddingProviderError(status_code=exc.code) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise EmbeddingProviderError() from exc

    try:
        if len(raw) > MAX_EMBEDDING_RESPONSE_BYTES:
            raise ValueError("response too large")
        payload = json.loads(raw)
        rows = payload["data"]
        if not isinstance(rows, list) or len(rows) != len(texts):
            raise ValueError("wrong embedding count")
        by_index = {row["index"]: row["embedding"] for row in rows}
        if set(by_index) != set(range(len(texts))):
            raise ValueError("invalid embedding indexes")
        vectors: list[list[float]] = []
        for index in range(len(texts)):
            values = by_index[index]
            if (
                not isinstance(values, list)
                or len(values) != EMBEDDING_DIMENSION
                or not all(
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and math.isfinite(value)
                    for value in values
                )
                or not any(value != 0 for value in values)
            ):
                raise ValueError("invalid embedding")
            vectors.append([float(value) for value in values])
        return vectors
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidEmbeddingResponse() from exc
